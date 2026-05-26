---
name: "hook:add-start"
description: "Add a single SessionStart hook to an existing Claude Code setup. Skips the broad interview and asks only what's needed for one hook."
argument-hint: "[--pattern wiki|confluence|git|todo|ai-consult|comment-inbox|custom] [--scope project|local|user]"
allowed-tools: Skill(session-hooks), AskUserQuestion, Bash, Read, Write, Edit, Glob, Grep
---

# Hook Add — SessionStart

Add a single SessionStart hook without re-running the full design interview.

## Arguments

```
[--pattern <name>] [--scope project|local|user]
```

- `--pattern` — one of the named patterns from the catalog (wiki, confluence, git, todo, ai-consult, comment-inbox, custom)
- `--scope` — where to write the hook config

## Process

Invoke the `session-hooks` skill with `mode: add-start` and forward `$ARGUMENTS`.

The skill will:

1. Detect existing hooks in `settings.json` to avoid duplicates.
2. Ask which pattern to add (skipping if `--pattern` was provided).
3. Ask about settings scope, language, and failure mode.
4. Scaffold the script under `.claude/hooks/` and append to `settings.json`.

## Examples

```
/hook:add-start --pattern wiki
/hook:add-start --pattern confluence --scope local
/hook:add-start --pattern custom
```
