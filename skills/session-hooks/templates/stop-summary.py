#!/usr/bin/env python3
"""SessionEnd hook: write a per-session summary page to the wiki.

Reads the transcript pointed to by `transcript_path` in the hook input,
extracts a concise summary, and writes it as a markdown page under
`wiki/_sessions/{date}-{session-short-id}.md`.

This pairs with the SessionStart "Working Memory" pattern — the next
session can be configured to read the most recent session page so
Claude resumes with continuity.

Failure mode: silent degrade.
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime
from pathlib import Path


MAX_TRANSCRIPT_CHARS = 12000  # cap how much of the transcript we scan


def warn(msg: str) -> None:
    print(f"warn: {msg}", file=sys.stderr)


def read_transcript(path: str) -> list[dict]:
    """Transcripts are JSONL — one JSON object per line. Return list of entries."""
    if not path or not os.path.isfile(path):
        return []
    entries: list[dict] = []
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entries.append(json.loads(line))
                except Exception:
                    continue
    except Exception as e:  # noqa: BLE001
        warn(f"could not read transcript: {e}")
    return entries


def extract_user_messages(entries: list[dict]) -> list[str]:
    """Pull plain-text user messages out of the transcript."""
    out: list[str] = []
    for entry in entries:
        if entry.get("type") != "user":
            continue
        message = entry.get("message") or {}
        content = message.get("content")
        if isinstance(content, str):
            out.append(content)
        elif isinstance(content, list):
            for block in content:
                if isinstance(block, dict) and block.get("type") == "text":
                    text = block.get("text") or ""
                    if text:
                        out.append(text)
    return out


def extract_files_touched(entries: list[dict]) -> list[str]:
    """Look for file paths in tool inputs — Edit, Write, NotebookEdit."""
    seen: set[str] = set()
    for entry in entries:
        msg = entry.get("message") or {}
        content = msg.get("content")
        if not isinstance(content, list):
            continue
        for block in content:
            if not isinstance(block, dict):
                continue
            if block.get("type") != "tool_use":
                continue
            name = block.get("name", "")
            if name not in {"Edit", "Write", "MultiEdit", "NotebookEdit"}:
                continue
            inp = block.get("input") or {}
            path = inp.get("file_path") or inp.get("notebook_path")
            if path:
                seen.add(path)
    return sorted(seen)


def main() -> int:
    try:
        raw = sys.stdin.read() or "{}"
        payload = json.loads(raw)
    except Exception:
        payload = {}

    session_id = payload.get("session_id", "unknown")
    transcript_path = payload.get("transcript_path", "")
    cwd = payload.get("cwd") or os.getcwd()
    short_id = session_id[:8] if session_id != "unknown" else "session"

    wiki_dir = Path(cwd) / os.environ.get("WIKI_DIR_OVERRIDE", "wiki")
    if not wiki_dir.is_dir():
        warn(f"no wiki dir at {wiki_dir}; skipping stop-summary")
        return 0

    sessions_dir = wiki_dir / "_sessions"
    sessions_dir.mkdir(exist_ok=True)

    today = datetime.now().strftime("%Y-%m-%d")
    out_path = sessions_dir / f"{today}-{short_id}.md"

    # Idempotency: don't overwrite an existing summary for this session.
    if out_path.exists():
        return 0

    entries = read_transcript(transcript_path)
    user_msgs = extract_user_messages(entries)
    files = extract_files_touched(entries)

    first_prompt = (user_msgs[0] if user_msgs else "").strip().splitlines()[0:3]
    first_prompt_str = " / ".join(first_prompt)[:200] or "(no user messages found)"
    last_prompt = (user_msgs[-1] if user_msgs else "").strip().splitlines()[0:3]
    last_prompt_str = " / ".join(last_prompt)[:200] or ""

    lines = [
        "---",
        f"title: Session {short_id}",
        f"date: {today}",
        f"session_id: {session_id}",
        "type: session-log",
        "related: []",
        "---",
        "",
        f"# Session {short_id} — {today}",
        "",
        "## Opening prompt",
        "",
        f"> {first_prompt_str}",
        "",
    ]

    if last_prompt_str and last_prompt_str != first_prompt_str:
        lines += ["## Last prompt", "", f"> {last_prompt_str}", ""]

    if files:
        lines += ["## Files touched", ""]
        for f in files:
            lines.append(f"- `{f}`")
        lines.append("")

    lines += [
        f"## Transcript",
        "",
        f"Raw transcript: `{transcript_path}`",
        "",
        "## TODO",
        "",
        "- [ ] Promote anything worth keeping into a regular wiki page",
        "- [ ] Update related: front-matter with cross-references",
        "",
    ]

    try:
        out_path.write_text("\n".join(lines), encoding="utf-8")
    except Exception as e:  # noqa: BLE001
        warn(f"could not write session page: {e}")
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
