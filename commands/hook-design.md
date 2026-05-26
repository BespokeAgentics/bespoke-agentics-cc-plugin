---
name: "hook-design"
description: "Alias for /hook:design — interview-driven designer for Claude Code SessionStart / SessionEnd / Stop hooks."
argument-hint: "[--scope project|local|user] [--language bash|python|both]"
allowed-tools: Skill(session-hooks), AskUserQuestion, Bash, Read, Write, Edit, Glob, Grep
---

# Hook Design (alias)

Flat-namespace alias for `/hook:design`. See `commands/hook/design.md` for full documentation.

Invoke the `session-hooks` skill with `mode: design` and forward `$ARGUMENTS`.
