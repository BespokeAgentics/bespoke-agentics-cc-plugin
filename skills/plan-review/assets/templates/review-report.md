---
type: report
status: draft
date: {{DATE}}
source: plan-review
artifact: {{ARTIFACT_PATH}}
artifact_type: {{ARTIFACT_TYPE}}
depth: {{DEPTH}}
readiness: {{🟢 Ready | 🟡 Needs revisions | 🔴 Not ready}}
grounded: {{true|false}}
related: []
---

# Review — {{ARTIFACT_TITLE}}

> **Readiness: {{🟢 Ready | 🟡 Needs revisions | 🔴 Not ready}}** — {{one-line verdict}}
>
> Reviewed: `{{ARTIFACT_PATH}}` ({{type}}) · depth `{{DEPTH}}` · {{grounded against N files | document-only}}
> _This review is read-only. The original artifact was not modified._

## Summary

{{2–4 sentences: what this artifact is, the headline result, and the single most important thing to
address. If 🟢, say so plainly.}}

| | Count |
|---|---|
| 🔴 Blockers | {{B}} |
| 🟡 Majors | {{M}} |
| ⚪ Minors | {{m}} |
| Claims contradicted by code | {{N}} |
| Anchors unresolved / not found | {{N}} |

## Strengths

What the plan gets right — keep doing these, don't churn them.

- {{specific strength, e.g. "Clear, testable acceptance criteria in §3."}}
- {{…}}

## Findings

Grouped by severity. Each cites the artifact quote and (where grounded) the real `file:line`.
**Kind:** `error` = code contradicts the plan · `gap` = missing & needed · `improvement` = better-with.

### 🔴 Blockers

#### F1 — {{title}}   `{{error|gap|improvement}}`
- **In the artifact:** "{{quote}}" ({{§section}})
- **In the code:** `{{file:line}}` — {{what the code actually does}}
- **Why it matters:** {{consequence of building as-written}}
- **Recommendation:** {{concrete next step}}
- **Status:** {{CONFIRMED P0 (user) | UNVALIDATED}}

### 🟡 Majors

#### F3 — {{title}}   `{{kind}}`
- **In the artifact:** "{{quote}}"
- **In the code:** `{{file:line}}`
- **Why it matters:** {{…}}
- **Recommendation:** {{…}}

### ⚪ Minors / polish

- F7 — {{title}} — {{one-line recommendation}} ({{evidence}})

## Resolved during review

Ambiguities the interview settled — treat these as decisions, not open questions.

- {{"improve the loading state" → add a skeleton + 5s timeout message}}

## Considered & dismissed

Findings raised but ruled out of scope by the author — recorded for the trail.

- {{F4 — out of scope: /edge/* is deprecated (per author)}}

## Gap & ambiguity register

<!-- Inline the gap-register table here, or link to a sibling file. Color legend:
     🟢 OOTB · 🔵 Config · 🟡 Custom Dev · 🔴 Gap · ⚪ TBD · 🟣 3rd Party -->

{{INSERT gap-register table}}

## Open questions

Unresolved after review — answer before or during the build.

- {{question — and what each answer would change}}

## Definition of ready

Tick these and the verdict flips to 🟢. Derived from the confirmed P0/P1 findings.

- [ ] {{close blocker F1: add the edge/auth.ts task}}
- [ ] {{add acceptance criteria to §2 (testable)}}
- [ ] {{add a rollback step}}

## Appendix — grounding coverage

- **Grounded:** {{N}} anchors confirmed to real source.
- **Contradicted:** {{N}} claims the code disproves (see Findings).
- **Unresolved / not found:** {{N}} — {{list, with what was searched}}.
- {{If --no-ground or repo mismatch: "Document-only review — feasibility findings are UNCONFIRMED."}}
