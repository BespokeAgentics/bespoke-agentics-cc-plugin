#!/usr/bin/env bash
# Stop / SessionEnd hook: append a `## YYYY-MM-DD — <operation> — <summary>` entry to wiki/_log.md.
#
# Idempotent: uses a daily lock file so multi-firing during a session
# doesn't produce duplicate rows. (Stop hooks fire once per assistant
# turn, which can be many times per session.)
#
# Required env vars: none. Reads cwd from hook input.

set -uo pipefail
trap 'echo "warn: stop-wiki-log hook errored, continuing" >&2; exit 0' ERR

INPUT=$(cat || echo '{}')
SESSION_ID=$(echo "$INPUT" | grep -o '"session_id"[^"]*"[^"]*"' | sed 's/.*"session_id"[^"]*"\([^"]*\)"/\1/' 2>/dev/null || echo "unknown")
CWD=$(echo "$INPUT" | grep -o '"cwd"[^"]*"[^"]*"' | sed 's/.*"cwd"[^"]*"\([^"]*\)"/\1/' 2>/dev/null || pwd)

cd "$CWD" 2>/dev/null || exit 0

WIKI_DIR="${WIKI_DIR_OVERRIDE:-wiki}"
LOG="$WIKI_DIR/_log.md"

if [ ! -f "$LOG" ]; then
  echo "warn: $LOG not found; skipping (run /wiki:init first?)" >&2
  exit 0
fi

# Daily-per-session lock so this hook only writes once per session per day.
LOCK_DIR=".claude/hooks"
mkdir -p "$LOCK_DIR"
LOCK="$LOCK_DIR/.logged-$(date +%F)-${SESSION_ID:0:8}"
if [ -f "$LOCK" ]; then
  exit 0
fi
touch "$LOCK"

# Build the entry: the wiki's log format is a heading line plus a short body.
TODAY=$(date +%Y-%m-%d)
SUMMARY="claude-code session ${SESSION_ID:0:8}"

# Try to enrich with the active branch if available.
if command -v git >/dev/null 2>&1 && git rev-parse --git-dir >/dev/null 2>&1; then
  BRANCH=$(git branch --show-current 2>/dev/null || echo "")
  if [ -n "$BRANCH" ]; then
    SUMMARY="$SUMMARY on branch \`$BRANCH\`"
  fi
fi

printf '\n## %s — session — %s\n\nLogged by the stop-wiki-log hook.\n' "$TODAY" "$SUMMARY" >> "$LOG"

# Stop hooks don't inject context — output is ignored. Still exit 0.
exit 0
