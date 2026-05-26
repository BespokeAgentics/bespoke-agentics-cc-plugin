#!/usr/bin/env bash
# SessionStart hook: Pull a pinned Confluence page and inject its contents
# as additionalContext so every session starts with the canonical spec.
#
# Required env vars:
#   CONFLUENCE_BASE_URL   e.g. https://yourorg.atlassian.net/wiki
#   CONFLUENCE_EMAIL      your Atlassian account email
#   CONFLUENCE_TOKEN      API token from id.atlassian.com/manage-profile/security/api-tokens
#   CONFLUENCE_PAGE_ID    the page ID to pull (or use CONFLUENCE_SPACE_KEY for a space root)
#
# Failure mode: silent degrade. If anything fails, prints warning to stderr,
# emits no additionalContext, exits 0.

set -uo pipefail

# Hooks must never crash the session. Catch errors and degrade.
trap 'echo "warn: confluence-loader hook errored, continuing without context" >&2; exit 0' ERR

# Drain stdin so Claude Code doesn't block. We don't use the input here.
cat >/dev/null

# Bail gracefully if any required var is missing.
for var in CONFLUENCE_BASE_URL CONFLUENCE_EMAIL CONFLUENCE_TOKEN CONFLUENCE_PAGE_ID; do
  if [ -z "${!var:-}" ]; then
    echo "warn: $var not set; skipping confluence-loader hook" >&2
    exit 0
  fi
done

# Pull the page. v2 API returns clean storage-format HTML/markdown.
RESPONSE=$(curl --silent --show-error --max-time 20 \
  -u "$CONFLUENCE_EMAIL:$CONFLUENCE_TOKEN" \
  -H "Accept: application/json" \
  "$CONFLUENCE_BASE_URL/api/v2/pages/$CONFLUENCE_PAGE_ID?body-format=atlas_doc_format")

if [ -z "$RESPONSE" ]; then
  echo "warn: empty response from Confluence" >&2
  exit 0
fi

TITLE=$(echo "$RESPONSE" | jq -r '.title // empty')
BODY=$(echo "$RESPONSE" | jq -r '.body.atlas_doc_format.value // empty' | head -c 8000)

if [ -z "$TITLE" ]; then
  echo "warn: confluence response had no title; skipping" >&2
  exit 0
fi

# Plain stdout becomes additionalContext on SessionStart.
echo "## Confluence — $TITLE"
echo ""
echo "(Pinned page, auto-loaded each session. Last fetched: $(date '+%Y-%m-%d %H:%M').)"
echo ""
echo "$BODY"

exit 0
