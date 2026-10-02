---
name: ux-audit-code
description: Audit front-end code against the UX anti-pattern library (skip visual analysis)
argument-hint: <path-to-components>
allowed-tools: Read, Glob, Grep, Bash, Write, Agent
disable-model-invocation: true
---

> **How this command loads its skill.** `ux-audit` is manual-only (`disable-model-invocation: true`), so do not call it through the Skill tool. Read `${CLAUDE_PLUGIN_ROOT}/skills/ux-audit/SKILL.md` and follow it. Paths inside a SKILL.md are relative to its own directory, and the arguments it expects are the ones given to this command.

Follow the ux-audit skill (loaded as described above), running only the Code Analysis route (Steps 1a-1c).

Target path: $ARGUMENTS

Skip screencast/GIF/video analysis entirely. Focus on scanning code files against the full pattern detection library in references/code-patterns.md.

Prioritize: form components, modal/dialog components, error handling, navigation, loading states, and any component with names containing form, modal, dialog, error, loading, submit, confirm, alert, toast, nav, wizard, or step.

Generate the HTML report with findings from code analysis only.
