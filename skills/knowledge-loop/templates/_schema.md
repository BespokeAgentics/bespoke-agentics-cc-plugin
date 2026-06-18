---
type: knowledge
layer: schema
status: active
created: "{{DATE}}"
updated: "{{DATE}}"
related:
  - "[[INDEX]]"
tags: [knowledge-loop, schema]
---

# Knowledge Store — Schema

The contract for this knowledge store. Read it before editing any layer file. The full
algorithm (counters, promotion/demotion, integrity rules) lives in the `knowledge-loop`
skill's `references/loop-algorithm.md` — this page is the at-a-glance version that lives
next to the data.

## Layers

Each domain folder holds exactly three layer files, in increasing order of confidence:

| File | `layer:` | Holds | How it's used |
|------|----------|-------|---------------|
| `knowledge.md` | `facts` | Observed facts and patterns | Reference material; seeds hypotheses |
| `hypotheses.md` | `hypotheses` | Candidate rules, not yet trusted | Tested on touch; counters move on evidence |
| `rules.md` | `rules` | Confirmed knowledge | **Applied by default** unless contradicted |

## Frontmatter (every layer file)

```yaml
---
type: knowledge          # always "knowledge" so wiki tooling sees these pages
layer: facts             # facts | hypotheses | rules | index | schema
domain: pricing          # the domain slug (folder name)
status: active
created: YYYY-MM-DD
updated: YYYY-MM-DD
related: ["[[INDEX]]"]   # plus any wiki pages this domain references
tags: [knowledge-loop, <domain>]
---
```

`rules.md` may additionally set `promotion-threshold: <n>` (default 3, never below 3) to raise
the bar for that domain.

> **Linting note:** `type: knowledge` is a knowledge-store page type. If `/wiki:lint` enforces a
> closed `type` enum, allowlist `knowledge` (these pages live under `wiki/knowledge/`).

## Entry format

Entries live under a `## Entries` heading in each file. IDs are `<domain>-<F|H|R>-<nnn>`.
See `references/loop-algorithm.md` §2 for the full field list. Minimal shapes:

- **Fact:** id + title, `observed:`, `source:` (a link), `tags:`.
- **Hypothesis:** id + title, `status:`, `confirmations:`, `contradictions:`, `applies-when:`,
  dated linked `evidence:` bullets (`+1`/`-1`), `tags:`.
- **Rule:** id + title, `from:`, `confirmations:`, `contradictions: 0`, `applies-when:`,
  `promoted-on:`, `wiki-page:`, `evidence:`, `tags:`.

## The loop (one screen)

1. **Before a task** → `/knowledge:review` — load rules (apply by default) + testable hypotheses.
2. **During** → apply rules; let the work confirm or contradict hypotheses.
3. **After a task** → `/knowledge:extract` — write facts, move counters (one distinct, dated,
   linked source per increment), auto-promote at ≥3 confirmations / 0 contradictions, auto-demote
   any contradicted rule.
4. **Bridge** → `/knowledge:promote` — turn confirmed rules into proper wiki pages.
5. **Maintain** → `/knowledge:audit` — candidates, stale entries, integrity, broken links.
