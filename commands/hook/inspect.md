---
name: "hook:inspect"
description: "Audit existing Claude Code SessionStart / SessionEnd / Stop hooks. Reports configured hooks, missing timeouts, broken script references, and inline secret risks."
argument-hint: ""
allowed-tools: Skill(session-hooks), Read, Glob, Grep, Bash
---

# Hook Inspect

Read the current `.claude/settings.json` and `.claude/settings.local.json` files and print a human-readable table of every SessionStart / SessionEnd / Stop hook configured.

## Process

Invoke the `session-hooks` skill with `mode: inspect`.

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
