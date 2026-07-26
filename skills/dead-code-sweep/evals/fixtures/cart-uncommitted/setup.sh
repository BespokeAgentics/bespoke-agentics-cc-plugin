#!/usr/bin/env bash
# Usage: setup.sh <target-dir>
# Creates a fresh instance of the cart-uncommitted fixture: a git repo whose HEAD
# is the pre-session baseline, with the session's refactor sitting UNCOMMITTED
# in the working tree. The session removed lineItem, migrated discounts to
# applyDiscount, and left dead code behind.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
TARGET="$1"
rm -rf "$TARGET"
mkdir -p "$TARGET"
cp -R "$HERE/base/." "$TARGET/"
cd "$TARGET"
git init -q
git config user.email "fixture@example.com"
git config user.name "Fixture"
git add -A
git commit -qm "baseline: cart library with seasonal coupon discounts"
# Session changes: uncommitted working-tree edits, deliberately not staged.
cp -R "$HERE/session/." "$TARGET/"
echo "Fixture ready at $TARGET (uncommitted session changes in working tree)."
