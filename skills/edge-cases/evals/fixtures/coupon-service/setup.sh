#!/usr/bin/env bash
# Usage: setup.sh <target-dir>
# Creates a fresh instance of the coupon-service fixture: a git repo whose HEAD is the
# baseline (percent coupons only), with the session's fixed-amount-coupon change sitting
# UNCOMMITTED in the working tree.
#
# Planted edge cases (the evals check for these; keep this list in step with evals.json):
#   baseline  coupons.js     `subtotal > minSubtotal` refuses an order of exactly $50 ("$50 or more")
#   baseline  coupons.js     `COUPONS[code]` is case-sensitive and untrimmed ("case-insensitive")
#   baseline  coupons.js     `new Date('2026-12-31')` is UTC midnight: the coupon dies a day early
#                            in US time zones ("valid through the end of its expiry date")
#   baseline  coupons.js     percent discount is not rounded to cents (33.33 * 10% = 3.333)
#   baseline  redemptions.js check-then-act across `await`: two concurrent redeems both pass maxUses
#   session   coupons.js     FIVEOFF on a $3 cart gives total -2 (amount larger than subtotal)
#   session   receipt.js     (unchanged caller) prints "saved undefined%" for an amount coupon
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
git commit -qm "baseline: percent coupons, redemptions, receipts"
cp -R "$HERE/session/." "$TARGET/"
echo "Fixture ready at $TARGET (uncommitted fixed-amount coupon change in working tree)."
