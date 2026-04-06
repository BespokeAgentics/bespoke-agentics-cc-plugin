---
name: bespokeagentics:ux-audit-code
description: Audit front-end code against the UX anti-pattern library (skip visual analysis)
argument-hint: <path-to-components>
allowed-tools: Skill(ux-audit), Read, Glob, Grep, Bash, Write, Agent
---

Invoke the ux-audit skill, but ONLY run the Code Analysis route (Steps 1a-1c).

Target path: $ARGUMENTS

Skip screencast/GIF/video analysis entirely. Focus on scanning code files against the full pattern detection library in references/code-patterns.md.

Prioritize: form components, modal/dialog components, error handling, navigation, loading states, and any component with names containing form, modal, dialog, error, loading, submit, confirm, alert, toast, nav, wizard, or step.

Generate the HTML report with findings from code analysis only.
