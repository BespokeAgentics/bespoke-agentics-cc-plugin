#!/usr/bin/env bash
# Copy the teamboard fixture (source-app + micros-workspace) to a working
# directory so eval runs never mutate the pristine fixture.
# Usage: setup.sh <dest-dir>
set -euo pipefail

dest="${1:?usage: setup.sh <dest-dir>}"
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

mkdir -p "$dest"
cp -R "$here/source-app" "$dest/source-app"
cp -R "$here/micros-workspace" "$dest/micros-workspace"

echo "fixture ready:"
echo "  source-app:       $dest/source-app"
echo "  micros-workspace: $dest/micros-workspace"
