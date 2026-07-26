#!/usr/bin/env bash
# Usage: setup.sh <target-dir>
# Creates a fresh instance of the py-branch fixture: main holds the legacy
# renderer; branch feature/html-rewrite switches cli to a new render_html and
# leaves the legacy renderer, a dead import, and a soon-orphaned utils chain
# behind. Working tree is clean; HEAD is the feature branch.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
TARGET="$1"
rm -rf "$TARGET"
mkdir -p "$TARGET"
cp -R "$HERE/base/." "$TARGET/"
cd "$TARGET"
git init -q -b main
git config user.email "fixture@example.com"
git config user.name "Fixture"
git add -A
git commit -qm "baseline: reportgen with legacy wrapped-HTML renderer"
git checkout -qb feature/html-rewrite
cp -R "$HERE/feature/." "$TARGET/"
git add -A
git commit -qm "feat: escape-based render_html, cli switched over"
echo "Fixture ready at $TARGET (branch feature/html-rewrite, clean tree)."
