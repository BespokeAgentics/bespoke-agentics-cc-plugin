#!/usr/bin/env bash
# SessionStart hook: inject a "where you left off" snapshot of the codebase.
# Includes branch, status, recent commits, and a short list of recently
# modified files.
#
# No external dependencies beyond git.

set -uo pipefail
trap 'echo "warn: codebase-snapshot hook errored, continuing" >&2; exit 0' ERR

# Drain stdin.
cat >/dev/null

if ! command -v git >/dev/null 2>&1; then
  echo "warn: git not installed; skipping codebase-snapshot" >&2
  exit 0
fi

if ! git rev-parse --git-dir >/dev/null 2>&1; then
  echo "warn: not a git repo; skipping codebase-snapshot" >&2
  exit 0
fi

BRANCH=$(git branch --show-current 2>/dev/null || echo "(detached)")
DIRTY=$(git status --porcelain 2>/dev/null | wc -l | tr -d ' ')

echo "## Codebase snapshot"
echo ""
echo "- **Branch:** \`$BRANCH\`"
echo "- **Uncommitted changes:** $DIRTY file(s)"
echo ""

echo "### Recent commits"
echo ""
echo "\`\`\`"
git log --oneline --decorate -10 2>/dev/null || echo "(no commits)"
echo "\`\`\`"
echo ""

if [ "$DIRTY" -gt 0 ]; then
  echo "### Uncommitted files"
  echo ""
  echo "\`\`\`"
  git status --short 2>/dev/null | head -20
  echo "\`\`\`"
  echo ""
fi

echo "### Files modified in the last 24h"
echo ""
echo "\`\`\`"
git log --since="24 hours ago" --name-only --pretty=format: 2>/dev/null | sort -u | grep -v '^$' | head -15 || echo "(none)"
echo "\`\`\`"

exit 0
