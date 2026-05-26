---
name: "hook:add-stop"
description: "Add a single Stop or SessionEnd hook to an existing Claude Code setup. Skips the broad interview and asks only what's needed for one hook."
argument-hint: "[--pattern wiki-log|session-page|diff|confluence|slack|notify|custom] [--scope project|local|user]"
allowed-tools: Skill(session-hooks), AskUserQuestion, Bash, Read, Write, Edit, Glob, Grep
---

# Hook Add — Stop / SessionEnd

Add a single Stop or SessionEnd hook without re-running the full design interview.

## Arguments

```
[--pattern <name>] [--scope project|local|user]
```

- `--pattern` — one of: wiki-log, session-page, diff, confluence, slack, notify, custom
- `--scope` — where to write the hook config

## Process

Invoke the `session-hooks` skill with `mode: add-stop` and forward `$ARGUMENTS`.

The skill will:

1. Detect existing Stop / SessionEnd hooks to avoid duplicates.
2. Ask which pattern to add (skipping if `--pattern` was provided).
3. Ask about settings scope and idempotency strategy.
4. Scaffold the script under `.claude/hooks/` and append to `settings.json`.
5. If `wiki/` exists and the chosen pattern writes to it, append a `wiki/_log.md` row.

## Examples

```
/hook:add-stop --pattern wiki-log
/hook:add-stop --pattern session-page
/hook:add-stop --pattern slack --scope local
```
