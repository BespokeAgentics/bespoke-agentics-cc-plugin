---
name: "hook:add-start"
description: "Add a single SessionStart hook to an existing Claude Code setup. Skips the broad interview and asks only what's needed for one hook."
argument-hint: "[--pattern wiki|confluence|git|todo|ai-consult|comment-inbox|custom] [--scope project|local|user]"
allowed-tools: AskUserQuestion, Bash, Read, Write, Edit, Glob, Grep
disable-model-invocation: true
---

> **How this command loads its skill.** `session-hooks` is manual-only (`disable-model-invocation: true`), so do not call it through the Skill tool. Read `${CLAUDE_PLUGIN_ROOT}/skills/session-hooks/SKILL.md` and follow it. Paths inside a SKILL.md are relative to its own directory, and the arguments it expects are the ones given to this command.

# Hook Add — SessionStart

Add a single SessionStart hook without re-running the full design interview.

## Arguments

```
[--pattern <name>] [--scope project|local|user]
```

- `--pattern` — one of the named patterns from the catalog (wiki, confluence, git, todo, ai-consult, comment-inbox, custom)
- `--scope` — where to write the hook config

## Process

Follow the `session-hooks` skill (loaded as described above) with `mode: add-start` and forward `$ARGUMENTS`.

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
