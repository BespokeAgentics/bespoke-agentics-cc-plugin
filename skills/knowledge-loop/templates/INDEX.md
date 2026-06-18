---
type: knowledge
layer: index
status: active
created: "{{DATE}}"
updated: "{{DATE}}"
related:
  - "[[_schema]]"
tags: [knowledge-loop, index]
---

# Knowledge Store — Index

Router for the self-improving knowledge loop. Each domain compounds facts → hypotheses → rules.
Counts are maintained by `/knowledge:extract` and verified by `/knowledge:audit`.

- Schema & loop rules: [[_schema]]
- Before a task: `/knowledge:review --domain <slug>`
- After a task: `/knowledge:extract --domain <slug>`
- Bridge rules to the wiki: `/knowledge:promote`
- Health check: `/knowledge:audit`

## Domains

<!-- knowledge-loop:domains -->
<!-- One row per domain. Maintained by /knowledge:extract and /knowledge:audit. -->

| Domain | Facts | Hypotheses | Rules | Promotion candidates | Updated |
|--------|------:|-----------:|------:|----------------------|---------|
| _none yet — run `/knowledge:extract` after a task to seed the first domain_ | 0 | 0 | 0 | 0 | — |

<!-- /knowledge-loop:domains -->

## Legend

- **Promotion candidate** — a hypothesis at `confirmations: 2, contradictions: 0` (one solid
  source away from becoming a rule).
- A **rule** is applied by default. A single contradiction demotes it back to a hypothesis.
