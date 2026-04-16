---
name: "glean:add-tool"
description: "Scaffold a new @tool_spec custom tool in tools/custom_tools.py with Pydantic schema and GleanContext boilerplate."
argument-hint: "<tool-name> [--description '<text>'] [--params name:type,name:type]"
allowed-tools: Skill(glean-agent-toolkit), AskUserQuestion, Read, Write, Edit, Grep, Glob
---

# Glean Add Tool

Append a new `@tool_spec` custom tool to the project's `tools/custom_tools.py`. Creates the file (with the import header) if missing.

## Arguments

Parse from `$ARGUMENTS`:

```
<tool-name> [--description '<text>'] [--params name:type,name:type]
```

- `<tool-name>` — required, snake_case (validated)
- `--description` — one-sentence description of what the tool does (asked via interview if omitted)
- `--params` — comma-separated typed params, e.g. `query:str,limit:int`. Supported types: `str`, `int`, `float`, `bool`, `list[str]`. Asked if omitted.

## Process

Invoke the `glean-agent-toolkit` skill with `mode: add-tool` and forward `$ARGUMENTS`.

The skill will:

1. Locate `custom_tools.py` (search `./tools/` and `./src/*/tools/`; prompt if multiple).
2. Create the file with the import header if missing.
3. Render the per-tool block from `templates/custom_tool.py.tmpl` with the user's `name`, `description`, and `params`.
4. Append the rendered block (preceded by a blank line).
5. Report the path and remind the user to bind the tool with `.as_<framework>_tool()` at the use site.

If a `wiki/` directory exists at the repo root, append a single-line entry to `wiki/_log.md`.

## Examples

```
/glean:add-tool get_weather --description "Fetch the current weather for a city" --params city:str
/glean:add-tool list_open_tickets --description "Pull open Jira tickets for a project" --params project_key:str,limit:int
/glean:add-tool summarize_team   # asks for description and params
```
