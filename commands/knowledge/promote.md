---
name: "knowledge:promote"
description: "Bridge confirmed rules into the wiki: turn each rule that has no wiki page into a proper ADR-style wiki page (single source of truth), cross-linked back to the rule. Also handles manual promote/demote overrides."
argument-hint: "[--domain <slug>] [--demote <rule-id>] [--rule <rule-id>]"
allowed-tools: Skill(knowledge-loop), Agent, AskUserQuestion, Read, Write, Edit, Glob, Grep
---

# Knowledge Loop — Promote (the wiki bridge)

The hybrid step. Confirmed rules live in the lightweight store for speed; this command promotes
them into **proper wiki pages** so the wiki stays the single source of truth for validated
knowledge — satisfying the Wiki-First Mandate.

## Arguments

Parse from `$ARGUMENTS`:

```
[--domain <slug>] [--demote <rule-id>] [--rule <rule-id>]
```

- `--domain <slug>` — only bridge rules in this domain.
- `--rule <rule-id>` — bridge one specific rule (e.g., `pricing-R-003`).
- `--demote <rule-id>` — manual override: push a rule back to `hypotheses.md` (e.g., it's stale or
  you know it no longer holds), updating any bridged wiki page to `status: revisited`.

## Process

Invoke the `knowledge-loop` skill with `mode: promote`. The skill:

1. **Finds candidates** — rules with an empty `wiki-page:` (plus any named via `--rule`).
2. **Creates/updates the wiki page** — default mapping is an **ADR-style `type: decision`** page
   (`status: approved`), located by domain (a client → that client's `decisions/`; otherwise
   `wiki/verndale/playbooks/`). It confirms the location/type via `AskUserQuestion` on the first
   promotion of a run.
3. **Cross-links** — sets the rule's `wiki-page:` to the new page and adds the rule to the page's
   `related:` (bidirectional).
4. **Logs + indexes** — appends to `wiki/_log.md` and adds the page to `wiki/_index.md`.

For `--demote`, it performs the rule→hypothesis transition per the algorithm and updates the
bridged wiki page's status.

## Examples

```bash
/knowledge:promote                       # bridge every unbridged confirmed rule
/knowledge:promote --domain pricing      # just the pricing rules
/knowledge:promote --rule pricing-R-003  # one rule
/knowledge:promote --demote pricing-R-001
```
