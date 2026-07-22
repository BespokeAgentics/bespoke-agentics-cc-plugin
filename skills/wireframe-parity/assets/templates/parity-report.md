---
type: report
status: draft
date: {{DATE}}
source: wireframe-parity
spec: {{SPEC_PATH}}
slug: {{SLUG}}
wireframe: {{WIREFRAME}}
app: {{APP_URL | "structural-only"}}
depth: {{DEPTH}}
parity: {{🟢 Faithful | 🟡 Minor drift | 🔴 Diverges}}
measured: {{true|false}}
related: []
---

# Parity — {{SURFACE}}

> **Parity: {{🟢 Faithful | 🟡 Minor drift | 🔴 Diverges}}** — {{one-line verdict}}
>
> Wireframe `{{WIREFRAME}}` vs {{APP_URL | "implementation (structural-only)"}} · spec `{{SPEC_PATH}}` · depth `{{DEPTH}}`
> Tolerance: geometry ±2px · contrast same AA/AAA verdict · contiguity as the contract requires.
> _This review is read-only. The implementation was not modified._

## Summary

{{2–4 sentences: what was built, the headline parity result, and the single most important divergence
to reconcile — or, if 🟢, that the build faithfully matches the decided design.}}

| | Count |
|---|---|
| ✅ Decisions honored | {{H}} / {{TOTAL}} |
| ⚠️ Drifted | {{Dr}} |
| ❌ Diverged (regressions) | {{Rg}} |
| Measured checks pass / diverge | {{P}} / {{F}} |
| States not measured | {{NM}} |
| Intended evolutions (recorded) | {{Ev}} |

## Strengths

What the build got right — faithful to the decided design; don't churn these.

- {{specific match, e.g. "Rail renders the settled flat outline (D3) at 236px, contiguous with the header stack — matches the contract exactly."}}
- {{…}}

## Decision parity

One row per settled Decision. **Verdict:** ✅ honored · ⚠️ drifted · ❌ diverged · ➖ not implemented.
Evidence cites the decision (id / spec §) and the as-built `file:line` (+ measurement where relevant).

| # | Decision | Settled choice | As-built | Verdict | Evidence |
|---|----------|----------------|----------|---------|----------|
| D1 | {{question}} | {{settled choice}} | {{what shipped}} | {{✅/⚠️/❌/➖}} | {{spec §Decisions · `file:line`}} |

## Measured parity

Same probe (`wf-probe.js`) on both sides, per state. Δ against the tolerance above.
{{If --no-browser or unavailable: "Not measured — structural-only run. Every geometry/contrast row below is unverified."}}

| State | Region | Intended (wireframe) | Spec-frozen | As-built (app) | Δ | Verdict |
|---|---|---|---|---|---|---|
| {{default}} | {{band contiguity}} | `0→44→76→131` | `0→44→76→131` | `0→44→76→131` | 0 | ✅ pass |
| {{default}} | {{pill contrast}} | `7.8:1 AA` | `7.8:1 AA` | `6.9:1 AA` | AA held | ✅ pass |
| {{scrolled}} | {{sticky contiguity}} | `contiguous` | `contiguous` | `gap 12px` | +12 | ❌ diverge |

## Label & enum fidelity

Does the app render the real strings the wireframe used?

| Where | Intended label | As-built | Verdict |
|---|---|---|---|
| {{status pill}} | `Internal Review` | {{`in_review`}} | {{✅/❌}} |

## Divergence register

<!-- Color legend: 🟢 OOTB · 🔵 Config · 🟡 Custom Dev · 🔴 Gap · ⚪ TBD · 🟣 3rd Party.
     Class: regression = breaks a settled decision · intended-evolution = build improved past the
     wireframe (recorded, not a fault) · unspecified = spec never fixed this (out of parity scope). -->

{{INSERT divergence-register table}}

## Intended evolutions

Divergences the interview confirmed as deliberate improvements — the build is right, the **wireframe/decisions ledger is now stale**.

- {{"Rail width 236→248px — widened to fit the longest real label; keep. Update D5."}}

## Not measured

Honest coverage. Every state/check not verified, and why — so nobody reads silence as a pass.

- {{"admin, archived states — auth-gated; no session available. Structural grounding only."}}

## Open questions

- {{question — and what each answer would change about the parity call}}

## Definition of parity

Tick these and the verdict flips to 🟢. Derived from the confirmed regressions.

- [ ] {{restore the single sticky element (contract R1) — `FeatureHeader.tsx:41`}}
- [ ] {{map the status enum to its label ("Internal Review")}}
- [ ] {{re-run `/bespokeagentics:wireframe-parity {{SLUG}} --app {{APP_URL}}` — expect 🟢}}

## Appendix — coverage

- **Decisions grounded:** {{N}} to real source (`file:line`).
- **States measured:** {{N}} of {{S}} ({{list unreachable, with reason}}).
- **Wireframe re-measured:** {{yes|no}} · **Spec Verification snapshot:** {{present|absent}}.
- {{If --no-browser or repo mismatch: "Structural-only — all geometry/contrast findings are UNVERIFIED."}}
