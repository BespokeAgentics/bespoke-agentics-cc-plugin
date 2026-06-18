---
type: knowledge
layer: rules
domain: "{{DOMAIN}}"
status: active
promotion-threshold: 3
created: "{{DATE}}"
updated: "{{DATE}}"
related:
  - "[[INDEX]]"
  - "[[_schema]]"
  - "[[hypotheses]]"
tags: [knowledge-loop, "{{DOMAIN}}"]
---

# {{DOMAIN}} — Rules (apply by default)

Confirmed knowledge for **{{DOMAIN}}**. These are **applied by default** to any matching task —
`/knowledge:review` surfaces them before work begins. A rule reached this layer with ≥3 distinct
confirmations and zero contradictions.

**Demotion:** a single contradicting source demotes a rule back to [[hypotheses]]
(`status: demoted`). Rules are trusted precisely because they are kept honest.

`promotion-threshold` (frontmatter) may be raised above 3 for high-stakes domains; never lowered.

## Entries

<!-- knowledge-loop:entries -->
<!-- Format (see _schema / loop-algorithm.md §2):

### {{DOMAIN}}-R-001 — <rule statement>  (apply by default)
- from: {{DOMAIN}}-H-00X
- confirmations: 3
- contradictions: 0
- applies-when: <trigger>
- promoted-on: YYYY-MM-DD
- wiki-page:            # set by /knowledge:promote — the proper wiki page for this rule
- evidence:
  - +1 YYYY-MM-DD [[<link>]]
  - +1 YYYY-MM-DD [[<link>]]
  - +1 YYYY-MM-DD [[<link>]]
- tags: {{DOMAIN}}, <...>

-->

_No rules confirmed yet._

<!-- /knowledge-loop:entries -->
