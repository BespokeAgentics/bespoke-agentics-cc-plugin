#!/usr/bin/env bash
set -euo pipefail

INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // ""')
FILENAME=$(basename "$FILE_PATH")

PROTECTED_FILES=("biome.json" "biome.jsonc" "eslint.ai-guardrails.mjs" ".eslintrc" ".eslintrc.js" ".eslintrc.json" ".eslintrc.yml" "eslint.config.js" "eslint.config.mjs" "eslint.config.ts")

for protected in "${PROTECTED_FILES[@]}"; do
  if [[ "$FILENAME" == "$protected" ]]; then
    jq -n '{
      decision: "block",
      reason: "Modifying lint config files is forbidden. These guardrails are intentional constraints on AI-generated code. If a rule makes your task impossible, stop and explain to the user why."
    }'
    exit 0
  fi
done

echo '{"decision": "approve"}'
