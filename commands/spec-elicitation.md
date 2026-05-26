---
name: bespokeagentics:spec-elicitation
model: opus
description: Interview-driven spec development that transforms vague ideas into battle-ready specifications through structured, exhaustive questioning. Use when starting any non-trivial feature to ensure complete understanding before writing code.
argument-hint: "[path/to/spec.md]"
allowed-tools: Skill(spec-elicitation), AskUserQuestion, Read, Write, Edit
---

Invoke the `spec-elicitation` skill with the user's arguments:

```
$ARGUMENTS
```

The argument is an optional path to the spec file to read or create (defaults to `spec.md`). The skill runs the full interview-driven workflow — exhaustive `AskUserQuestion` interview across every spec dimension, then writes the final structured spec to the file.

See `skills/spec-elicitation/SKILL.md` for the workflow and `references/` for interview dimensions, techniques, and the spec template.
