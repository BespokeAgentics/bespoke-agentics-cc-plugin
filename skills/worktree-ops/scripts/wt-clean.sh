#!/usr/bin/env bash
# Safely tear down a worktree: drop its isolated DB, remove the worktree,
# release its migration reservation. Guardrails block loss of uncommitted or
# unpushed work unless --force AND typed confirmation.
# Usage: wt-clean.sh <worktree-path> [--force] [--confirm <basename>]
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=wt-common.sh
. "$HERE/wt-common.sh"

WT="${1:?usage: wt-clean.sh <worktree-path> [--force] [--confirm <basename>]}"; shift || true
FORCE=0; CONFIRM=""
while [ $# -gt 0 ]; do
  case "$1" in
    --force) FORCE=1; shift ;;
    --confirm) CONFIRM="$2"; shift 2 ;;
    *) echo "unknown flag: $1"; exit 2 ;;
  esac
done

WT="$(cd "$WT" 2>/dev/null && pwd || echo "$WT")"
[ -d "$WT" ] || { echo "not a directory: $WT"; exit 1; }

MAIN="$(wt_toplevel)"
if [ "$WT" = "$MAIN" ]; then echo "GUARDRAIL: refusing to remove the current worktree."; exit 1; fi

# Guardrail 1: uncommitted changes
if [ -n "$(git -C "$WT" status --porcelain 2>/dev/null)" ]; then
  echo "GUARDRAIL: $WT has uncommitted changes."
  [ "$FORCE" = 1 ] || { echo "Commit/stash first, or pass --force --confirm $(basename "$WT")."; exit 1; }
fi

# Guardrail 2: unpushed commits
branch="$(git -C "$WT" rev-parse --abbrev-ref HEAD 2>/dev/null || echo '')"
upstream="$(git -C "$WT" rev-parse --abbrev-ref --symbolic-full-name '@{u}' 2>/dev/null || true)"
unpushed=0
if [ -n "$upstream" ]; then
  n="$(git -C "$WT" rev-list --count "$upstream..HEAD" 2>/dev/null || echo 0)"
  [ "${n:-0}" -gt 0 ] && unpushed=1
else
  unpushed=1
fi
if [ "$unpushed" = 1 ]; then
  echo "GUARDRAIL: $WT ($branch) has commits not on any remote (or no upstream)."
  [ "$FORCE" = 1 ] || { echo "Push first, or pass --force --confirm $(basename "$WT")."; exit 1; }
fi

# Typed confirmation required whenever --force overrides a guardrail.
if [ "$FORCE" = 1 ]; then
  [ "$CONFIRM" = "$(basename "$WT")" ] || { echo "GUARDRAIL: --force requires --confirm $(basename "$WT")"; exit 1; }
fi

echo "→ dropping isolated DB for $WT"
bash "$HERE/wt-db.sh" drop "$WT" || true

echo "→ releasing migration reservation"
bash "$HERE/wt-migrations.sh" release "$WT" || true

echo "→ git worktree remove"
git -C "$MAIN" worktree remove "$WT" ${FORCE:+--force} 2>/dev/null || git -C "$MAIN" worktree remove --force "$WT"

# Delete the local branch only if fully merged into base (never force-delete unmerged).
if [ -n "$branch" ] && git -C "$MAIN" branch --merged "$(wt_base_branch)" 2>/dev/null | grep -qE "^\+?\s*${branch}$"; then
  git -C "$MAIN" branch -d "$branch" 2>/dev/null || true
  echo "✓ deleted merged branch $branch"
else
  echo "  kept branch $branch (not fully merged into $(wt_base_branch))"
fi

echo "✓ cleaned up $WT"
