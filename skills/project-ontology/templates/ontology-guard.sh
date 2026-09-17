#!/usr/bin/env bash
# ontology-guard.sh — installed by the project-ontology skill (/ontology:init). One script, three events:
#
#   pre   PreToolUse  Write|Edit|MultiEdit  reconstruct the post-write file, block (exit 2) only the strict
#                                           violations this write ADDS (ratchet); guard ontology.yaml itself
#   post  PostToolUse Write|Edit|MultiEdit  non-blocking additionalContext: what still stands in the file
#   bash  PreToolUse  Bash                  approve/deprecate → permission prompt (human gate); shell writes
#                                           into governed pages → blocked (use Write/Edit so the check runs)
#
# The rules live in .claude/ontology/ontology.py — the same code wiki-lint, CI and project-db run.

set -uo pipefail

mode="${1:-pre}"
root="${CLAUDE_PROJECT_DIR:-$PWD}"
engine="$root/.claude/ontology/ontology.py"
[ -f "$engine" ] || exit 0

if ! command -v python3 >/dev/null 2>&1; then
  if [ "$mode" = "pre" ]; then
    echo "project-ontology: python3 not found — the ontology is NOT being enforced on this write" >&2
  fi
  exit 0
fi

input="$(cat 2>/dev/null || true)"

if [ "$mode" = "bash" ]; then
  # fast path: almost every Bash call touches neither the ontology engine nor a markdown page
  case "$input" in
    *ontology.py*|*.md*) ;;
    *) exit 0 ;;
  esac
fi

printf '%s' "$input" | python3 "$engine" hook "$mode" --root "$root"
exit $?
