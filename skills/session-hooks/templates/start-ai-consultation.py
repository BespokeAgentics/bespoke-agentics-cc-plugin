#!/usr/bin/env python3
"""SessionStart hook: ask a *different* model for a "second opinion" framing
before Claude starts.

The idea: at session start, send a small prompt to another LLM (OpenAI,
Gemini, etc.) along with the project's CLAUDE.md, and inject its reply
as context. Claude then begins the session having seen another model's
read of the situation.

Required env vars:
  CONSULT_PROVIDER     "openai" | "anthropic" | "gemini"
  CONSULT_MODEL        e.g. "gpt-5", "claude-opus-4-6", "gemini-3-pro"
  CONSULT_API_KEY      provider API key

Optional:
  CONSULT_PROMPT_FILE  path to a custom system prompt (default: built-in)
  CONSULT_MAX_TOKENS   default 400 — keep small, this is just framing

Failure mode: silent degrade.
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request


DEFAULT_PROMPT = """You are advising another AI agent (Claude Code) that is
about to start a coding/work session in the project described below.

Your job: in 3-5 bullets, surface the most important questions or framing
considerations the agent should hold in mind before doing any work.

Be specific to the project context. Do not give generic advice. Skip
preamble — start directly with the bullets."""


def warn(msg: str) -> None:
    print(f"warn: {msg}", file=sys.stderr)


def load_claude_md(cwd: str) -> str:
    for candidate in ("CLAUDE.md", "README.md", ".claude/CLAUDE.md"):
        path = os.path.join(cwd, candidate)
        if os.path.isfile(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return f.read()[:8000]
            except Exception:
                continue
    return ""


def call_openai(model: str, key: str, system: str, user: str, max_tokens: int) -> str | None:
    payload = json.dumps({
        "model": model,
        "max_tokens": max_tokens,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    }).encode()
    req = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=payload,
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode())
        return data["choices"][0]["message"]["content"]
    except Exception as e:  # noqa: BLE001
        warn(f"openai call failed: {e}")
        return None


def call_anthropic(model: str, key: str, system: str, user: str, max_tokens: int) -> str | None:
    payload = json.dumps({
        "model": model,
        "max_tokens": max_tokens,
        "system": system,
        "messages": [{"role": "user", "content": user}],
    }).encode()
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=payload,
        headers={
            "x-api-key": key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode())
        return data["content"][0]["text"]
    except Exception as e:  # noqa: BLE001
        warn(f"anthropic call failed: {e}")
        return None


def call_gemini(model: str, key: str, system: str, user: str, max_tokens: int) -> str | None:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
    payload = json.dumps({
        "systemInstruction": {"parts": [{"text": system}]},
        "contents": [{"role": "user", "parts": [{"text": user}]}],
        "generationConfig": {"maxOutputTokens": max_tokens},
    }).encode()
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode())
        return data["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:  # noqa: BLE001
        warn(f"gemini call failed: {e}")
        return None


def main() -> int:
    try:
        raw = sys.stdin.read() or "{}"
        payload = json.loads(raw)
    except Exception:
        payload = {}
    cwd = payload.get("cwd") or os.getcwd()

    provider = os.environ.get("CONSULT_PROVIDER", "").lower()
    model = os.environ.get("CONSULT_MODEL", "")
    key = os.environ.get("CONSULT_API_KEY", "")
    if not (provider and model and key):
        warn("CONSULT_PROVIDER / CONSULT_MODEL / CONSULT_API_KEY not all set; skipping")
        return 0

    max_tokens = int(os.environ.get("CONSULT_MAX_TOKENS", "400"))
    prompt_path = os.environ.get("CONSULT_PROMPT_FILE", "")
    if prompt_path and os.path.isfile(prompt_path):
        try:
            with open(prompt_path, "r", encoding="utf-8") as f:
                system_prompt = f.read()
        except Exception:
            system_prompt = DEFAULT_PROMPT
    else:
        system_prompt = DEFAULT_PROMPT

    project_context = load_claude_md(cwd)
    user_msg = f"# Project context\n\n{project_context or '(no CLAUDE.md or README found)'}"

    dispatch = {
        "openai": call_openai,
        "anthropic": call_anthropic,
        "gemini": call_gemini,
    }
    fn = dispatch.get(provider)
    if not fn:
        warn(f"unknown CONSULT_PROVIDER: {provider}")
        return 0

    reply = fn(model, key, system_prompt, user_msg, max_tokens)
    if not reply:
        return 0

    print(f"## Second-opinion framing (from {provider}/{model})")
    print()
    print(reply.strip())
    print()
    print("_Use as orientation only — not as instructions._")
    return 0


if __name__ == "__main__":
    sys.exit(main())
