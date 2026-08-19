# Reimagine spec template

Read before Phase 7. A delta on the parent skill's `references/spec-template.md`
— its laws hold (every claim carries a path; every decision records how it was
settled; drop sections that don't apply, never pad). What changes: the spec
records a *choice among alternatives*, so the rejected directions are first-
class content, and the core section is the **divergence-from-current
inventory** — the implementer's worklist for moving the real component to the
winning design.

The winner's **Verification table uses the parent's exact format**, so
`/bespoke-agentics:wireframe-parity` can consume this spec unchanged once the
redesign ships.

```markdown
# <Surface> — reimagined: <winning direction> (<tier>)

> **Status:** Draft — spec only, not implemented · **Created:** <YYYY-MM-DD>
>
> <2–4 sentences: what the surface becomes and why this direction won. Note the
> gallery size — "N directions pitched, M built, winner: X (hybrid of …)" — and
> the interview size.>

## Chosen direction & rationale

<The winning thesis, why it won (quote critique-round evidence), and what it
stole from losers — stolen elements are the fingerprint of a real gallery
process, name them: "the collapsed toolbar is B's, grafted in round 3".>

## Rejected directions

<One row per pitched direction that lost. `brief` = never built (lighter
evidence); `gallery` = built and seen. Reasons come from the winner round's
confirmations, not invention. These rows also append to the ledger.>

| Direction | Tier | Thesis | Rejected at | Reason | Pane |
|---|---|---|---|---|---|
| "Ledger" | Restructure | <thesis> | gallery | <confirmed reason> | [link](reimagine-v1.html#rv=ledger&view=single) |

## Decisions

<The parent's interchange format. Settled by: interview · gallery · browser
comment · carried (<slug>/Dn). "gallery" marks decisions validated by seeing
the rendered thing — that distinction is the point of having built one.>

| # | Decision | Choice | Settled by |
|---|----------|--------|-----------|

## The contract

<The winner's structural rules an implementation must not break, with the
numbers from `__wf.bands()` that prove them. Same as the parent.>

## Divergence-from-current inventory

<THE core section — one row per region/element that changes from the real,
shipped component. "Current" cites real source; "Becomes" describes the winner
pane. Change class drives estimation: css-only < markup < interaction <
new-component. This table is the implementer's worklist; if a row is missing,
that change silently won't happen.>

| # | Region/element | Current (path:line) | Becomes | Change class |
|---|---|---|---|---|
| Δ1 | Status column | src/…/OrdersTable.tsx:114 | row-group headers | markup |

## States

<Shared-axis matrix resolved for the WINNER: every axis value × what renders.
Populated (longest-case) and empty are mandatory rows.>

| State | <region A> | <region B> |
|---|---|---|

## Behaviour

<Trigger → effect table. Mandatory when the winner is a Rethink — a new
interaction model with no behaviour table is not a spec.>

| Trigger | Effect |
|---|---|

## Verification

<Table 1 — the winner's full battery, parent's exact format (wireframe-parity
consumes this). Honest labels for anything not measured.>

| Check | Result |
|---|---|
| Region contiguity (at rest / changed) | `0→44→76→131` — contiguous |
| Contrast, <pairing> | `#…` on `#…` — 7.8:1, AA pass |
| `button button` count | 0 |
| Off-screen focusables | 0 |
| <behavioural rule> | not verified — hidden tab |

<Table 2 — gallery checks, one row per built variant incl. retired ones. This
evidences the rejections: "B lost partly on contrast" needs B's number.>

| Variant | Tier proxy | AA (key pairs) | Markup clean | Focusables |
|---|---|---|---|---|

## Baseline fidelity

<The chip's claim, expanded: cross-checked (date, deltas found) or
code-grounded only; then the approximations list from grounding.md verbatim.
This bounds how much to trust the Δ inventory's Current column.>

## Risks · Open questions · Out of scope

<As the parent. Out of scope MUST list the states deliberately excluded
(loading/error/responsive unless pulled in) — and note the narrow-viewport
spot-check result on the winner.>

## Handoff

- **Fine-grained settlement:** `/bespoke-agentics:interactive-wireframe
  '<surface>' --slug <slug>` — the winner becomes the surface under discussion;
  this spec's Decisions carry in via the ledger. Offer, don't assume.
- **Build:** `/bespoke-agentics:orchestrate` or workstream-orchestrate, with
  this spec (the Δ inventory is the work breakdown).

## References

- Gallery — `wireframes/<slug>/reimagine-v2.html` (relative path; state links
  per pane in Rejected directions)
- Grounding — `wireframes/<slug>/grounding.md`
```

## Where it goes

Same resolution as the parent: project wiki → `./plans/<slug>.md` → ask once
and record in `CLAUDE.md`. Decision rows AND rejected-direction rows append to
`wireframes/_library/decisions.md`; the `_index.md` run row gets
`Type: reimagine`.
