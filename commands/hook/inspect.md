---
name: "hook:inspect"
description: "Audit existing Claude Code SessionStart / SessionEnd / Stop hooks. Reports configured hooks, missing timeouts, broken script references, and inline secret risks."
argument-hint: ""
allowed-tools: Read, Glob, Grep, Bash
disable-model-invocation: true
---

> **How this command loads its skill.** `session-hooks` is manual-only (`disable-model-invocation: true`), so do not call it through the Skill tool. Read `${CLAUDE_PLUGIN_ROOT}/skills/session-hooks/SKILL.md` and follow it. Paths inside a SKILL.md are relative to its own directory, and the arguments it expects are the ones given to this command.

# Hook Inspect

Read the current `.claude/settings.json` and `.claude/settings.local.json` files and print a human-readable table of every SessionStart / SessionEnd / Stop hook configured.

## Process

Follow the `session-hooks` skill (loaded as described above) with `mode: inspect`.

The skill will:

1. Read both project and local settings files.
2. Resolve each hook command and check that the script exists.
3. Print a table: event, matcher, command, timeout, status.
4. Surface recommendations:
   - Hooks with no timeout set
   - Hooks referencing scripts that no longer exist
   - Hooks with inline secrets (recommend moving to env vars)
   - Duplicate hooks across events

Inspect mode is read-only — it never modifies your config.

## Example

```
/hook:inspect
```
