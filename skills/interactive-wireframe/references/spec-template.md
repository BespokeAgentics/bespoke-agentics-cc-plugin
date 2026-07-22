# Spec template

Read before Phase 6. The spec is the durable artifact — the wireframe is
evidence, and the spec is what someone implements from six weeks later.

Two properties make it worth reading: **every claim about the codebase carries a
path**, and **every decision records how it was settled** (interview, or
validated on screen). Drop a section that genuinely does not apply; never pad one
with invention.

```markdown
# <Surface> — <the change, in one line>

> **Status:** Draft — spec only, not implemented · **Created:** <YYYY-MM-DD>
>
> <2–4 sentences: what changes and why. Note the interview size — "N rounds,
> M decisions" — and that a wireframe backs it.>

## Overview

### The problem
<What is wrong today, cited to real files. Symptoms a user would recognise,
not architecture-speak.>

### The shape of the change
<The new structure. A table of regions/bands/zones with dimensions, or a small
ASCII rendering of the surface using REAL labels from grounding.>

## Decisions

<One row per locked decision. "Wireframe" marks decisions additionally
validated visually or by measurement — that distinction is the point of having
built one. "carried (<slug>/Dn)" marks a verdict imported from the decisions
ledger and left unreopened. Group into 3–5 themed tables rather than one long
one.>

| # | Decision | Choice | Settled by |
|---|----------|--------|-----------|
| D1 | <question> | <choice> | interview · wireframe · carried (<slug>/Dn) |

## The contract

<The one or two structural rules the implementation must not break, with the
code that enforces them and the measurement that proves it. This is where a
"why it must be one sticky element, not four" argument lives, with the numbers
from `__wf.bands()`.>

## Architecture

<Component-level plan: what is new, what is modified, what is deleted. Real
paths. Call out any hidden restructuring cost the route tree does not reveal —
that is usually the largest item and the one that gets missed in estimates.>

| Component | Path | Change |
|---|---|---|

## Data model

<Only if the change needs one. Schema delta, resolution/precedence order, and
the backfill story — including what happens to records that predate it.>

## Behaviour

<Trigger → effect table. Every row should be mechanically testable.>

| Trigger | Effect |
|---|---|

<Then any non-obvious behaviour in prose, with the fix already written — e.g.
the scroll-anchoring baseline. If the wireframe hit it, say so: it is the
difference between a warning and a proven defect.>

## States

<Every state × role combination the overlay exposed, and what renders in each.
This table IS the control overlay's axes, resolved.>

| State | <region A> | <region B> |
|---|---|---|

## Verification

<Results from the browser-verification pass. Real numbers, and honest labels for
anything not verified.>

| Check | Result |
|---|---|
| Region contiguity (at rest / changed) | `0→44→76→131` / `-76→-32→0→55` — contiguous |
| Contrast, <pairing> | `#035530` on `#e7f2ec` — 7.8:1, AA pass |
| `button button` count | 0 |
| Off-screen focusables | 0 (focus guard verified) |
| <behavioural rule> | not verified — hidden tab |

## Risks

<Severity-rated, each with a recommendation. Be specific about blast radius:
"every route renders this component" is a risk; "might affect other pages" is
not.>

**R1 — <title> (high/medium/low).** <What could go wrong, why, what to do.>

## Open questions

<Genuinely undecided things. Better here than invented above. Each with enough
context that answering it does not require re-running the interview.>

- **Q1 — <question>?** <The trade-off, and what each answer would cost.>

## Out of scope

<What was explicitly excluded, so nobody re-litigates it — and so the estimate
matches the scope.>

## Testing

**Unit —** <the logic most likely to be wrong and cheapest to pin.>

**E2E —** <numbered, each derived from a row in Behaviour or Verification.>

1. <assertion>

<Flag the highest-value test and say why — usually the one that reproduces a
defect the wireframe found, because it is invisible in the default state.>

## References

- Wireframe — `wireframes/<slug>/v2.html` (<what it demonstrates>)
- Grounding — `wireframes/<slug>/grounding.md`
- <related plans/docs>

[path-ref]: <relative path to a real source file>
```

## Where it goes

1. **Project wiki**, if one exists (`wiki/`, `docs/wiki/`, or a configured
   vault) — follow that vault's schema, frontmatter, and index/log conventions.
2. **`./plans/<slug>.md`** otherwise.
3. If neither exists, ask once, then record the answer in the project's
   `CLAUDE.md` so the next run does not re-ask.

Link the wireframe from the spec with a **relative path** so the link survives
being read from a different checkout.
