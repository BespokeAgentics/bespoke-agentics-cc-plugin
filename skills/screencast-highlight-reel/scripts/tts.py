#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "elevenlabs",
#     "python-dotenv",
# ]
# ///
"""ElevenLabs Text-to-Speech narration synthesizer.

Companion to elevenlabs-transcribe/transcribe.py (STT). This is the TTS half:
it turns the narration script for a highlight reel into voiceover audio.

Reads ELEVENLABS_API_KEY (and optional ELEVENLABS_VOICE_ID / ELEVENLABS_MODEL_ID)
from the .env in the current working directory.

Two modes:

  1. Single line -> single file
     uv run tts.py --text "Here we open the dashboard." --out voiceover/seg1.mp3

  2. Reel plan -> one file per narrated segment (+ an updated plan with paths + durations)
     uv run tts.py --plan reel-plan.json --out-dir voiceover/ --update-plan reel-plan.voiced.json

In plan mode each `segments[i]` that has a non-empty `narration` is synthesized to
`{out-dir}/{id}.mp3`; the written path and measured audio duration (via ffprobe when
available) are added back to that segment as `voiceover` and `voiceover_seconds`.
"""

import argparse
import json
import os
import shutil
import subprocess
import sys

from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs

# Sensible defaults; override via flags or .env.
DEFAULT_VOICE_ID = "21m00Tcm4TlvDq8ikWAM"      # ElevenLabs "Rachel" (a stock voice)
DEFAULT_MODEL_ID = "eleven_multilingual_v2"
DEFAULT_OUTPUT_FORMAT = "mp3_44100_128"


def load_api_key() -> str:
    env_path = os.path.join(os.getcwd(), ".env")
    load_dotenv(env_path) if os.path.exists(env_path) else load_dotenv()
    api_key = os.getenv("ELEVENLABS_API_KEY")
    if not api_key:
        print("Error: ELEVENLABS_API_KEY not found in .env file.", file=sys.stderr)
        print("Add ELEVENLABS_API_KEY=your-key-here to your .env file.", file=sys.stderr)
        sys.exit(1)
    return api_key


def synthesize(client: ElevenLabs, text: str, out_path: str, voice_id: str,
               model_id: str, output_format: str) -> None:
    os.makedirs(os.path.dirname(os.path.abspath(out_path)) or ".", exist_ok=True)
    # The SDK returns an iterator of audio byte chunks.
    audio = client.text_to_speech.convert(
        voice_id=voice_id,
        model_id=model_id,
        text=text,
        output_format=output_format,
    )
    with open(out_path, "wb") as f:
        for chunk in audio:
            if chunk:
                f.write(chunk)


def probe_duration(path: str):
    """Return audio duration in seconds via ffprobe, or None if unavailable."""
    if not shutil.which("ffprobe"):
        return None
    try:
        out = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", path],
            capture_output=True, text=True, check=True,
        )
        return round(float(out.stdout.strip()), 3)
    except (subprocess.CalledProcessError, ValueError):
        return None


def main():
    p = argparse.ArgumentParser(description="Synthesize narration voiceover with ElevenLabs TTS")
    p.add_argument("--text", help="Single line of narration to synthesize")
    p.add_argument("--plan", help="reel-plan.json with a segments[] array (batch mode)")
    p.add_argument("--out", help="Output file path (single-text mode)")
    p.add_argument("--out-dir", default="voiceover", help="Output dir for per-segment files (plan mode)")
    p.add_argument("--update-plan", help="Write the plan back with voiceover paths + durations (plan mode)")
    p.add_argument("--voice", default=os.getenv("ELEVENLABS_VOICE_ID", DEFAULT_VOICE_ID),
                   help="ElevenLabs voice_id (default: env ELEVENLABS_VOICE_ID or Rachel)")
    p.add_argument("--model", default=os.getenv("ELEVENLABS_MODEL_ID", DEFAULT_MODEL_ID),
                   help="ElevenLabs model_id")
    p.add_argument("--format", default=DEFAULT_OUTPUT_FORMAT, help="Output format (e.g. mp3_44100_128)")
    args = p.parse_args()

    if not args.text and not args.plan:
        print("Error: provide either --text or --plan.", file=sys.stderr)
        sys.exit(2)

    api_key = load_api_key()
    client = ElevenLabs(api_key=api_key)
    print(f"TTS | voice={args.voice} model={args.model} format={args.format}", file=sys.stderr)

    # -- Single-text mode --
    if args.text:
        out = args.out or "narration.mp3"
        synthesize(client, args.text, out, args.voice, args.model, args.format)
        dur = probe_duration(out)
        print(f"Wrote {out}" + (f" ({dur}s)" if dur else ""), file=sys.stderr)
        return

    # -- Plan mode --
    with open(args.plan) as f:
        plan = json.load(f)
    segments = plan.get("segments", [])
    if not segments:
        print("Error: plan has no segments[].", file=sys.stderr)
        sys.exit(1)

    os.makedirs(args.out_dir, exist_ok=True)
    n_voiced = 0
    for seg in segments:
        narration = (seg.get("narration") or "").strip()
        seg_id = seg.get("id") or f"seg{segments.index(seg) + 1}"
        if not narration:
            print(f"  {seg_id}: no narration, skipped", file=sys.stderr)
            continue
        out_path = os.path.join(args.out_dir, f"{seg_id}.mp3")
        synthesize(client, narration, out_path, args.voice, args.model, args.format)
        dur = probe_duration(out_path)
        seg["voiceover"] = out_path
        if dur is not None:
            seg["voiceover_seconds"] = dur
        n_voiced += 1
        print(f"  {seg_id}: {out_path}" + (f" ({dur}s)" if dur else ""), file=sys.stderr)

    print(f"Synthesized {n_voiced}/{len(segments)} segment narrations.", file=sys.stderr)

    if args.update_plan:
        with open(args.update_plan, "w") as f:
            json.dump(plan, f, indent=2)
        print(f"Updated plan written to {args.update_plan}", file=sys.stderr)
    else:
        # Echo the enriched plan to stdout so the orchestrator can capture it.
        print(json.dumps(plan, indent=2))


if __name__ == "__main__":
    main()
