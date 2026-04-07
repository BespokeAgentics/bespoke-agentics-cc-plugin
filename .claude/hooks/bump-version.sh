#!/usr/bin/env bash
# Pre-commit hook: auto-bump patch version in plugin.json and marketplace.json
# Receives PreToolUse JSON via stdin, checks for git commit, bumps version if matched.

set -euo pipefail

INPUT=$(cat)

# Extract the bash command from hook input
COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // ""')

# Only act on git commit commands (not amend-only or other git subcommands)
if ! echo "$COMMAND" | grep -qE 'git\s+commit'; then
  exit 0
fi

PROJECT_DIR=$(echo "$INPUT" | jq -r '.cwd')
PLUGIN_JSON="$PROJECT_DIR/.claude-plugin/plugin.json"
MARKETPLACE_JSON="$PROJECT_DIR/.claude-plugin/marketplace.json"

# Bail if plugin files don't exist
if [ ! -f "$PLUGIN_JSON" ] || [ ! -f "$MARKETPLACE_JSON" ]; then
  exit 0
fi

# Read current version from plugin.json
CURRENT_VERSION=$(jq -r '.version' "$PLUGIN_JSON")

# Parse semver components
IFS='.' read -r MAJOR MINOR PATCH <<< "$CURRENT_VERSION"

# Bump patch
NEW_PATCH=$((PATCH + 1))
NEW_VERSION="${MAJOR}.${MINOR}.${NEW_PATCH}"

# Update plugin.json
jq --arg v "$NEW_VERSION" '.version = $v' "$PLUGIN_JSON" > "${PLUGIN_JSON}.tmp" && mv "${PLUGIN_JSON}.tmp" "$PLUGIN_JSON"

# Update marketplace.json (top-level version + plugins[0].version)
jq --arg v "$NEW_VERSION" '.version = $v | .plugins[0].version = $v' "$MARKETPLACE_JSON" > "${MARKETPLACE_JSON}.tmp" && mv "${MARKETPLACE_JSON}.tmp" "$MARKETPLACE_JSON"

# Stage the updated files so they're included in the commit
git -C "$PROJECT_DIR" add "$PLUGIN_JSON" "$MARKETPLACE_JSON"

# Report what happened via systemMessage
echo "{\"decision\": \"approve\", \"reason\": \"Bumped version $CURRENT_VERSION → $NEW_VERSION\", \"systemMessage\": \"Auto-bumped plugin version: $CURRENT_VERSION → $NEW_VERSION\"}"
