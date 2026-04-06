---
description: Accessibility-focused audit checking ARIA roles, labels, keyboard navigation, and color usage
argument-hint: <path-to-components>
allowed-tools: Skill(ux-audit), Read, Glob, Grep, Bash, Write, Agent
---

Invoke the ux-audit skill with a focus on accessibility patterns.

Target path: $ARGUMENTS

Run code analysis but prioritize the accessibility cross-heuristic patterns:

- PA.1 — Missing ARIA roles on custom interactive components (div/span onClick without role="button", tabIndex, keyboard handlers)
- PA.2 — Form inputs missing associated labels (no htmlFor, aria-label, or aria-labelledby)
- PA.3 — Color as only differentiator (error states, required fields, status using only color)

Also check these accessibility-adjacent patterns:
- P2.3 — Icon-only buttons without accessible labels (H2, H7)
- P7.1 — No keyboard shortcuts for frequent actions (H7)
- P3.3 — Modal with no escape/cancel (H3) — check for Escape key handler

Scan ALL component files in the target path, not just priority-named ones.

Generate the HTML report with accessibility findings. Tag each finding with the relevant WCAG success criterion where applicable (e.g., 1.1.1 Non-text Content, 1.3.1 Info and Relationships, 2.1.1 Keyboard, 4.1.2 Name Role Value).
