---
title: Session Hooks Design
date: {{TODAY}}
generated_by: session-hooks skill
related: []
---

# Session Hooks Design — {{PROJECT_NAME}}

This document explains the SessionStart and Stop/SessionEnd hooks configured
for this project, why each one exists, and how to maintain them.

## Why hooks at all

> **Pain solved:** {{PAIN_POINT}}

The hooks below address that pain. They run automatically — no user action
required — and inject context (start) or capture state (end) on every
Claude Code session in this repo.

## SessionStart hooks

Each of these fires when a session **begins** (fresh, resume, or after `/clear`).
Output is injected as `additionalContext` in Claude's preamble.

{{START_HOOK_BLOCKS}}

## Stop / SessionEnd hooks

Each of these fires when a session **ends** (or, for Stop, when Claude
finishes a turn). Output is **not** injected — these are pure side-effects.

{{STOP_HOOK_BLOCKS}}

## Config location

| Setting | Value |
|---------|-------|
| Settings file | `{{SETTINGS_PATH}}` |
| Scope | {{SETTINGS_SCOPE}} |
| Script directory | `.claude/hooks/` |
| Failure mode | {{FAILURE_MODE}} |

## Required environment variables

The following env vars must be set in your shell (or via `direnv` / `.envrc`):

{{ENV_VARS_TABLE}}

If any required var is missing, the corresponding hook will warn to stderr
and skip — it will **not** block the session from starting.

## Testing each hook

Run any hook in isolation by piping a mock input JSON:

```bash
echo '{"session_id":"test","cwd":"'"$PWD"'","hook_event_name":"SessionStart","source":"startup"}' \
  | .claude/hooks/start-{slug}.sh
```

Expected behavior:
- Exit code 0
- stdout contains the context block you'd expect to see in the session preamble
- stderr is empty (happy path) or contains a one-line warning (degraded path)

## Disabling a hook

To temporarily disable, comment out the relevant block in `{{SETTINGS_PATH}}`.
To permanently remove, delete the block and the corresponding script in
`.claude/hooks/`.

## Updating

When the project's needs change, re-run the design flow:

```
/hook:design
```

The skill will detect existing hooks and offer to add, replace, or remove.

## Audit trail

Every hook run that produces a side-effect (writes to the wiki, posts to
Slack, updates Confluence) appends a row to `wiki/_log.md`. Review that
file to see what the hooks have done.
