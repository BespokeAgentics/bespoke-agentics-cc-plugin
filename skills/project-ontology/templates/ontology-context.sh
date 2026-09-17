#!/usr/bin/env bash
# ontology-context.sh — SessionStart hook installed by the project-ontology skill (/ontology:init).
#
# Prints a three-line banner — term counts, policy, open violations, where the rules are — so every
# session starts knowing the vocabulary is controlled. The full vault check is cached by fingerprint
# (.claude/ontology/state.json), so an unchanged vault costs a directory walk, not a re-check.
# Never fatal: anything missing is reported and the hook exits 0.

set -uo pipefail

input="$(cat 2>/dev/null || true)"
root="${CLAUDE_PROJECT_DIR:-}"
if [ -z "$root" ] && command -v python3 >/dev/null 2>&1; then
  root="$(printf '%s' "$input" | python3 -c 'import sys,json
try: print(json.load(sys.stdin).get("cwd",""))
except Exception: print("")' 2>/dev/null || true)"
fi
[ -z "$root" ] && root="$PWD"

engine="$root/.claude/ontology/ontology.py"
[ -f "$engine" ] || exit 0

if ! command -v python3 >/dev/null 2>&1; then
  echo "🧭 project-ontology: python3 not found — the ontology is not enforced this session (install python3)"
  exit 0
fi

if out="$(cd "$root" && python3 "$engine" status --banner --root "$root" 2>&1)"; then
  printf '%s\n' "$out"
else
  echo "🧭 project-ontology: status failed — run: python3 .claude/ontology/ontology.py status"
  printf '%s\n' "$out" | tail -n 3
fi
exit 0
