---
name: "hook:add-stop"
description: "Add a single Stop or SessionEnd hook to an existing Claude Code setup. Skips the broad interview and asks only what's needed for one hook."
argument-hint: "[--pattern wiki-log|session-page|diff|confluence|slack|notify|custom] [--scope project|local|user]"
allowed-tools: AskUserQuestion, Bash, Read, Write, Edit, Glob, Grep
disable-model-invocation: true
---

> **How this command loads its skill.** `session-hooks` is manual-only (`disable-model-invocation: true`), so do not call it through the Skill tool. Read `${CLAUDE_PLUGIN_ROOT}/skills/session-hooks/SKILL.md` and follow it. Paths inside a SKILL.md are relative to its own directory, and the arguments it expects are the ones given to this command.

# Hook Add — Stop / SessionEnd

Add a single Stop or SessionEnd hook without re-running the full design interview.

## Arguments

```
[--pattern <name>] [--scope project|local|user]
```

- `--pattern` — one of: wiki-log, session-page, diff, confluence, slack, notify, custom
- `--scope` — where to write the hook config

## Process

Follow the `session-hooks` skill (loaded as described above) with `mode: add-stop` and forward `$ARGUMENTS`.

The skill will:

1. Detect existing Stop / SessionEnd hooks to avoid duplicates.
2. Ask which pattern to add (skipping if `--pattern` was provided).
3. Ask about settings scope, script language, and failure mode.
4. Scaffold the script under `.claude/hooks/` and append to `settings.json`.
5. If `wiki/` exists and the chosen pattern writes to it, append a `wiki/_log.md` entry (`## YYYY-MM-DD — <operation> — <summary>` plus a short body).

## Examples

```
/hook:add-stop --pattern wiki-log
/hook:add-stop --pattern session-page
/hook:add-stop --pattern slack --scope local
```
