#!/usr/bin/env bash
# Create a worktree that's immediately testable in isolation:
# branch off base, copy+override env, provision a local per-worktree DB,
# migrate+seed it, and reserve a collision-free migration number.
# Usage: wt-new.sh <slug> [--base <branch>] [--no-db] [--no-migrate] [--no-seed]
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=wt-common.sh
. "$HERE/wt-common.sh"

SLUG="${1:?usage: wt-new.sh <slug> [--base b] [--no-db] [--no-migrate] [--no-seed]}"; shift || true
BASE="$(wt_base_branch)"; DO_DB=1; DO_MIGRATE=1; DO_SEED=1; BRANCH_PREFIX="${WT_BRANCH_PREFIX:-feat/}"
while [ $# -gt 0 ]; do
  case "$1" in
    --base) BASE="$2"; shift 2 ;;
    --no-db) DO_DB=0; shift ;;
    --no-migrate) DO_MIGRATE=0; shift ;;
    --no-seed) DO_SEED=0; shift ;;
    *) echo "unknown flag: $1"; exit 2 ;;
  esac
done

SRC="$(wt_toplevel)"
REPO_PARENT="$(dirname "$SRC")"
REPO_BASENAME="$(basename "$SRC")"
# Sibling path: <repo>-<slug>  (matches the user's existing convention)
DEST="$REPO_PARENT/${REPO_BASENAME}-${SLUG}"
BRANCH="${BRANCH_PREFIX}${SLUG}"

[ -e "$DEST" ] && { echo "path already exists: $DEST"; exit 1; }

echo "→ creating worktree $DEST on branch $BRANCH off $BASE"
if git -C "$SRC" show-ref --verify -q "refs/heads/$BRANCH"; then
  git -C "$SRC" worktree add "$DEST" "$BRANCH"
else
  git -C "$SRC" worktree add -b "$BRANCH" "$DEST" "$BASE"
fi

# Copy env files from source worktree (they're git-ignored, so not carried by git).
echo "→ copying .env* files"
copied=0
while IFS= read -r -d '' f; do
  rel="${f#"$SRC"/}"
  mkdir -p "$DEST/$(dirname "$rel")"
  cp "$f" "$DEST/$rel"
  copied=$((copied+1))
done < <(find "$SRC" -maxdepth 3 -name '.env*' -not -path '*/node_modules/*' -print0 2>/dev/null)
echo "  copied $copied env file(s)"

# Reserve a collision-free migration number for this worktree.
RESERVED="$(bash "$HERE/wt-migrations.sh" reserve "$DEST" 2>/dev/null | tail -1 || true)"
echo "→ reserved migration number: ${RESERVED:-<none>}"

# Provision the isolated DB (this also OVERRIDES DATABASE_URL in the copied env).
if [ "$DO_DB" = 1 ]; then
  bash "$HERE/wt-db.sh" provision "$DEST"
  [ "$DO_MIGRATE" = 1 ] && bash "$HERE/wt-db.sh" migrate "$DEST"
  [ "$DO_SEED" = 1 ] && bash "$HERE/wt-db.sh" seed "$DEST" || true
else
  echo "→ skipping DB provisioning (--no-db); env still points at shared DATABASE_URL — beware."
fi

echo ""
echo "✓ worktree ready"
echo "  path:      $DEST"
echo "  branch:    $BRANCH  (base $BASE)"
[ "$DO_DB" = 1 ] && echo "  test DB:   $(wt_db_url "$DEST")"
echo "  reserved migration #: ${RESERVED:-<none>}"
echo ""
echo "  cd \"$DEST\" && bun run dev   # runs against the isolated DB — your dev data is safe"
