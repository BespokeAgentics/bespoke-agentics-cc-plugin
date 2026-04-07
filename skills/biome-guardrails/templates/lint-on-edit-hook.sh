#!/usr/bin/env bash
set -euo pipefail

INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // ""')

if [[ "$FILE_PATH" != *.ts && "$FILE_PATH" != *.tsx && "$FILE_PATH" != *.js && "$FILE_PATH" != *.jsx ]]; then
  echo '{"decision": "approve"}'
  exit 0
fi

# __PMX__ is replaced by the skill with the detected package manager exec command (npx/bunx/pnpm dlx/yarn dlx)
PMX="__PMX__"
if ! command -v "${PMX%% *}" &>/dev/null; then
  echo '{"decision": "approve"}'
  exit 0
fi

HASH=$(echo -n "$FILE_PATH" | md5sum 2>/dev/null | cut -d' ' -f1 || echo "$FILE_PATH" | md5 2>/dev/null || echo "fallback")
ATTEMPT_FILE="/tmp/lint_attempts_${HASH}"
ATTEMPT=$(cat "$ATTEMPT_FILE" 2>/dev/null || echo 0)

LINT_OUTPUT=$($PMX biome check "$FILE_PATH" 2>&1) || true
LINT_EXIT_CODE=${PIPESTATUS[0]:-$?}

if [ "$LINT_EXIT_CODE" -ne 0 ] 2>/dev/null; then
  ATTEMPT=$((ATTEMPT + 1))
  echo "$ATTEMPT" > "$ATTEMPT_FILE"

  if [ "$ATTEMPT" -ge 3 ]; then
    jq -n --arg out "$LINT_OUTPUT" '{
      decision: "approve",
      reason: ("CRITICAL: File has failed linting 3 times. STOP. Report the lint errors to the user and do not attempt further fixes without their guidance.\n\n" + $out)
    }'
  else
    jq -n --arg out "$LINT_OUTPUT" '{
      decision: "approve",
      reason: ("Linting failed. Fix these errors before continuing:\n\n" + $out)
    }'
  fi
else
  rm -f "$ATTEMPT_FILE" 2>/dev/null || true
  echo '{"decision": "approve"}'
fi
