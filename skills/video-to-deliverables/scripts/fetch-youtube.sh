#!/usr/bin/env bash
# fetch-youtube.sh — download a YouTube video and (if available) its auto-captions
# into a video-extraction directory, normalized for the video-to-deliverables pipeline.
#
# Outputs (on success):
#   {OUT_DIR}/source.mp4           — the downloaded video, re-muxed to mp4 if needed
#   {OUT_DIR}/auto-captions.vtt    — English auto-captions, if available
#   {OUT_DIR}/youtube-meta.json    — metadata (title, uploader, url, duration) for provenance
#
# Exit codes:
#   0 success
#   1 missing dependency
#   2 invalid URL or download failure
#   3 output directory not writable

set -euo pipefail

usage() {
  cat <<'EOF'
Usage: fetch-youtube.sh <youtube-url> <out-dir>

Downloads the video to <out-dir>/source.mp4 and English auto-captions (if
available) to <out-dir>/auto-captions.vtt. Also writes youtube-meta.json with
provenance data for citation downstream.

Requires: yt-dlp, ffmpeg, jq.
EOF
  exit 64
}

[[ $# -eq 2 ]] || usage

URL="$1"
OUT_DIR="$2"

# Basic URL sanity check.
if ! [[ "$URL" =~ ^https?://(www\.)?(youtube\.com|youtu\.be)/ ]]; then
  echo "ERROR: not a YouTube URL: $URL" >&2
  exit 2
fi

# Dependency checks.
for bin in yt-dlp ffmpeg jq; do
  if ! command -v "$bin" >/dev/null 2>&1; then
    echo "ERROR: required dependency not installed: $bin" >&2
    case "$bin" in
      yt-dlp) echo "  Install with: brew install yt-dlp  (or: pip install --upgrade yt-dlp)" >&2 ;;
      ffmpeg) echo "  Install with: brew install ffmpeg" >&2 ;;
      jq)     echo "  Install with: brew install jq" >&2 ;;
    esac
    exit 1
  fi
done

# Make sure output dir is writable.
mkdir -p "$OUT_DIR" || { echo "ERROR: cannot create $OUT_DIR" >&2; exit 3; }
[[ -w "$OUT_DIR" ]] || { echo "ERROR: $OUT_DIR is not writable" >&2; exit 3; }

echo "==> Fetching metadata..."
META_JSON="$OUT_DIR/.yt-meta-raw.json"
if ! yt-dlp --quiet --no-warnings --dump-single-json --no-playlist "$URL" > "$META_JSON"; then
  echo "ERROR: yt-dlp failed to fetch metadata for $URL" >&2
  rm -f "$META_JSON"
  exit 2
fi

# Normalized metadata for downstream citation.
jq '{
  id:          .id,
  title:       .title,
  uploader:    .uploader,
  upload_date: .upload_date,
  duration:    .duration,
  webpage_url: .webpage_url,
  description: (.description | if . then (. | split("\n") | .[0:10] | join("\n")) else null end)
}' "$META_JSON" > "$OUT_DIR/youtube-meta.json"
rm -f "$META_JSON"

TITLE=$(jq -r '.title' "$OUT_DIR/youtube-meta.json")
DURATION=$(jq -r '.duration' "$OUT_DIR/youtube-meta.json")
echo "    title:    $TITLE"
echo "    duration: ${DURATION}s"

echo "==> Downloading video to $OUT_DIR/source.mp4 ..."
# Prefer an mp4-compatible stream; remux to mp4 if the best formats aren't already mp4.
yt-dlp \
  --quiet --no-warnings \
  --no-playlist \
  --format "bv*[ext=mp4]+ba[ext=m4a]/bv*+ba/b" \
  --merge-output-format mp4 \
  --output "$OUT_DIR/source.%(ext)s" \
  "$URL" \
  || { echo "ERROR: video download failed" >&2; exit 2; }

# If yt-dlp saved as something other than mp4 (e.g. .mkv), re-mux.
if [[ ! -f "$OUT_DIR/source.mp4" ]]; then
  for cand in "$OUT_DIR"/source.*; do
    [[ -f "$cand" ]] || continue
    echo "==> Remuxing $cand -> source.mp4"
    ffmpeg -y -loglevel error -i "$cand" -c copy "$OUT_DIR/source.mp4" || {
      echo "ERROR: ffmpeg remux failed" >&2
      exit 2
    }
    rm -f "$cand"
    break
  done
fi

[[ -f "$OUT_DIR/source.mp4" ]] || { echo "ERROR: source.mp4 missing after download" >&2; exit 2; }

echo "==> Attempting to fetch English auto-captions..."
# Non-fatal — many videos don't have captions.
yt-dlp \
  --quiet --no-warnings \
  --no-playlist \
  --skip-download \
  --write-auto-subs \
  --sub-langs 'en.*' \
  --convert-subs vtt \
  --output "$OUT_DIR/captions.%(ext)s" \
  "$URL" 2>/dev/null || true

# yt-dlp names auto-caption files like captions.en.vtt or captions.en-US.vtt — pick the first.
for cand in "$OUT_DIR"/captions.en*.vtt "$OUT_DIR"/captions.*.vtt; do
  [[ -f "$cand" ]] || continue
  mv "$cand" "$OUT_DIR/auto-captions.vtt"
  echo "    captured auto-captions to $OUT_DIR/auto-captions.vtt"
  break
done
# Clean up any remaining caption scraps.
rm -f "$OUT_DIR"/captions.*.vtt "$OUT_DIR"/captions.*.srt 2>/dev/null || true

if [[ ! -f "$OUT_DIR/auto-captions.vtt" ]]; then
  echo "    (no auto-captions available — transcription will run normally)"
fi

echo "==> Done. Video: $OUT_DIR/source.mp4"
exit 0
