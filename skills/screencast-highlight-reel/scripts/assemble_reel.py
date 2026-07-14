#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Assemble a highlight reel from a source screencast using ffmpeg.

Given a reel-plan.json (an edit-decision list produced by the skill after the
interview + TTS step), this script:

  1. Cuts each selected [in, out] segment from the source video.
  2. Normalizes every segment to a uniform resolution / fps / SAR / pixfmt so
     they concatenate cleanly.
  3. Builds each segment's audio: a silent bed + (optional) the original audio
     (kept, muted, or ducked) + (optional) the synthesized voiceover, mixed.
  4. Extends a clip by freezing its last frame when its narration is longer than
     the clip, so no narration is cut off.
  5. Concatenates all segments.
  6. Generates an SRT from the narration timings and (optionally) burns it in.

It shells out to ffmpeg / ffprobe only — no Python dependencies. Requires ffmpeg
built with libx264, aac, and libass (subtitles). Run a self-check with --check.

Plan schema (see references/narration-and-render.md for the full contract):

{
  "source": "/abs/path/demo.mp4",
  "output": "highlight-reel.mp4",
  "resolution": "1920x1080",        // optional; default = source resolution
  "fps": 30,                          // optional; default = source fps (fallback 30)
  "original_audio": "duck",          // "keep" | "mute" | "duck"  (default "duck")
  "duck_db": -18,                     // how far to lower original under voiceover
  "voiceover_gain_db": 0,
  "tail_pad_seconds": 0.4,            // silence held after narration ends
  "subtitles": true,
  "segments": [
    {"id":"seg1","in":12.5,"out":27.0,
     "narration":"Here the dashboard loads...",
     "voiceover":"voiceover/seg1.mp3",   // optional (from tts.py)
     "voiceover_seconds":9.2,            // optional; probed if missing
     "title":"Dashboard overview"}       // optional (unused in burn; reserved)
  ]
}
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile


def run(cmd, **kw):
    return subprocess.run(cmd, check=True, capture_output=True, text=True, **kw)


def ffprobe_json(path, streams="v:0", entries="width,height,r_frame_rate"):
    out = run([
        "ffprobe", "-v", "error", "-select_streams", streams,
        "-show_entries", f"stream={entries}", "-of", "json", path,
    ])
    return json.loads(out.stdout)


def probe_duration(path):
    out = run([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", path,
    ])
    try:
        return float(out.stdout.strip())
    except ValueError:
        return 0.0


def has_audio(path):
    try:
        info = ffprobe_json(path, streams="a", entries="index")
        return bool(info.get("streams"))
    except subprocess.CalledProcessError:
        return False


def parse_fps(rate_str, fallback=30.0):
    try:
        num, den = rate_str.split("/")
        den = float(den)
        return float(num) / den if den else fallback
    except (ValueError, AttributeError):
        return fallback


def srt_ts(seconds):
    if seconds < 0:
        seconds = 0
    ms = int(round(seconds * 1000))
    h, ms = divmod(ms, 3600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def wrap(text, width=42):
    """Word-wrap a caption to ~`width` chars per line. Never drops words — keep
    narration beats short (the skill enforces this) so captions stay ~1-2 lines."""
    words, lines, cur = text.split(), [], ""
    for w in words:
        if cur and len(cur) + len(w) + 1 > width:
            lines.append(cur)
            cur = w
        else:
            cur = f"{cur} {w}".strip()
    if cur:
        lines.append(cur)
    return "\n".join(lines)


def build_segment(seg, idx, src, W, H, fps, src_has_audio, audio_mode,
                  duck_db, vo_gain_db, tail_pad, tmpdir):
    """Render one normalized segment to a temp mp4. Returns (path, target_len, speak_len)."""
    t_in = float(seg["in"])
    t_out = float(seg["out"])
    clip_len = max(0.05, t_out - t_in)

    vo = seg.get("voiceover")
    vo_len = 0.0
    if vo:
        vo = os.path.abspath(vo)
        if not os.path.exists(vo):
            print(f"  ! seg {idx}: voiceover not found: {vo} (ignoring)", file=sys.stderr)
            vo = None
        else:
            vo_len = seg.get("voiceover_seconds") or probe_duration(vo)

    speak_len = vo_len if vo else clip_len
    target_len = max(clip_len, (vo_len + tail_pad) if vo else clip_len)
    ext = round(target_len - clip_len, 3)

    inputs = ["-i", src]
    if vo:
        inputs += ["-i", vo]
    # Silent bed sized to target_len guarantees an audio stream + fixes duration.
    inputs += ["-f", "lavfi", "-t", f"{target_len:.3f}", "-i",
               "anullsrc=channel_layout=stereo:sample_rate=48000"]

    # --- video chain ---
    vchain = (
        f"[0:v]scale={W}:{H}:force_original_aspect_ratio=decrease,"
        f"pad={W}:{H}:(ow-iw)/2:(oh-ih)/2,setsar=1,fps={fps},format=yuv420p"
    )
    if ext > 0.01:
        vchain += f",tpad=stop_mode=clone:stop_duration={ext:.3f}"
    vchain += "[vout]"

    # --- audio chain ---
    bed_idx = 2 if vo else 1
    parts = []

    real = []
    if src_has_audio and audio_mode != "mute":
        gain = duck_db if (audio_mode == "duck" and vo) else 0
        parts.append(f"[0:a]aformat=sample_rates=48000:channel_layouts=stereo,volume={gain}dB[oa]")
        real.append("[oa]")
    if vo:
        parts.append(f"[1:a]aformat=sample_rates=48000:channel_layouts=stereo,volume={vo_gain_db}dB[va]")
        real.append("[va]")

    bed = f"[{bed_idx}:a]"
    amix_inputs = [bed] + real
    n = len(amix_inputs)
    parts.append(
        "".join(amix_inputs)
        + f"amix=inputs={n}:duration=first:normalize=0,"
        + f"apad,atrim=0:{target_len:.3f},asetpts=N/SR/TB[aout]"
    )

    filtergraph = ";".join([vchain] + parts)
    out_path = os.path.join(tmpdir, f"seg_{idx:03d}.mp4")

    cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error"]
    # accurate output-seek for the source window
    cmd += ["-ss", f"{t_in:.3f}", "-t", f"{clip_len:.3f}"]
    cmd += inputs
    cmd += [
        "-filter_complex", filtergraph,
        "-map", "[vout]", "-map", "[aout]",
        "-r", str(fps),
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2",
        "-video_track_timescale", "90000",
        out_path,
    ]
    run(cmd)
    return out_path, target_len, min(speak_len, target_len)


def main():
    ap = argparse.ArgumentParser(description="Assemble a highlight reel from a reel-plan.json")
    ap.add_argument("plan", nargs="?", help="Path to reel-plan.json")
    ap.add_argument("--srt-only", action="store_true", help="Only (re)generate the SRT, do not render")
    ap.add_argument("--check", action="store_true", help="Verify ffmpeg/ffprobe + required filters, then exit")
    args = ap.parse_args()

    for tool in ("ffmpeg", "ffprobe"):
        if not shutil.which(tool):
            print(f"Error: {tool} not found on PATH.", file=sys.stderr)
            sys.exit(1)

    if args.check:
        filt = run(["ffmpeg", "-hide_banner", "-filters"]).stdout
        need = ["tpad", "subtitles", "amix", "concat", "anull", "apad"]
        missing = [f for f in need if f not in filt]
        if missing:
            print(f"Missing ffmpeg filters: {', '.join(missing)}", file=sys.stderr)
            sys.exit(1)
        print("OK: ffmpeg, ffprobe, and required filters (tpad, subtitles, amix, concat) present.")
        return

    if not args.plan:
        ap.error("plan path is required (unless --check)")

    with open(args.plan) as f:
        plan = json.load(f)

    src = os.path.abspath(os.path.expanduser(plan["source"]))
    if not os.path.exists(src):
        print(f"Error: source not found: {src}", file=sys.stderr)
        sys.exit(1)

    segments = plan.get("segments", [])
    if not segments:
        print("Error: plan has no segments[].", file=sys.stderr)
        sys.exit(1)

    output = os.path.abspath(plan.get("output", "highlight-reel.mp4"))
    srt_path = os.path.splitext(output)[0] + ".srt"

    # Resolution / fps defaults from source.
    vinfo = ffprobe_json(src)["streams"][0]
    if plan.get("resolution"):
        W, H = (int(x) for x in str(plan["resolution"]).lower().split("x"))
    else:
        W, H = int(vinfo["width"]), int(vinfo["height"])
    W += W % 2  # libx264 needs even dims
    H += H % 2
    fps = int(round(float(plan.get("fps") or parse_fps(vinfo.get("r_frame_rate", "30/1")))))

    audio_mode = plan.get("original_audio", "duck")
    duck_db = float(plan.get("duck_db", -18))
    vo_gain = float(plan.get("voiceover_gain_db", 0))
    tail_pad = float(plan.get("tail_pad_seconds", 0.4))
    want_subs = bool(plan.get("subtitles", True))
    src_audio = has_audio(src)

    # ---- Build SRT (always; needed for burn and useful as a sidecar) ----
    cues, offset = [], 0.0
    tmpdir = tempfile.mkdtemp(prefix="reel_")
    seg_files = []
    try:
        for i, seg in enumerate(segments, 1):
            if args.srt_only:
                # Estimate durations without rendering.
                clip_len = max(0.05, float(seg["out"]) - float(seg["in"]))
                vo = seg.get("voiceover")
                vo_len = (seg.get("voiceover_seconds") or (probe_duration(os.path.abspath(vo)) if vo and os.path.exists(vo) else 0.0))
                target_len = max(clip_len, (vo_len + tail_pad) if vo else clip_len)
                speak_len = min(vo_len if vo else clip_len, target_len)
            else:
                print(f"Rendering segment {i}/{len(segments)} "
                      f"[{seg['in']}-{seg['out']}]...", file=sys.stderr)
                path, target_len, speak_len = build_segment(
                    seg, i, src, W, H, fps, src_audio, audio_mode,
                    duck_db, vo_gain, tail_pad, tmpdir)
                seg_files.append(path)

            narration = (seg.get("narration") or "").strip()
            if narration:
                cues.append((offset, offset + max(1.0, speak_len), narration))
            offset += target_len

        with open(srt_path, "w") as f:
            for n, (start, end, text) in enumerate(cues, 1):
                f.write(f"{n}\n{srt_ts(start)} --> {srt_ts(end)}\n{wrap(text)}\n\n")
        print(f"SRT written: {srt_path}", file=sys.stderr)

        if args.srt_only:
            print(srt_path)
            return

        # ---- Concatenate segments ----
        concat_list = os.path.join(tmpdir, "concat.txt")
        with open(concat_list, "w") as f:
            for p in seg_files:
                f.write(f"file '{p}'\n")
        joined = os.path.join(tmpdir, "joined.mp4")
        run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
             "-f", "concat", "-safe", "0", "-i", concat_list,
             "-c", "copy", joined])

        # ---- Burn subtitles (or just move) ----
        if want_subs and cues:
            # Escape the path for the subtitles filter.
            esc = srt_path.replace("\\", "\\\\").replace(":", "\\:").replace("'", "\\'")
            style = ("FontName=Arial,Fontsize=22,PrimaryColour=&H00FFFFFF,"
                     "OutlineColour=&H80000000,BorderStyle=1,Outline=2,Shadow=0,"
                     "Alignment=2,MarginV=40")
            run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
                 "-i", joined,
                 "-vf", f"subtitles='{esc}':force_style='{style}'",
                 "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
                 "-pix_fmt", "yuv420p", "-c:a", "copy", output])
        else:
            shutil.move(joined, output)

        dur = probe_duration(output)
        print(f"\nHighlight reel: {output}  ({dur:.1f}s, {len(seg_files)} segments, {len(cues)} captions)")
        print(f"Subtitles:      {srt_path}")
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


if __name__ == "__main__":
    main()
