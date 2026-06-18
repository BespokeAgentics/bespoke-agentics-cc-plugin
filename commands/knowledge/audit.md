---
name: "knowledge:audit"
description: "Health-check the knowledge store: promotion candidates, stale hypotheses, contradiction hotspots, counter-integrity violations, rules not yet bridged to the wiki, and broken links. Read-only unless --fix."
argument-hint: "[--domain <slug>] [--stale-days <n>] [--fix]"
allowed-tools: Skill(knowledge-loop), Read, Glob, Grep, Edit, Write
---

# Knowledge Loop — Audit

Keep the store trustworthy. Because rules are **applied by default**, the store is only as useful
as it is honest — this surfaces drift, gaming, and gaps.

## Arguments

Parse from `$ARGUMENTS`:

```
[--domain <slug>] [--stale-days <n>] [--fix]
```

- `--domain <slug>` — limit to one domain.
- `--stale-days <n>` — age (default 30) past which an un-reinforced hypothesis is "stale".
- `--fix` — apply safe mechanical fixes (recount counters from evidence bullets, refresh
  `INDEX.md` counts, repair obvious link typos). Without it, the audit is read-only.

## Process

Invoke the `knowledge-loop` skill with `mode: audit`. It reports, prioritized:

1. **Promotion candidates** — hypotheses at/near the bar (e.g., `confirmations: 2, contradictions: 0`).
2. **Stale hypotheses** — no new evidence in `--stale-days`.
3. **Contradiction hotspots** — rules with `contradictions > 0` (should have demoted) and
   conflicted hypotheses.
4. **Integrity violations** — a counter incremented twice by the same source, or a count that
   disagrees with its evidence bullets (per `references/loop-algorithm.md` §7).
5. **Bridge gaps** — confirmed rules with an empty `wiki-page:`.
6. **Broken links** — unresolved `[[wiki-links]]` or `related:` references.

## Examples

```bash
/knowledge:audit                       # full read-only health report
/knowledge:audit --domain pricing
/knowledge:audit --stale-days 14 --fix # tighter staleness, apply mechanical fixes
```
