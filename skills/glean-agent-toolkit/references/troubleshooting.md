# Glean Agent Toolkit — Troubleshooting

Operational pitfalls and fix recipes. SDK-internals questions belong with the upstream `glean-agent-toolkit-guide` skill.

> Verified against `glean-agent-toolkit` v0.5.0.

---

## Environment

### `ValidationError: GLEAN_API_TOKEN must be set`

The toolkit validates env vars at first client construction. Set in `.env`:

```dotenv
GLEAN_API_TOKEN=glean_pat_…
GLEAN_SERVER_URL=https://your-company-be.glean.com
```

Then export before running (or use `python-dotenv` / `direnv`):

```bash
set -a; source .env; set +a
```

### `GLEAN_INSTANCE` vs `GLEAN_SERVER_URL`

`GLEAN_SERVER_URL` is the canonical full URL (`https://your-company-be.glean.com`). `GLEAN_INSTANCE` is a legacy fallback (just the company slug, e.g. `your-company`). Prefer `GLEAN_SERVER_URL`. If both are set, `GLEAN_SERVER_URL` wins.

### Retry tuning

If you see frequent transient timeouts, the toolkit honors:
- `GLEAN_RETRY_INITIAL` (default `1.0` seconds)
- `GLEAN_RETRY_MAX` (default `50.0`)
- `GLEAN_RETRY_MULTIPLIER` (default `1.1`)
- `GLEAN_RETRY_MAX_ELAPSED` (default `60.0`)

---

## Install / Import

### `ModuleNotFoundError: No module named 'agents'`

You imported the OpenAI Agents SDK but installed the base toolkit. Fix:

```bash
pip install "glean-agent-toolkit[openai]"
```

Same pattern for the other frameworks: `[langchain]`, `[adk]`, `[crewai]`, or `[all]`.

### `ModuleNotFoundError: No module named 'glean-agent-toolkit'`

Pip name vs import name confusion. The pip package is `glean-agent-toolkit` (hyphens); the Python import path is `glean.agent_toolkit` (dot + underscore):

```python
# wrong
import glean_agent_toolkit
from glean-agent-toolkit import tool_spec

# right
from glean.agent_toolkit.decorators import tool_spec
from glean.agent_toolkit.context import GleanContext
from glean.agent_toolkit.tools import search
```

### Importing built-in tools

```python
from glean.agent_toolkit.tools import (
    search,
    glean_chat,
    read_document,
    employee_search,
    calendar_search,
    code_search,
    gmail_search,
    outlook_search,
    web_search,
)
```

---

## Tool authoring

### LLM keeps trying to pass `ctx`

Your `GleanContext` parameter is exposed in the JSON schema. Fix the signature:

```python
# wrong — ctx becomes a required JSON-schema field
def my_tool(ctx: GleanContext, *, query: str) -> ToolResult: ...

# right — decorator auto-excludes ctx when it's optional with None default
def my_tool(ctx: GleanContext | None = None, *, query: str) -> ToolResult: ...
```

The `GleanContext` parameter must be **first**, **optional** with `None` default, and named exactly `ctx` for the decorator's `_is_context_param()` check to fire.

### Tool returns empty results

For built-in tools: the relevant Glean connector may not be enabled for your instance. `gmail_search` requires a Gmail connector; `outlook_search` requires Microsoft 365; `calendar_search` needs Google Calendar or M365 Calendar. Check with your Glean admin.

For custom tools: verify the underlying API call returns data when invoked directly outside the agent loop.

### Schema validation error on tool input

`@tool_spec` generates the schema from your type hints via Pydantic v2. Common issues:
- A non-JSON-serializable type (e.g. raw `datetime` without serializer config).
- Missing `Annotated[Type, Field(description=...)]` — the LLM gets no guidance on how to fill the field.
- A `Union` type the LLM can't disambiguate.

Fix: use Pydantic `BaseModel` for complex inputs, and always add `Field(description=...)` for primitive params.

### Async tool hangs under load

The decorator wraps sync functions in a `ThreadPoolExecutor` with `max_workers=10`. CPU-heavy tools called concurrently will queue. Either:
- Make the tool natively async, or
- Run the agent with lower concurrency, or
- Pre-process / cache outside the tool.

---

## Project structure

### `pyproject.toml` exists but isn't PEP 621

`/glean:init` only generates a PEP 621 `[project]` table. If your project uses Poetry (`[tool.poetry]`) or PDM, init aborts. Either:
- Migrate to PEP 621 (Poetry 2.0+ supports it), or
- Add the toolkit manually:
  ```bash
  poetry add "glean-agent-toolkit[openai]"   # Poetry
  pdm add "glean-agent-toolkit[openai]"      # PDM
  ```
  Then run `/glean:add-tool` and `/glean:add-adapter` against the project — those work regardless of build backend.

### `[all]` extra and doctor false-negatives

Doctor checks for each requested framework's importability. `[all]` installs all four — doctor treats `[all]` as satisfying any per-framework check.

### Monorepo

Pass `--dir apps/myagent` to `/glean:init`. The src layout will be created inside that dir.

---

## Quick recipes

| Symptom | Recipe |
|---------|--------|
| `GLEAN_API_TOKEN must be set` at startup | Populate `.env`, `set -a; source .env; set +a` |
| `import openai_agents` fails | `pip install "glean-agent-toolkit[openai]"` |
| LLM passes `ctx` and gets a 400 | Make `ctx` optional with `None` default |
| Tool returns `[]` consistently | Verify connector enabled in Glean admin |
| 401 on every request | Wrong `GLEAN_SERVER_URL` host (use `*-be.glean.com`, not the public-facing UI URL) |
| Timeouts under load | Tune `GLEAN_RETRY_*` env vars; reduce concurrency |
| `@tool_spec` schema includes `ctx` | Signature wrong (see "LLM keeps trying to pass ctx") |
