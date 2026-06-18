---
type: knowledge
layer: hypotheses
domain: "{{DOMAIN}}"
status: active
created: "{{DATE}}"
updated: "{{DATE}}"
related:
  - "[[INDEX]]"
  - "[[_schema]]"
  - "[[rules]]"
tags: [knowledge-loop, "{{DOMAIN}}"]
---

# {{DOMAIN}} — Hypotheses

Candidate rules for **{{DOMAIN}}** — patterns that look true but are **not yet trusted enough to
apply by default**. Each carries a confirmation/contradiction counter. A hypothesis with
`confirmations ≥ 3` from distinct sources and `contradictions: 0` is promoted to [[rules]].

Counter rule: **one distinct, dated, linked source per increment** (see [[_schema]] / algorithm §3).

## Entries

<!-- knowledge-loop:entries -->
<!-- Format (see _schema / loop-algorithm.md §2):

### {{DOMAIN}}-H-001 — <candidate rule statement>
- status: open            # open | promoting | demoted
- confirmations: 1
- contradictions: 0
- applies-when: <trigger that /knowledge:review matches against a task>
- opened: YYYY-MM-DD
- updated: YYYY-MM-DD
- evidence:
  - +1 YYYY-MM-DD [[<link>]] — <reason>
- tags: {{DOMAIN}}, <...>

-->

_No hypotheses open yet._

<!-- /knowledge-loop:entries -->

## Promoted

<!-- knowledge-loop:promoted -->
<!-- Hypotheses moved up to [[rules]], kept here for history. Each notes its new rule id. -->

_None promoted yet._

<!-- /knowledge-loop:promoted -->
