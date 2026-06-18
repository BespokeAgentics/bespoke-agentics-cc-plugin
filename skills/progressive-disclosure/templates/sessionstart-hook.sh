#!/usr/bin/env bash
# disclosure-context.sh — SessionStart hook installed by the progressive-disclosure skill.
#
# Anything this prints to stdout is added to Claude's context before the first prompt.
# It reads the launch directory from the hook input and surfaces the context that applies
# there: the nearest CLAUDE.md, relevant wiki page(s), and any recommended code-intelligence
# plugin. Keep it fast and side-effect-free — it runs on every session start.
#
# Generated from a template; the PATH MAP below is filled in per repository by the skill.
# Safe to re-generate via /disclosure:refresh (managed block only).

set -euo pipefail

# --- read launch dir from hook input (stdin JSON: {"cwd": "...", ...}) ---
input="$(cat 2>/dev/null || true)"
cwd=""
if command -v jq >/dev/null 2>&1; then
  cwd="$(printf '%s' "$input" | jq -r '.cwd // empty' 2>/dev/null || true)"
fi
if [ -z "$cwd" ] && command -v python3 >/dev/null 2>&1; then
  cwd="$(printf '%s' "$input" | python3 -c 'import sys,json;
try: print(json.load(sys.stdin).get("cwd",""))
except Exception: print("")' 2>/dev/null || true)"
fi
[ -z "$cwd" ] && cwd="${CLAUDE_PROJECT_DIR:-$PWD}"

root="${CLAUDE_PROJECT_DIR:-$PWD}"
# Path of the launch dir relative to the repo root (for matching the map below).
rel="${cwd#"$root"/}"
[ "$rel" = "$cwd" ] && rel="."   # launched at root

# <!-- progressive-disclosure:managed -->
# --- PATH MAP (generated) ---------------------------------------------------
# One match() call per subsystem the skill mapped. First match wins. Patterns are
# shell case-globs against $rel. Edit CLAUDE.md content, not this map — re-run
# /disclosure:refresh to regenerate after the subsystem set changes.
emit() { printf '%s\n' "$1"; }

case "$rel" in
  # {{#each SUBSYSTEMS}}
  # {{path}}*)
  #   emit "📁 {{name}} — see {{path}}/CLAUDE.md for stack, commands, conventions."
  #   {{#if wiki_link}}emit "📖 Wiki: {{wiki_link}}"{{/if}}
  #   {{#if lsp}}emit "🔎 Tip: install {{lsp}} for fast symbol lookup in this area."{{/if}}
  #   ;;
  # {{/each}}
  *)
    emit "📁 Repo context: see ./CLAUDE.md. Each package has its own CLAUDE.md that loads when you work there."
    # {{#if HAS_WIKI}}emit "📖 Knowledge base: start at wiki/_index.md (wiki-first)."{{/if}}
    ;;
esac
# <!-- /progressive-disclosure:managed -->
