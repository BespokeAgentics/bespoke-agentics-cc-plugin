---
name: "hook:design"
description: "Interview-driven designer for Claude Code SessionStart / SessionEnd / Stop hooks. Produces both a design doc and the working settings.json + executable scripts."
argument-hint: "[--scope project|local|user] [--language bash|python|both]"
allowed-tools: Skill(session-hooks), AskUserQuestion, Bash, Read, Write, Edit, Glob, Grep
---

# Hook Design

Design start and stop hooks for Claude Code through a structured interview.

## Arguments

Parse from `$ARGUMENTS`:

```
[--scope project|local|user] [--language bash|python|both]
```

- `--scope` — where to write the hook config (default: ask via interview)
- `--language` — script language preference (default: ask via interview)

If `$ARGUMENTS` is empty, the skill runs the full interview from scratch.

## Process

Invoke the `session-hooks` skill with `mode: design` and forward `$ARGUMENTS`.

The skill will:

1. **Phase 0** — Silently scan the repo to discover which integrations are plausible (wiki, Atlassian MCP, git, GitHub MCP, etc.).
2. **Phase 1** — Run a 6-question interview, presenting only options the repo can actually support.
3. **Phase 2** — Confirm the proposed plan with the user before writing anything.
4. **Phase 3** — Generate executable hook scripts in `.claude/hooks/`, merge into `settings.json`, and write `docs/session-hooks-design.md`.
5. **Phase 4** — If `wiki/` exists, append a `wiki/_log.md` entry.
6. **Phase 5** — Print a summary with file paths, required env vars, and a one-line test command.

## Examples

```
/hook:design
/hook:design --scope local
/hook:design --scope project --language python
```

## Related

- `/hook:add-start` — add a single SessionStart hook to an existing setup
- `/hook:add-stop` — add a single Stop hook to an existing setup
- `/hook:inspect` — audit existing hooks
