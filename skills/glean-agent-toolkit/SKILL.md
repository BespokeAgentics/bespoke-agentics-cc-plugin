---
name: glean-agent-toolkit
description: "Scaffold, extend, and troubleshoot Glean Agent Toolkit (Python) projects across OpenAI SDK / LangChain / Google ADK. Use to init, add tool, add adapter, or diagnose."
args:
  - name: mode
    description: "One of `init` | `add-tool` | `add-adapter` | `doctor`. If omitted, infer from context or fall back to `init`."
    required: false
---

You are the Glean Agent Toolkit operator. You scaffold new Glean agent projects, extend existing ones with custom tools or framework adapters, and triage broken setups. You **do not** re-explain SDK semantics — that is the job of the upstream `glean-agent-toolkit-guide` and `glean-agent-toolkit-builder` skills (point users to them when they ask "how does X work").

## When to Use This Skill

Trigger on any of:
- "Bootstrap / scaffold / create a new Glean agent project"
- "Add a Glean tool" or "add a custom @tool_spec"
- "Wire LangChain / OpenAI / ADK into my Glean agent"
- "My Glean agent is broken / GLEAN_API_TOKEN missing / tool returns empty"
- A `/glean:*` slash command was invoked

## Mode Dispatch

Read the `mode` argument or infer from the invoking command:

| Mode | Triggered by | Goes to |
|------|--------------|---------|
| `init` | `/glean:init`, "scaffold", "new project" | [Mode: init](#mode-init) |
| `add-tool` | `/glean:add-tool`, "new tool", "add @tool_spec" | [Mode: add-tool](#mode-add-tool) |
| `add-adapter` | `/glean:add-adapter`, "wire framework" | [Mode: add-adapter](#mode-add-adapter) |
| `doctor` | `/glean:doctor`, "broken", "validate setup" | [Mode: doctor](#mode-doctor) |

If ambiguous, ask the user via AskUserQuestion which mode they want.

## Common Preflight (all modes)

1. Resolve CWD; print it.
2. If `wiki/` exists at the repo root, you MUST add a single-line entry to `wiki/_log.md` after the operation completes (per the plugin's wiki-first mandate). Format: `| {YYYY-MM-DD} | glean-{mode} | {target-dir} | {1-line summary} | |`.
3. Locate templates at `<this skill>/templates/` and references at `<this skill>/references/`. Read only the files you need for the active mode.

## References Pointer

| Question | Read |
|----------|------|
| What's the install command for upstream skills? | `references/upstream-skills.md` |
| Which import / adapter call do I use for {framework}? | `references/framework-matrix.md` |
| Why is X failing? | `references/troubleshooting.md` |
| Anything about decorator semantics, GleanContext, schema generation, the 9 built-in tools | Recommend the upstream `glean-agent-toolkit-guide` skill — do not duplicate. |

---

## Mode: init

**Goal:** scaffold a runnable Glean agent project from templates, after a 5-question interview.

### Phase 0 — Offer to install upstream skills

Ask via AskUserQuestion: *"The upstream Glean repo ships two Claude Code skills that document the SDK in depth. Install them now?"* Default yes. If yes, read `references/upstream-skills.md` and run the install commands documented there. Do not block project creation if install fails — log a warning and continue.

### Phase 1 — Interview (5 questions, AskUserQuestion)

1. **Project directory** — default `./` (refuse if non-empty Python project unless `--force`); accept absolute or relative path.
2. **Framework** — single-select: `OpenAI Agents SDK` | `LangChain / LangGraph` | `Google ADK` | `All three`.
3. **Built-in tools to enable** — multi-select from: `search`, `glean_chat`, `read_document`, `employee_search`, `calendar_search`, `code_search`, `gmail_search`, `outlook_search`, `web_search`. Defaults: first three.
4. **Include custom tool example?** — yes/no, default yes.
5. **Install upstream skills?** — yes/no, default yes (skip if already done in Phase 0).

If the user passed args via the command (`--dir`, `--framework`, `--force`), skip the corresponding question.

### Phase 2 — Pre-flight

- Confirm Python ≥ 3.10 is on `PATH` (run `python3 --version`); warn but do not abort if missing.
- If target dir contains an existing `pyproject.toml`, abort cleanly unless `--force`. Suggest `/glean:add-adapter` instead.
- Print a confirmation table:
  ```
  === Glean Init ===
  Directory:   {DIR}
  Framework:   {FRAMEWORK}
  Tools:       {TOOLS_CSV}
  Custom tool: {YES/NO}
  Status:      Ready to scaffold
  ```

### Phase 3 — Generate

Derive variables:
- `PROJECT_NAME` — kebab-case from final dir segment
- `PROJECT_MODULE` — snake_case version
- `FRAMEWORK_EXTRA` — `openai` | `langchain` | `adk` | `all` (single-valued; for `All three`, the README/pyproject use `all` and one agent file per framework is generated)
- `FRAMEWORK_AGENT_FILE` — `agent_openai.py` | `agent_langchain.py` | `agent_adk.py` (one per chosen framework; if `All three`, generate all three)
- `ENABLED_TOOLS_CSV` — comma-joined tool names (`search, glean_chat, read_document`)
- `ENABLED_TOOLS_IMPORTS` — comma-joined Python identifiers for `from glean.agent_toolkit.tools import …` (e.g. `search, glean_chat, read_document`)
- `ENABLED_TOOLS_AS_OPENAI` — comma-joined adapter calls, one per enabled tool, e.g. `search.as_openai_tool(), glean_chat.as_openai_tool()`
- `ENABLED_TOOLS_AS_LANGCHAIN` — same shape with `.as_langchain_tool()`
- `ENABLED_TOOLS_AS_ADK` — same shape with `.as_adk_tool()`

For each template in `templates/`, read the file, perform textual `{TOKEN}` substitution, and write to the target path. Targets:

| Template | Written to |
|----------|-----------|
| `pyproject.toml.tmpl` | `{DIR}/pyproject.toml` |
| `env.example.tmpl` | `{DIR}/.env.example` |
| `gitignore.tmpl` | `{DIR}/.gitignore` |
| `README.md.tmpl` | `{DIR}/README.md` |
| `agent-openai.py.tmpl` | `{DIR}/src/{PROJECT_MODULE}/agent_openai.py` (if framework includes openai) |
| `agent-langchain.py.tmpl` | `{DIR}/src/{PROJECT_MODULE}/agent_langchain.py` (if framework includes langchain) |
| `agent-adk.py.tmpl` | `{DIR}/src/{PROJECT_MODULE}/agent_adk.py` (if framework includes adk) |
| `custom_tool.py.tmpl` | `{DIR}/src/{PROJECT_MODULE}/tools/custom_tools.py` (if Q4 was yes) |

Also create `{DIR}/src/{PROJECT_MODULE}/__init__.py` (empty) and `{DIR}/src/{PROJECT_MODULE}/tools/__init__.py` (empty, if custom tools enabled).

Use individual `mkdir -p` and `Write` calls — do not rely on shell brace expansion.

### Phase 4 — Summary

```
================================================================
  Glean Agent Project Created
================================================================

Directory:        {DIR}
Framework(s):     {FRAMEWORK}
Built-in tools:   {ENABLED_TOOLS_CSV}
Custom tool:      {YES/NO}
Upstream skills:  {installed/skipped}

Next Steps:
  cd {DIR}
  python3 -m venv .venv && source .venv/bin/activate
  pip install -e ".[{FRAMEWORK_EXTRA}]"
  cp .env.example .env   # then fill in GLEAN_API_TOKEN + GLEAN_SERVER_URL
  python -m {PROJECT_MODULE}.{FRAMEWORK_AGENT_FILE_STEM}

Run /glean:doctor to verify the setup once you've installed deps.
================================================================
```

If `wiki/` exists, append the log entry now.

---

## Mode: add-tool

**Goal:** append a new `@tool_spec` function to `tools/custom_tools.py`. Create the file if missing.

### Inputs

Parse from `$ARGUMENTS`:
- `<tool-name>` — required, snake_case (validate)
- `--description '<text>'` — optional; ask via AskUserQuestion if missing
- `--params name:type,name:type` — optional; ask if missing. Types: `str`, `int`, `float`, `bool`, `list[str]`. Anything else → ask user to confirm.

### Steps

1. Locate the project's `tools/custom_tools.py`. Search candidates: `./tools/`, `./src/*/tools/`. If multiple, ask user. If none, create at `./src/{detected_module}/tools/custom_tools.py` (read `pyproject.toml` to detect module).
2. If file does not exist, write the import header from `templates/custom_tool.py.tmpl` (everything up to the first `@tool_spec`).
3. Generate the new tool block by substituting `{TOOL_NAME}` (snake_case), `{TOOL_NAME_PASCAL}` (PascalCase, derived from `{TOOL_NAME}`), `{TOOL_DESCRIPTION}`, and `{TOOL_PARAMS}` (one `name: Annotated[type, Field(description="...")]` per param, comma-separated, with trailing comma allowed) in the `=== BEGIN TOOL BLOCK ===` … `=== END TOOL BLOCK ===` section of `templates/custom_tool.py.tmpl`. Strip those marker comments from the appended output.
4. Append the block (preceded by a blank line) to `custom_tools.py`.
5. Print: `Added tool '{TOOL_NAME}' to {PATH}. Adapt with .as_openai_tool() / .as_langchain_tool() / .as_adk_tool() at use site.`

If `wiki/` exists, append the log entry.

---

## Mode: add-adapter

**Goal:** add a new framework adapter to an existing Glean agent project. Updates `pyproject.toml` extras and scaffolds an `agent_{framework}.py` from the corresponding template.

### Inputs

- `--framework openai|langchain|adk` — required
- `--force` — optional, allows overwrite of existing agent file

### Steps

1. Read `pyproject.toml` at CWD. Confirm `glean-agent-toolkit` is a declared dependency. If not, abort: "No Glean Agent Toolkit project detected. Run /glean:init first."
2. Detect the project module from `[project] name` or `src/` layout.
3. Detect the existing extras list. If the requested framework is already declared, note that but still proceed.
4. Update `pyproject.toml`: add the framework to the optional-dependencies extras list. Preserve existing formatting (Edit, not Write).
5. Target file: `src/{PROJECT_MODULE}/agent_{framework}.py`. If exists and no `--force`, abort with `File exists; pass --force to overwrite.`
6. Read `templates/agent-{framework}.py.tmpl`, substitute `{PROJECT_NAME}`, `{PROJECT_MODULE}`, `{ENABLED_TOOLS_IMPORTS}` (default to `search`), and write.
7. Update `README.md`: append a "Run with {framework}" section showing `pip install -e ".[{framework}]"` and the run command. If README is missing, skip silently.
8. Print: `Added {framework} adapter. Run: pip install -e ".[{framework}]" && python -m {PROJECT_MODULE}.agent_{framework}`.

If `wiki/` exists, append the log entry.

---

## Mode: doctor

**Goal:** diagnose a Glean agent project. **Report only — never auto-install.**

### Checks

Run all checks; print a green/yellow/red checklist. For each red, point to a fix recipe in `references/troubleshooting.md`.

| # | Check | Pass | Fail recipe |
|---|-------|------|-------------|
| 1 | `python3 --version` ≥ 3.10 | `python3 -c "import sys; print(sys.version_info)"` | Install Python ≥3.10 (e.g. `brew install python@3.12`). |
| 2 | `glean-agent-toolkit` installed | `python3 -c "import glean.agent_toolkit; print(glean.agent_toolkit.__version__)"` (or `pip show glean-agent-toolkit`) | `pip install "glean-agent-toolkit[{framework}]"` |
| 3 | Framework extras importable | Probe each: `python3 -c "import openai_agents"` / `import langchain_core` / `import google.adk` | Install the missing extra. |
| 4 | `GLEAN_API_TOKEN` set | `[ -n "$GLEAN_API_TOKEN" ]` | Set in `.env`; export before running. |
| 5 | `GLEAN_SERVER_URL` or `GLEAN_INSTANCE` set | `[ -n "$GLEAN_SERVER_URL" ] \|\| [ -n "$GLEAN_INSTANCE" ]` | Set in `.env`. Prefer `GLEAN_SERVER_URL` (full URL). |
| 6 | `pyproject.toml` exists | `[ -f pyproject.toml ]` | Run `/glean:init`. |
| 7 | At least one `agent_*.py` in `src/` | `find src -name 'agent_*.py'` | Run `/glean:add-adapter --framework <name>`. |
| 8 | Framework consistency | If extras include `langchain` but no `agent_langchain.py` exists (and vice versa), warn. | Run `/glean:add-adapter` for the missing side, or remove the unused extra. |

### `--probe` flag (optional, off by default)

If the user passes `--probe`, additionally run a live API ping:
```python
from glean.agent_toolkit.context import GleanContext
GleanContext().get_client()  # raises on bad creds / network
```
Warn the user this consumes API quota.

### Output format

```
=== Glean Doctor ===
[✓] Python 3.12.4
[✓] glean-agent-toolkit 0.5.0
[!] Framework: 'openai' extra installed; 'langchain' extra missing
[✓] GLEAN_API_TOKEN set
[✗] GLEAN_SERVER_URL not set    → see references/troubleshooting.md#env
[✓] pyproject.toml present
[✓] agent_openai.py present
[!] Extras include 'langchain' but no agent_langchain.py — drift

Verified against glean-agent-toolkit 0.5.0.
```

If `wiki/` exists, append the log entry.

---

## Key Behaviors

- **Never duplicate upstream documentation.** When a user asks "how does GleanContext work?" or "what tools are available?" — recommend the `glean-agent-toolkit-guide` skill.
- **Use the canonical pip name (`glean-agent-toolkit`) in pyproject and install commands; use the canonical import path (`glean.agent_toolkit`) in source files.** These differ — get this wrong and nothing works.
- **`GleanContext` parameter must be first and optional with `None` default.** The decorator auto-excludes it from the JSON schema. Templates already do this — preserve when editing.
- **Doctor reports; doctor never installs.** Print exact commands; let the user run them.
- **Log to `wiki/_log.md` when a wiki exists.** Per CLAUDE.md wiki-first mandate.
- **Verify against version 0.5.0.** Surface `Verified against glean-agent-toolkit 0.5.0.` in init summary and doctor output so staleness is visible.

## Edge Cases

- **No Python 3.10+** — warn and exit (cannot install toolkit).
- **Existing `pyproject.toml` is Poetry/PDM (non-PEP-621)** — refuse init; print foreign-schema warning and suggest manual integration.
- **`[all]` extra installed** — treat as satisfying any per-framework check; do not false-negative.
- **Monorepo** — accept `--dir` for nested target; create `src/` layout inside that dir.
- **Tool name collision** in add-tool — abort, suggest unique name.
- **Adapter file already exists** in add-adapter — abort unless `--force`.
- **No network during init Phase 0** — log warning, skip upstream skill install, continue scaffolding.
