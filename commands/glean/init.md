---
name: "glean:init"
description: "Bootstrap a new Glean agent project (Python) — interviews for framework choice, generates pyproject.toml, .env, agent file, and optional custom tool."
argument-hint: "[--dir <path>] [--framework openai|langchain|adk|all] [--force]"
allowed-tools: Skill(glean-agent-toolkit), AskUserQuestion, Bash, Read, Write, Edit, Glob, Grep
---

# Glean Init

Bootstrap a new Glean Agent Toolkit project.

## Arguments

Parse from `$ARGUMENTS`:

```
[--dir '<path>'] [--framework openai|langchain|adk|all] [--force]
```

- `--dir` — target directory (default `./`; ask if omitted and CWD is non-empty)
- `--framework` — `openai` | `langchain` | `adk` | `all` (ask if omitted)
- `--force` — allow scaffolding into a non-empty Python project (skip the abort check)

If `$ARGUMENTS` is empty, the skill runs the full 5-question interview.

## Process

Invoke the `glean-agent-toolkit` skill with `mode: init` and forward `$ARGUMENTS`.

The skill will:

1. **Phase 0** — Offer to install the upstream `glean-agent-toolkit-guide` and `glean-agent-toolkit-builder` Claude Code skills (one-time per machine).
2. **Phase 1** — Run the 5-question interview (skipping any answered via `$ARGUMENTS`).
3. **Phase 2** — Pre-flight: check Python ≥ 3.10, refuse non-empty Python project unless `--force`.
4. **Phase 3** — Generate `pyproject.toml`, `.env.example`, `.gitignore`, `README.md`, `src/<module>/__init__.py`, `src/<module>/agent_<framework>.py`, and (optionally) `src/<module>/tools/custom_tools.py` from templates.
5. **Phase 4** — Print a summary with the next-step commands (`pip install -e .`, `cp .env.example .env`, run command).

If a `wiki/` directory exists at the repo root, append a single-line entry to `wiki/_log.md`.

## Examples

```
/glean:init
/glean:init --framework openai
/glean:init --dir apps/knowledge-bot --framework all --force
```
