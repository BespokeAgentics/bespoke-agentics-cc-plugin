#!/usr/bin/env bash
# gif_to_mp4.sh <input.gif> <output.mp4> [fps]
#
# Convert a GIF (as exported by the Claude-in-Chrome gif_creator tool) into a broadly compatible,
# time-seekable MP4 that PRESERVES the GIF's playback duration.
#
# Why this matters: the screencast-highlight-reel renderer cuts moments with `ffmpeg -ss <t> -t <len>`,
# and a GIF reports no container duration, so downstream frame extraction falls back to frame-index
# timestamps that drift from real seconds. A constant-frame-rate (CFR), yuv420p, even-dimension
# H.264 MP4 gives accurate time-seeking. ffmpeg honors the GIF's per-frame delays on input, so the
# `fps` filter resamples to CFR WITHOUT changing the total duration.
#
# On success, prints the output MP4's real duration (seconds) to stdout — nothing else — so a caller
# can compute a sane reel interval (e.g. INTERVAL = max(2, round(duration / 6))).
set -euo pipefail

usage() {
  echo "usage: gif_to_mp4.sh <input.gif> <output.mp4> [fps]   (default fps: 12)" >&2
}

# No args: print usage + run the dependency check, then exit 0 (used by the skill's pre-flight).
if [ "$#" -eq 0 ]; then
  usage
  if command -v ffmpeg >/dev/null 2>&1 && command -v ffprobe >/dev/null 2>&1; then
    echo "ffmpeg + ffprobe: OK" >&2
    exit 0
  fi
  echo "ffmpeg/ffprobe NOT found — install ffmpeg (e.g. 'brew install ffmpeg')" >&2
  exit 3
fi

IN="${1:?input gif required}"
OUT="${2:?output mp4 required}"
FPS="${3:-12}"

command -v ffmpeg  >/dev/null 2>&1 || { echo "ffmpeg not found (brew install ffmpeg)"  >&2; exit 3; }
command -v ffprobe >/dev/null 2>&1 || { echo "ffprobe not found (brew install ffmpeg)" >&2; exit 3; }
[ -f "$IN" ] || { echo "input not found: $IN" >&2; exit 2; }

mkdir -p "$(dirname "$OUT")"

LOG="$(mktemp -t gif_to_mp4.XXXXXX)"          # unique per run so concurrent conversions don't clobber
trap 'rm -f "$LOG"' EXIT

# -movflags +faststart : web-friendly (moov atom up front)
# -pix_fmt yuv420p      : max player/decoder compatibility
# fps=$FPS              : normalize VFR gif timing to CFR (duration preserved)
# scale=even            : H.264 requires even width/height
if ! ffmpeg -y -i "$IN" \
      -movflags +faststart -pix_fmt yuv420p \
      -vf "fps=${FPS},scale=trunc(iw/2)*2:trunc(ih/2)*2" \
      "$OUT" >/dev/null 2>"$LOG"; then
  echo "ffmpeg conversion failed for: $IN" >&2
  tail -n 8 "$LOG" >&2 || true
  exit 5
fi

[ -s "$OUT" ] || { echo "conversion produced an empty file: $OUT" >&2; exit 5; }

# Emit only the real duration so the caller can parse it cleanly.
ffprobe -v error -show_entries format=duration -of csv=p=0 "$OUT"
