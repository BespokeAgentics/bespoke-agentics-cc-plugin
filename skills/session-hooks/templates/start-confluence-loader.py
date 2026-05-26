#!/usr/bin/env python3
"""SessionStart hook: pull a pinned Confluence page and inject as context.

Python variant of start-confluence-loader.sh. Use when you need richer parsing,
e.g. converting atlas_doc_format to markdown or chasing related pages.

Required env vars:
  CONFLUENCE_BASE_URL   e.g. https://yourorg.atlassian.net/wiki
  CONFLUENCE_EMAIL      your Atlassian account email
  CONFLUENCE_TOKEN      API token
  CONFLUENCE_PAGE_ID    page ID to pull

Optional:
  CONFLUENCE_MAX_CHARS  truncate body to this many chars (default 6000)

Failure mode: silent degrade. Prints warnings to stderr, exits 0 regardless.
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from base64 import b64encode


MAX_CHARS = int(os.environ.get("CONFLUENCE_MAX_CHARS", "6000"))
TIMEOUT_SECONDS = 15


def warn(msg: str) -> None:
    print(f"warn: {msg}", file=sys.stderr)


def main() -> int:
    # Drain stdin so Claude Code's pipe doesn't block.
    try:
        sys.stdin.read()
    except Exception:
        pass

    required = ["CONFLUENCE_BASE_URL", "CONFLUENCE_EMAIL", "CONFLUENCE_TOKEN", "CONFLUENCE_PAGE_ID"]
    for var in required:
        if not os.environ.get(var):
            warn(f"{var} not set; skipping confluence-loader")
            return 0

    base = os.environ["CONFLUENCE_BASE_URL"].rstrip("/")
    email = os.environ["CONFLUENCE_EMAIL"]
    token = os.environ["CONFLUENCE_TOKEN"]
    page_id = os.environ["CONFLUENCE_PAGE_ID"]

    auth = b64encode(f"{email}:{token}".encode()).decode()
    url = f"{base}/api/v2/pages/{page_id}?body-format=atlas_doc_format"
    req = urllib.request.Request(url, headers={
        "Authorization": f"Basic {auth}",
        "Accept": "application/json",
    })

    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT_SECONDS) as resp:
            payload = json.loads(resp.read().decode())
    except urllib.error.URLError as e:
        warn(f"confluence request failed: {e}")
        return 0
    except Exception as e:  # noqa: BLE001
        warn(f"unexpected error: {e}")
        return 0

    title = payload.get("title") or ""
    body = ((payload.get("body") or {}).get("atlas_doc_format") or {}).get("value") or ""
    if not title:
        warn("response missing title; skipping")
        return 0

    body = body[:MAX_CHARS]

    print(f"## Confluence — {title}")
    print()
    print("(Pinned page, auto-loaded each session.)")
    print()
    print(body)
    return 0


if __name__ == "__main__":
    sys.exit(main())
