#!/usr/bin/env bash
# find_download.sh <glob> <dest-path> [download-dir]
#
# The Claude-in-Chrome gif_creator `export {download:true}` saves the GIF to Chrome's download
# directory (usually ~/Downloads), not to the project. This finds the newest file matching <glob> in
# that directory and moves it to <dest-path>, printing the destination on success.
#
# Exit codes: 2 bad args, 4 no match found (caller should ask the user for the real download dir).
set -euo pipefail

GLOB="${1:?filename glob required, e.g. 'my-capture*.gif'}"
DEST="${2:?destination path required}"
DIR="${3:-$HOME/Downloads}"
DIR="${DIR/#\~/$HOME}"   # expand a leading ~ if the caller passed one literally (quoted args don't expand)

[ -d "$DIR" ] || { echo "download dir not found: $DIR" >&2; exit 2; }
mkdir -p "$(dirname "$DEST")"

# Newest match first. `ls -t` on the glob; guard the no-match case so `set -e` doesn't abort.
NEWEST="$(ls -t "$DIR"/$GLOB 2>/dev/null | head -n1 || true)"

if [ -z "$NEWEST" ] || [ ! -f "$NEWEST" ]; then
  echo "no file matching '$GLOB' in $DIR" >&2
  exit 4
fi

mv -f "$NEWEST" "$DEST"
echo "$DEST"
