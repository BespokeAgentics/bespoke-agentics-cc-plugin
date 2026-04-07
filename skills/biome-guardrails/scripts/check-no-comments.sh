#!/usr/bin/env bash
set -euo pipefail

SRC_DIR="${1:-src}"

if ! [ -d "$SRC_DIR" ]; then
  echo "Source directory '$SRC_DIR' not found. Skipping no-comments check."
  exit 0
fi

FOUND=$(grep -rn --include="*.ts" --include="*.tsx" --include="*.js" --include="*.jsx" '^\s*//' "$SRC_DIR" 2>/dev/null || true)

if [ -n "$FOUND" ]; then
  echo "ERROR: Comments are not allowed. Write self-documenting code instead."
  echo ""
  echo "$FOUND"
  exit 1
fi

echo "No comments found. Code is self-documenting."
