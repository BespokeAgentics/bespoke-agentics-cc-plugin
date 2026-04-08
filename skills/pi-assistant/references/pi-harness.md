# Pi Harness Reference

## Contents

- Modes and defaults
- Context and system prompt files
- Settings and scope
- Choosing the right customization surface
- Local audit checklist

## Modes and Defaults

- Pi runs in interactive mode, print or JSON mode, RPC mode, and SDK mode.
- The default model toolset is `read`, `write`, `edit`, and `bash`.
- `/reload` refreshes keybindings, extensions, skills, prompts, and context files without restarting the session.
- Startup surfaces loaded in the UI include AGENTS files, prompt templates, skills, and extensions.

## Context and System Prompt Files

Pi loads `AGENTS.md` or `CLAUDE.md` from:

- `~/.pi/agent/AGENTS.md`
- parent directories, walking up from the current working directory
- the current directory

All matching files are concatenated.

System prompt overrides:

- `.pi/SYSTEM.md` or `~/.pi/agent/SYSTEM.md`: replace the default system prompt
- `.pi/APPEND_SYSTEM.md` or `~/.pi/agent/APPEND_SYSTEM.md`: append to the default system prompt

Use these rules when choosing where behavior belongs:

- repo conventions or workflows: `AGENTS.md`
- replace default assistant behavior: `SYSTEM.md`
- layer extra global or project guidance: `APPEND_SYSTEM.md`

## Settings and Scope

Global Pi settings live at:

- `~/.pi/agent/settings.json`

Project-local settings live at:

- `.pi/settings.json`

Prefer project-local settings when:

- the behavior should be shared with a team
- the repo depends on specific packages or extensions
- the setup should bootstrap automatically on startup

Prefer global settings when:

- the behavior is purely personal
- the package is useful across many repos

## Choosing the Right Customization Surface

| Need | Best surface |
| --- | --- |
| Shared repo instructions | `AGENTS.md` or `CLAUDE.md` |
| Replace default assistant prompt | `SYSTEM.md` |
| Append extra assistant instructions | `APPEND_SYSTEM.md` |
| Reusable workflow | skill |
| Reusable prompt snippet | prompt template |
| New command, tool, hook, or UI | extension |
| Shareable bundle of resources | Pi package |

Prefer the smallest surface that solves the request cleanly.

## Local Audit Checklist

When reviewing a Pi setup, inspect these in order:

1. `AGENTS.md`, `CLAUDE.md`, `.pi/SYSTEM.md`, `.pi/APPEND_SYSTEM.md`
2. `.pi/settings.json`
3. `.pi/extensions/`
4. `.pi/skills/` and `.agents/skills/`
5. package manifests that declare Pi resources
6. installed package references in settings

Useful shell checks:

```bash
rg --files .pi .agents 2>/dev/null
rg -n '"packages"|"skills"|"extensions"|"prompts"|"themes"' .pi/settings.json package.json 2>/dev/null
```
