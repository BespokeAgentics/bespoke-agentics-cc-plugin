# Phase 3 — Interview (classify divergences)

Read before Phase 3. The job: a raw divergence is not yet a finding. A wireframe is a settled design, but a build sometimes deliberately improves past it. The interview decides, per divergence, whether it is a **regression from the decided design**, an **intended evolution**, or **out of scope** — and sets priority. This is what keeps the report honest rather than a pile of model suspicion.

Runs after grounding + measurement synthesis, so every question is concrete and backed by evidence on both sides. On `--depth deep` it runs after adversarial verification has already dropped the measurement artifacts.

## Print a digest first

Before any question, print a short digest so the user sees the shape:

```
Parity digest — <slug> vs <app-url>
  ✅ honored:   9 decisions, 5 measured checks
  ⚠️ drifted:   3   (rail width 236→248px · accent hex · empty-state copy)
  ❌ diverges:  1   (breadcrumb no longer the single sticky element — contract R1)
  ➖ not measured: 2 states (admin, archived — auth-gated)
```

## Batch the questions (AskUserQuestion, ≤4 per round)

- **Batch 1 — classify the real ones.** For each `diverge` and each material `drift`, ask: is this a **regression** (fix the build to match the decision), **intended evolution** (the build is right, the wireframe is stale — record it), or **out of scope**? Give each option the evidence: the decided value, the as-built value, and the `file:line`. Example:
  > "The wireframe settled the rail at 236px (D5); the build renders 248px (`FeatureSectionRail.tsx:24`). Regression, intended change, or not worth flagging?"
- **Batch 2 — resolve blocking ambiguities.** Where a decision's intent is unclear against what shipped ("the spec says 'primary action pinned' — the build pins a different action"), ask what was meant.
- **Batch 3 — priority.** For the confirmed regressions, set P0/P1/P2 (multiSelect). A broken contract invariant defaults to P0.

## Rules

- **Intended evolution is a first-class outcome, not a loss.** When the user says the build is right, the divergence becomes a recorded "design evolved" note (and a nudge that the wireframe/decisions ledger is now stale) — not a finding against the build.
- **Don't re-litigate honored parity.** Only divergences and material drifts get questions. Don't ask about the 9 things that matched.
- **A settled Decision carries weight.** If the user wants to keep a divergence from an explicit `Settled by: interview/wireframe` decision, that's their call — but record that a settled decision was consciously overridden, so the trail shows it.
- If the interview is declined, classify by the default rule (contract break or dropped decision → regression; everything else → open question), mark all `UNVALIDATED`, and say so in the report.

Write `{ANALYSIS_DIR}/interview-answers.md`: per divergence, the classification, priority, and any resolved ambiguity. This **overrides** the raw measured/grounding verdicts in Phase 4.
