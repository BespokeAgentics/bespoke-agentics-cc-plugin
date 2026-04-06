---
name: bespokeagentics:ux-audit-quick
description: Spot-check a single component or screen against top-priority UX heuristics — no full report
argument-hint: <component-path-or-screenshot>
allowed-tools: Skill(ux-audit), Read, Glob, Grep, Bash
---

Invoke the ux-audit skill for a quick spot-check.

Target: $ARGUMENTS

This is a lightweight check, NOT a full audit. Do the following:

1. Read the target file or view the target image
2. Check against the top-priority patterns only:
   - P3.2 — Destructive action without confirmation (Critical)
   - P6.1 — Form clears on validation error (Critical)
   - P9.2 — Error dismissal clears form (Critical)
   - P1.1 — Button with no loading state (High)
   - P1.3 — Missing success/error feedback after mutation (High)
   - P2.3 — Icon-only buttons without labels (High)
   - P5.1 — Validation only on submit (High)
   - P9.1 — Generic catch-all error message (High)
3. Report findings as a concise markdown list directly in the conversation — do NOT generate an HTML report
4. For each finding, include: severity, heuristic, one-line description, file:line, and the fix

Keep it fast. This is for iterating on a single component, not auditing a whole product.
