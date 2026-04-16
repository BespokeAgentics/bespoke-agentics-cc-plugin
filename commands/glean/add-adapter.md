---
name: "glean:add-adapter"
description: "Wire an additional framework adapter (OpenAI / LangChain / ADK) into an existing Glean agent project — updates pyproject.toml extras and scaffolds an agent file."
argument-hint: "--framework openai|langchain|adk [--force]"
allowed-tools: Skill(glean-agent-toolkit), AskUserQuestion, Read, Write, Edit, Bash, Glob
---

# Glean Add Adapter

Add a new framework adapter (OpenAI Agents SDK, LangChain/LangGraph, or Google ADK) to an existing Glean agent project. Updates the `pyproject.toml` extras and scaffolds an `agent_<framework>.py` file from the matching template.

## Arguments

Parse from `$ARGUMENTS`:

```
--framework openai|langchain|adk [--force]
```

- `--framework` — required (asked via interview if omitted)
- `--force` — allow overwriting an existing `agent_<framework>.py`

## Process

Invoke the `glean-agent-toolkit` skill with `mode: add-adapter` and forward `$ARGUMENTS`.

The skill will:

1. Confirm CWD is a Glean Agent Toolkit project (reads `pyproject.toml`; aborts if `glean-agent-toolkit` is not declared).
2. Detect the project module (from `[project] name` or `src/` layout).
3. Add the requested framework to the optional-dependencies extras list (in-place edit, preserving formatting).
4. Generate `src/<module>/agent_<framework>.py` from the matching template (refuses overwrite without `--force`).
5. Append a "Run with <framework>" section to `README.md` if present.
6. Print install + run commands.

If a `wiki/` directory exists at the repo root, append a single-line entry to `wiki/_log.md`.

## Examples

```
/glean:add-adapter --framework langchain
/glean:add-adapter --framework adk --force
```
