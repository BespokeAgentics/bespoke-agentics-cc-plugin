#!/usr/bin/env bash
# Usage: setup.sh <target-dir>
# Creates a fresh instance of the js-project fixture: a single-commit repo with
# a clean tree, containing long-accumulated dead code (old-mailer.js, median)
# alongside deliberate liveness traps (config-string webhook dispatch, bin
# entry cli.js, side-effect polyfill import, test-only csv-export).
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
git commit -qm "notifier: latency alerts, webhook routing, cli"
echo "Fixture ready at $TARGET (single commit, clean tree)."
