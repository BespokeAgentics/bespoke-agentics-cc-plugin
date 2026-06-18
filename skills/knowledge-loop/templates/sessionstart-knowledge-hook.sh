#!/usr/bin/env bash
# knowledge-context.sh — SessionStart hook installed by the knowledge-loop skill (/knowledge:init).
#
# Anything this prints to stdout is added to Claude's context before the first prompt. It surfaces
# the RULES IN EFFECT from the knowledge store so the agent applies confirmed knowledge by default
# from the very first message, and reminds it to run the loop (review before / extract after a task).
#
# Fast, read-only, dependency-light (grep/sed/awk only — no jq required). Safe to re-generate via
# /knowledge:init; only the managed block below is owned by the skill.

set -euo pipefail

# --- read launch dir from hook input (stdin JSON: {"cwd": "...", ...}) ---
input="$(cat 2>/dev/null || true)"
cwd=""
if command -v python3 >/dev/null 2>&1; then
  cwd="$(printf '%s' "$input" | python3 -c 'import sys,json
try: print(json.load(sys.stdin).get("cwd",""))
except Exception: print("")' 2>/dev/null || true)"
fi
[ -z "$cwd" ] && cwd="${CLAUDE_PROJECT_DIR:-$PWD}"
root="${CLAUDE_PROJECT_DIR:-$cwd}"

# <!-- knowledge-loop:managed -->
# --- STORE PATH (generated) -------------------------------------------------
# Relative to the repo root. /knowledge:init fills this in (wiki/knowledge or knowledge).
STORE_REL="wiki/knowledge"
MAX_RULES=20   # cap output so the banner never floods context

store="$root/$STORE_REL"
[ -d "$store" ] || exit 0   # no store yet — stay silent

emit() { printf '%s\n' "$1"; }

# Count domains = immediate subdirs of the store that contain a rules.md
domains=0
rules_total=0
for d in "$store"/*/; do
  [ -f "${d}rules.md" ] || continue
  domains=$((domains + 1))
  n=$(grep -c '^### ' "${d}rules.md" 2>/dev/null || echo 0)
  rules_total=$((rules_total + n))
done

[ "$domains" -eq 0 ] && exit 0

emit "🧠 Knowledge loop active — ${rules_total} rule(s) in effect across ${domains} domain(s) (apply by default)."

# List rule headlines (capped). Each '### ' line in a domain's rules.md is one rule.
shown=0
for d in "$store"/*/; do
  [ -f "${d}rules.md" ] || continue
  dom="$(basename "$d")"
  while IFS= read -r line; do
    [ "$shown" -ge "$MAX_RULES" ] && break 2
    # strip leading '#'s + space and any trailing '(apply by default)' / whitespace
    title=$(printf '%s' "$line" | sed -E 's/^#+[[:space:]]+//; s/[[:space:]]*\(apply by default\)[[:space:]]*$//; s/[[:space:]]+$//')
    emit "  • [${dom}] ${title}"
    shown=$((shown + 1))
  done < <(grep '^### ' "${d}rules.md" 2>/dev/null || true)
done

[ "$rules_total" -gt "$MAX_RULES" ] && emit "  … and $((rules_total - MAX_RULES)) more — see ${STORE_REL}/INDEX.md"
emit "↪ Before a task: /knowledge:review   •   After a task: /knowledge:extract"
# <!-- /knowledge-loop:managed -->
