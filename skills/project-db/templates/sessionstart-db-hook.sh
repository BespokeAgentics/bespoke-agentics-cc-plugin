#!/usr/bin/env bash
# db-context.sh — SessionStart hook installed by the project-db skill (/db:init).
#
# Runs an incremental sync of the project database (content-hash per file, so an unchanged wiki
# costs milliseconds) and prints a one-screen banner: what is in the database, how to query it,
# where the schema lives. Anything printed here lands in Claude's context before the first prompt,
# which is what makes "query the database first" happen without anyone remembering to ask.
#
# Fast, dependency-light (python3 only), never fatal: if anything is missing it says so and exits 0.

set -uo pipefail

input="$(cat 2>/dev/null || true)"
root="${CLAUDE_PROJECT_DIR:-}"
if [ -z "$root" ] && command -v python3 >/dev/null 2>&1; then
  root="$(printf '%s' "$input" | python3 -c 'import sys,json
try: print(json.load(sys.stdin).get("cwd",""))
except Exception: print("")' 2>/dev/null || true)"
fi
[ -z "$root" ] && root="$PWD"

engine="$root/.claude/db/db.py"
[ -f "$engine" ] || exit 0

if ! command -v python3 >/dev/null 2>&1; then
  echo "🗄 project-db: python3 not found — database not synced this session (install python3, then /db:sync)"
  exit 0
fi

if out="$(cd "$root" && python3 "$engine" sync --quiet --banner 2>&1)"; then
  printf '%s\n' "$out"
else
  echo "🗄 project-db: sync failed — run /db:sync to see why"
  printf '%s\n' "$out" | tail -n 3
fi
exit 0
