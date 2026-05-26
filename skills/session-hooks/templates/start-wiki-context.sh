#!/usr/bin/env bash
# SessionStart hook: inject the wiki index + recent log entries so every
# Claude Code session starts with current wiki state.
#
# Reads:
#   {{WIKI_DIR}}/_index.md           — list of wiki pages
#   {{WIKI_DIR}}/_log.md             — recent activity log (tail)
#
# No external dependencies. Pure file reads.

set -uo pipefail
trap 'echo "warn: wiki-context hook errored, continuing" >&2; exit 0' ERR

# Parse hook input for cwd; fall back to PWD.
INPUT=$(cat || echo '{}')
CWD=$(echo "$INPUT" | grep -o '"cwd"[^"]*"[^"]*"' | sed 's/.*"cwd"[^"]*"\([^"]*\)"/\1/' 2>/dev/null || pwd)
cd "$CWD" 2>/dev/null || cd "$(pwd)"

WIKI_DIR="${WIKI_DIR_OVERRIDE:-wiki}"

if [ ! -d "$WIKI_DIR" ]; then
  echo "warn: no $WIKI_DIR/ directory; skipping wiki-context" >&2
  exit 0
fi

echo "## Wiki Pulse"
echo ""
echo "_Auto-loaded from \`$WIKI_DIR/\` on session start._"
echo ""

if [ -f "$WIKI_DIR/_index.md" ]; then
  echo "### Index"
  head -c 2000 "$WIKI_DIR/_index.md"
  echo ""
  echo ""
fi

if [ -f "$WIKI_DIR/_log.md" ]; then
  echo "### Recent activity (last 20 log entries)"
  echo ""
  # Print the table header (first 2 lines) + the last 20 data rows.
  head -2 "$WIKI_DIR/_log.md"
  tail -20 "$WIKI_DIR/_log.md"
fi

exit 0
