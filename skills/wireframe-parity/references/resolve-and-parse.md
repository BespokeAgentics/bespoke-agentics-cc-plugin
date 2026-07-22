# Phase 0 — Resolve & Parse the intended model

Read before Phase 0. The job: turn the wireframe's spec (+ its wireframe HTML and decisions ledger) into `intended-model.md` — the structured "intended UI" every later phase diffs against. You do this yourself in the main session; it is the spine.

## Resolve the inputs

From `spec-or-slug`:

- **A slug** → spec at `wiki/…/<slug>` or `./plans/<slug>.md`; wireframe at `wireframes/<slug>/` (highest `vN.html`); ledger at `wireframes/_library/decisions.md`; grounding cache at `wireframes/_library/grounding-cache.md`.
- **A spec path** → read it; find the wireframe from its **References** section (`Wireframe — wireframes/<slug>/vN.html`), which gives the slug.
- **Neither given** → list `wireframes/*/` dirs that have a `vN.html`, match each to a spec, and propose the most recent; confirm before proceeding.

If a spec resolves no wireframe HTML, stop — this skill reviews *against* a wireframe.

## What to extract (from `references/spec-template.md`'s sections)

Write `intended-model.md` with these blocks:

| Block | Source in the spec | Why the parity check needs it |
|---|---|---|
| **Decisions** | `## Decisions` table + `_library/decisions.md` rows for this slug | The parity contract. Each row: id, the question, the settled choice, and `Settled by` (interview · wireframe · carried · browser comment). A build that breaks one of these is a regression. |
| **Contract invariants** | `## The contract` | The one or two structural rules the implementation "must not break", each with its `__wf.bands()` numbers. These are the highest-severity checks. |
| **States** | `## States` table | Each row is an axis combination (role × entity-state × …). Map each to (a) the **wireframe URL** that reproduces it and (b) a short description of the **equivalent app state** (which route, which role, which interaction). |
| **Verification snapshot** | `## Verification` table | The frozen `__wf` numbers: band contiguity (`0→44→76→131`), contrast (`#035530 on #e7f2ec — 7.8:1, AA pass`), `button button` count, off-screen focusables. This is the intended measurement to diff the app against. Copy it verbatim. |
| **Real labels / enums** | `## Overview`, the wireframe's REPLACE 3 markup, `_library/grounding-cache.md` | The literal strings the UI must render ("Internal Review", not `in_review`). |
| **Region ↔ zone map** | wireframe `class="wf-zone" data-z="1 · label"` markers | The vocabulary that aligns a spec "region" to a real DOM node in both the wireframe and the app. |

## Reproduce a state as a URL

A wireframe state **is** a URL: the overlay mirrors every axis into `location.hash`, and the scaffold re-hydrates on `hashchange`. So each States-table row becomes:

```
{WIREFRAME_BASE}#role=admin&density=v-compact&guides=0
```

Record that URL next to each state in `intended-model.md`. The app has no such hash — its equivalent state is reached by real navigation/interaction, which you describe (and Phase 1 grounding locates the role/permission logic that drives it).

## Honesty rules

- **Read, don't invent.** Every intended value comes from the spec, the wireframe source, or the grounding cache — with its citation. If the spec has no Verification table (an older wireframe, or `--no-verify` was used), say so: measured parity then diffs the app against the *re-measured wireframe* only, and the "spec-frozen" column reads "absent".
- **The grounding cache is authoritative for tokens/labels/roles** (`path:line`, TTL-dated). Use it rather than re-deriving; note if an entry is past its TTL (it may have drifted — Phase 1 confirms).
- If a decision in the ledger is `superseded`, use the superseding row; note the history.

Output: `{ANALYSIS_DIR}/intended-model.md`.
