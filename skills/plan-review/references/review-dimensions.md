# Phase 2 — Multi-Lens Review

Goal: review the artifact through several independent lenses at once, then merge into one
de-duplicated, severity-rated `findings.md`. Each lens is a different way a plan fails; running them in
parallel (one reviewer agent per lens) catches failure modes a single pass blurs together.

## The lenses

Launch one `general-purpose` reviewer per lens, all in a single response. Use `general-purpose` (not
`Explore`) because a reviewer must *reason and judge*, not just locate. Each reviewer receives the
artifact text, `artifact-map.md`, and `grounding-map.md`, and returns findings **only for its lens**.

| Lens | The question it asks | Signature findings |
| ---- | -------------------- | ------------------ |
| **Completeness** | What's missing that this work needs? | No tests / rollback / migration / error & empty states / observability / docs; a task with no owner or no acceptance criterion; an implied-but-unplanned step from the grounding map's "missed" list. |
| **Feasibility / correctness** | Will this actually work against the real code? | A CONTRADICTED claim; a referenced file that doesn't exist; an approach that fights the existing architecture; callers the plan forgot; an API used the way it doesn't behave. (Leans hardest on `grounding-map.md`.) |
| **Risk / blast radius** | What could go wrong, and how badly? | Breaking change to a shared API; irreversible data migration with no backup; security/authz hole; perf cliff; race/ordering hazard; no feature flag on a risky path; backward-incompatibility. |
| **Clarity / ambiguity / testability** | Could two engineers read this and build different things? | Vague verbs ("improve", "handle", "make robust") with no definition; undefined terms; untestable acceptance criteria ("should be fast"); ambiguous ownership; unspecified edge-case behavior. |
| **Scope / sequencing** | Is it the right size and order? | Too big to land safely (should be split); steps in an order that won't compile/deploy; hidden dependency between steps; a prerequisite that isn't called out; scope creep beyond the stated intent; a non-goal that's quietly in-scope. |

Tune by type: for an **issue/bug** report, weight Clarity (repro steps, expected-vs-actual) and
Feasibility (is the suspected root cause real?) and go light on Sequencing. For a **plan/spec**, all
five carry weight.

## Finding schema

Every reviewer returns findings in this shape (see `assets/templates/finding.schema.json`):

```json
{
  "id": "F1",
  "lens": "feasibility",
  "kind": "error",            // gap | improvement | error
  "severity": "blocker",      // blocker | major | minor
  "title": "Plan edits one of two auth middleware chains",
  "artifact_evidence": "\"update the auth middleware in mw.ts\" (§2)",
  "code_evidence": "edge/auth.ts:12 — a second, separate chain the plan never mentions",
  "why": "Requests on /edge/* bypass the change; the auth fix would be half-applied.",
  "recommendation": "Add a task to update edge/auth.ts:12, or state explicitly why it's out of scope.",
  "status_color": "🔴"        // gap register color: 🟢🔵🟡🔴⚪🟣
}
```

Keep the three **kinds** distinct — they ask different things of the author:

- **gap** — the plan is missing something it *needs* (a required step, a test, a migration).
- **improvement** — the plan would be *better* with something extra (it's not wrong without it).
- **error** — the plan asserts something the code *contradicts* (a wrong claim, a missing file).

## Severity rubric

- **blocker** — building from this as-written produces a broken, unsafe, or wrong result, or work
  stalls until it's resolved. (A CONTRADICTED claim, an irreversible migration with no rollback, an
  acceptance criterion so vague the feature can't be verified.)
- **major** — real risk or a meaningful gap; the plan can proceed but will likely cause rework, a
  follow-up bug, or a stalled review.
- **minor** — polish, clarity, nice-to-have; safe to ignore but cheap to fix.

Anchor severity to consequence, not to how confident you are. Low-confidence-but-high-consequence
belongs in the report as an **open question**, not inflated to a blocker.

## De-duplication & merge

The same weakness often surfaces from two lenses (a missing migration is both a completeness gap and a
risk). After all reviewers return:

1. Merge findings that point at the same root cause; keep the sharpest framing and union the evidence.
2. Re-number `F1…Fn`, sorted by severity then kind (errors before gaps before improvements).
3. Write `{ANALYSIS_DIR}/findings.md` — the schema above rendered as readable sections grouped by
   severity, plus a one-line tally (`{B} blocker, {M} major, {m} minor`).

If the artifact is genuinely solid, it is correct for `findings.md` to be short. Do not pad. A review
that says "two minor clarity nits, otherwise ready" is a *good* outcome when it's true.

## Phase 2.5 — Adversarial verification (`--depth deep` only)

False positives erode trust faster than missed nits. On `deep`, before the interview, spawn one
skeptic per blocker/major finding (parallel, `general-purpose`), each prompted to **refute** it:

```
Try to REFUTE this finding. Assume the reviewer was wrong until the evidence forces otherwise.
Finding: {finding}
Check the cited file:line and the artifact quote. Is the gap actually covered elsewhere in the
artifact? Does the code actually behave as the finding claims? Default to refuted=true if the
evidence is thin or you can't reproduce it.
Return: {verdict: holds|refuted, reason, corrected_evidence?}
```

Drop refuted findings (or downgrade to open questions if genuinely uncertain). Note in `findings.md`
which findings survived adversarial review — it tells the user the blockers are real.
