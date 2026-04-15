#!/bin/bash
# PostToolUse hook: AI Transparency Check
# Enforces "No Black Boxes" policy after edits to AI-related files.
# Framework-agnostic: detects any AI/LLM SDK usage and checks for
# proper state management, progress tracking, and error handling.

set -euo pipefail

INPUT=$(cat)

TOOL_NAME=$(echo "$INPUT" | jq -r '.tool_name // ""')
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // ""')

# Only trigger on file-modifying tools
case "$TOOL_NAME" in
  Write|Edit|MultiEdit) ;;
  *) exit 0 ;;
esac

# Skip if file doesn't exist or is empty
if [ ! -f "$FILE_PATH" ] || [ ! -s "$FILE_PATH" ]; then
  exit 0
fi

FILE_CONTENT=$(cat "$FILE_PATH")

# --- Detect if this is an AI-related backend file ---
IS_AI_BACKEND=false
HAS_AI_SDK=$(echo "$FILE_CONTENT" | grep -cE \
  'from .anthropic|from .openai|@anthropic-ai/sdk|@ai-sdk/|from .langchain|from .cohere|google\.generativeai|client\.messages\.(create|stream)|openai\.chat\.completions\.create|new Anthropic\(|new OpenAI\(|ChatOpenAI|generateText|streamText|model\.generate_content' || true)

if [ "$HAS_AI_SDK" -gt 0 ]; then
  IS_AI_BACKEND=true
fi

# --- Detect if this is a frontend component file ---
IS_AI_UI=false
case "$FILE_PATH" in
  *.tsx|*.jsx|*.vue|*.svelte) IS_AI_UI=true ;;
esac

# Skip if not an AI-related file
if [ "$IS_AI_BACKEND" = false ] && [ "$IS_AI_UI" = false ]; then
  exit 0
fi

WARNINGS=""

# --- Backend AI Transparency Checks ---
if [ "$IS_AI_BACKEND" = true ]; then

  # Check: File calls AI SDK but has no progress/activity logging
  HAS_LOGGING=$(echo "$FILE_CONTENT" | grep -cE \
    'logActivity|logAuditEvent|logger\.(info|log|debug)|console\.(log|info).*status|emit\(.*progress|dispatch\(.*progress|setProgress|updateProgress|onProgress' || true)

  HAS_STATUS=$(echo "$FILE_CONTENT" | grep -cE \
    'status\s*[:=].*"(processing|completed|failed|error|running|ready|pending)"|\.status\s*=|setStatus|updateStatus|setState.*status' || true)

  if [ "$HAS_AI_SDK" -gt 0 ] && [ "$HAS_LOGGING" -eq 0 ]; then
    WARNINGS="${WARNINGS}
- CRITICAL: $(basename "$FILE_PATH") calls an AI/LLM SDK but has NO progress or activity logging. AI operations must log progress at each processing phase so users have visibility."
  fi

  if [ "$HAS_AI_SDK" -gt 0 ] && [ "$HAS_STATUS" -eq 0 ]; then
    WARNINGS="${WARNINGS}
- BLOCKING: $(basename "$FILE_PATH") calls an AI/LLM SDK but never sets a status field (processing/completed/failed). AI operations must track status for UI subscriptions."
  fi
fi

# --- UI AI Transparency Checks ---
if [ "$IS_AI_UI" = true ]; then

  # Check: Component triggers AI-related work but has no status subscription
  HAS_AI_TRIGGER=$(echo "$FILE_CONTENT" | grep -cE \
    'use(Mutation|Action)\(.*\b(ai|analy|generat|decompos|scor|assess|refin|recommend|evaluat|transcri|summar|classify|predict|embed)|fetch\(.*\b(ai|generat|analy|predict)|\.mutate\(.*\b(ai|generat)|invoke.*\b(ai|generat)' || true)

  HAS_STATUS_SUB=$(echo "$FILE_CONTENT" | grep -cE \
    'useQuery\(.*\b(status|progress|activity|log)|useSubscription|useSWR.*status|onSnapshot.*status|subscribe\(.*status|EventSource|useEventSource' || true)

  if [ "$HAS_AI_TRIGGER" -gt 0 ] && [ "$HAS_STATUS_SUB" -eq 0 ]; then
    WARNINGS="${WARNINGS}
- BLOCKING: $(basename "$FILE_PATH") triggers AI work but has no subscription for status/progress/activity. Users need real-time visibility into AI operations."
  fi

  # Check: Component has AI loading state but no error state
  HAS_LOADING=$(echo "$FILE_CONTENT" | grep -cE \
    'isLoading|isProcessing|isExecuting|isAnalyzing|isGenerating|isPending|isSubmitting' || true)

  HAS_ERROR_STATE=$(echo "$FILE_CONTENT" | grep -cE \
    'status.*===.*"(failed|error)"|isError|error\s*&&|\.error\b|onError|catch\s*\(' || true)

  if [ "$HAS_LOADING" -gt 0 ] && [ "$HAS_ERROR_STATE" -eq 0 ]; then
    WARNINGS="${WARNINGS}
- WARNING: $(basename "$FILE_PATH") has AI loading states but no error/failure UI branch. Add error handling with a user-visible message and retry action."
  fi
fi

# --- Output warnings as systemMessage ---
if [ -n "$WARNINGS" ]; then
  MESSAGE="[AI Transparency] \"No Black Boxes\" policy violations in $(basename "$FILE_PATH"):
${WARNINGS}

Run /bespokeagentics:ai-transparency $(basename "$FILE_PATH") for detailed audit and fixes."
  jq -n --arg msg "$MESSAGE" '{"systemMessage": $msg}'
fi

exit 0
