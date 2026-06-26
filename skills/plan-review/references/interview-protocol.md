# Phase 3 — Interview (validate & prioritize)

Goal: a review the author trusts. The model's findings are *suspicions*; the author knows their intent
and constraints. This round converts suspicions into a validated, prioritized set — confirming which
gaps are real, which are deliberately out of scope, and what actually blocks the build. It runs
**after** analysis so every question is concrete and grounded, never "what do you want?".

The interview is mandatory but proportional: a clean review with two minor nits needs one short
confirmation, not an interrogation. Scale the number of `AskUserQuestion` batches to the findings.

## Before asking — print the digest

Show the user what was found, so the questions have context. Keep it scannable:

```
Plan Review — {artifact filename}  ({type}, depth={depth})
Provisional readiness: {🟢/🟡/🔴}

Grounding: {N} anchors grounded, {N} claims contradicted, {N} unresolved
Findings: {B} blocker · {M} major · {m} minor

Blockers:
  F1 🔴 {title}  — {artifact quote} vs {file:line}
  F2 🔴 {title}  — …
Majors:
  F3 🟡 {title} …
(minor items will be listed in the report)
```

## The batches

Use `AskUserQuestion`. Group related findings; don't fire one question per finding when a multiSelect
covers several. Recommended flow:

**Batch 1 — Validate the blockers & majors (one question each, or a multiSelect to confirm several).**
For each high-severity finding, the real question is "is this a real problem you want addressed, or is
it intentional / out of scope?". Make the options concrete:

> Header: `F1 auth scope`
> Question: "The plan updates `mw.ts` but there's a second auth chain at `edge/auth.ts:12` the plan
> doesn't mention. Requests on `/edge/*` would bypass the fix. How should the plan treat it?"
> Options: `Add a task to also update edge/auth.ts` (recommended) · `Out of scope — /edge/* is
> deprecated` · `Already handled elsewhere` · (Other)

This is also your false-positive filter: if the user says "already handled" or "out of scope", the
finding leaves the report (or moves to a "considered & dismissed" note) instead of overstating risk.

**Batch 2 — Resolve blocking ambiguities.** For each ambiguity that genuinely changes the build (not
every vague word — the ones where two readings produce different code), ask which reading is intended.
These answers are the highest-value output: they become resolved decisions in the report, not just
flagged gaps.

**Batch 3 — Priority & scope (one multiSelect).** When several real findings remain, ask which are P0
(must fix before building) vs. P1 (fix during) vs. P2 (nice-to-have / defer). Pre-fill the model's
recommendation as the first option so the user can accept-as-is fast.

## Calibration rules

- If `--depth quick` or the findings are all minor, collapse to a single confirmation batch ("these
  three minor items — worth noting in the review, or skip?") and move on.
- Never ask the user to re-supply information that's already in the artifact or grounding map. Ground
  every question in a specific finding + its evidence.
- Respect dismissals. A finding the user calls out-of-scope is **not** a gap — record the user's
  reason and demote it. Overriding the author's stated intent is how a review loses trust.
- If the user doesn't engage (skips/declines), don't block: fall back to the model's own ranking, mark
  findings `UNVALIDATED` in the report, and say so plainly.

## Output — `interview-answers.md`

Record every decision to `{ANALYSIS_DIR}/interview-answers.md`:

```markdown
# Interview Answers — {artifact filename}

## Validated findings
- F1 — CONFIRMED, P0. User: "good catch, add the edge task."
- F4 — DISMISSED. User: "out of scope, /edge/* is deprecated." → move to 'considered & dismissed'.

## Resolved ambiguities
- "improve the loading state" → user means: add a skeleton + a 5s timeout message. (was F6)

## Priority
- P0: F1, F2   ·   P1: F3, F5   ·   P2 / defer: F7
```

This file is the source of truth for Phase 4 — the report reflects these decisions, not the raw
Phase 2 findings.
