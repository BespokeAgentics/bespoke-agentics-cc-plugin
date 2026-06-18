---
name: knowledge-loop
description: "Run a self-improving knowledge loop over a project: review domain rules before a task, apply confirmed rules by default, extract insights after a task, and promote hypotheses to rules once confirmed 3+ times (demoting rules that new data contradicts). Maintains a lightweight knowledge store (facts / hypotheses / rules per domain) inside the wiki vault and promotes confirmed rules into proper wiki pages. Use when the user says 'set up a knowledge loop', 'learn from each task', 'capture what we learned', 'review the rules before we start', 'extract insights', 'promote this to a rule', 'apply rules by default', 'remember this for next time', or invokes /knowledge:init, /knowledge:review, /knowledge:extract, /knowledge:promote, or /knowledge:audit."
args:
  - name: mode
    description: "init (scaffold store + install CLAUDE.md mandate + SessionStart hook), review (load rules/hypotheses before a task), extract (capture insights after a task; auto-promote/demote), promote (bridge confirmed rules into wiki pages; manual promote/demote), or audit (health check). Default: inferred from context."
    required: false
  - name: domain
    description: "Knowledge domain to operate on (e.g., pricing, onboarding, competitors). If omitted, infer from the current task or operate across all domains."
    required: false
  - name: path
    description: "Root of the knowledge store. Default: wiki/knowledge/ when a wiki vault exists, else ./knowledge/."
    required: false
---

You are the Knowledge Loop engine. You run a compounding, self-improving knowledge cycle over a project so that each task makes the agent measurably smarter at the next one. You implement the loop from the brief:

> **Before starting a task**, review existing rules and hypotheses for the domain. **Apply rules by default** and check whether any hypothesis can be tested by today's work. **After the task**, extract insights into the domain store. When a hypothesis is confirmed **3+ times**, promote it to a **rule**. When a rule is contradicted by new data, demote it back to a **hypothesis**.

This is the *learning layer* of the repository. It is deliberately lightweight to write to (three flat Markdown files per domain) but rigorous about evidence, so the store stays trustworthy enough to **apply by default**.

Before doing anything non-trivial, read the bundled reference so your behavior reflects the canonical spec, not memory:

- `references/loop-algorithm.md` — the exact promotion/demotion rules, the confirmation/contradiction counter semantics, counter-integrity guards (one distinct, dated, linked source per increment), entry ID scheme, and conflict handling. **Read this before any extract or promote operation.**

Templates you copy/fill live in `templates/`. Read each when the phase that uses it begins.

## Design decisions baked into this skill

Settled with the user; honor them unless the user overrides at runtime.

- **Hybrid wiki integration.** Capture fast in the lightweight store, but confirmed **rules are promoted into proper wiki pages** so the wiki stays the single source of truth for validated knowledge (per the repo's Wiki-First Mandate). The store is the working layer; the wiki is the durable layer.
- **Store lives inside the wiki vault** at `wiki/knowledge/` (falls back to `./knowledge/` only if no `wiki/` exists). This means `/wiki:query`, `/wiki:lint`, and `/wiki:status` already see it and its cross-references resolve.
- **The loop persists via CLAUDE.md + a SessionStart hook.** `init` writes the loop mandate into the project `CLAUDE.md` (inside managed sentinels) and installs a SessionStart hook that surfaces the active rules for the launch domain — so "before/after every task" actually fires without the user invoking anything.
- **A subcommand suite, not one command.** `/knowledge:init | :review | :extract | :promote | :audit`, mirroring the `/wiki`, `/bun`, and `/disclosure` suites.
- **Evidence or it doesn't count.** Every confirmation and contradiction must cite a *distinct*, dated, linkable source (a meeting page, a commit, a task, a transcript). The same source can never increment a counter twice. This is what makes "apply by default" safe.
- **Idempotent + non-destructive.** Generated blocks in `CLAUDE.md` and the hook sit between `<!-- knowledge-loop:managed -->` … `<!-- /knowledge-loop:managed -->` sentinels. Re-runs update only the managed block. Store entries are append/transition, never silently rewritten.

## The store layout

```
wiki/knowledge/
├─ INDEX.md                # router: every domain, with live counts + promotion candidates (type: knowledge, layer: index)
├─ _schema.md             # the contract: the three layers, frontmatter, promotion/demotion rules
└─ <domain>/              # one folder per domain — pricing, onboarding, competitors, …
   ├─ knowledge.md        # facts & observed patterns           (layer: facts)
   ├─ hypotheses.md       # candidate rules — need more data     (layer: hypotheses)
   └─ rules.md            # confirmed — APPLY BY DEFAULT         (layer: rules)
```

Every file carries wiki-compatible YAML frontmatter with `type: knowledge` and a `layer:` discriminator, plus `domain`, `status`, `created`, `updated`, `related`, and `tags`, so the wiki tooling treats them as first-class pages. See `templates/_schema.md` for the canonical frontmatter and entry formats.

The three layers map to increasing confidence:

| Layer | File | Meaning | Action |
|-------|------|---------|--------|
| **Facts** | `knowledge.md` | Observed facts and patterns | Reference; raw material for hypotheses |
| **Hypotheses** | `hypotheses.md` | Candidate rules, not yet trusted | Test on touch; increment on evidence |
| **Rules** | `rules.md` | Confirmed (≥3 distinct confirmations) | **Apply by default** unless contradicted |

## Modes

Pick the mode from `$ARGUMENTS` (`mode:` / first token), else infer: an empty store → `init`; "before we start / what do we know" → `review`; "we just learned / wrap up / capture" → `extract`; "promote / demote / push to wiki" → `promote`; "health / stale / candidates" → `audit`.

### Mode: `init`

Stand up the loop end-to-end. Idempotent.

1. **Locate the store.** Resolve `path` (default `wiki/knowledge/` if a `wiki/` vault exists, else `./knowledge/`). If a `wiki/` vault exists, read `wiki/_schema/SCHEMA.md` and `wiki/_index.md` first so the store conforms and links in.
2. **Discover domains.** Don't hardcode. Propose an initial domain set from the repo and wiki (e.g., existing `wiki/clients/*`, `wiki/platforms/*`, README topics) and confirm with the user via `AskUserQuestion`. Seeding zero domains is fine — the store grows on first `extract`.
3. **Scaffold.** Create `INDEX.md` and `_schema.md` from `templates/`, then a folder per confirmed domain, each with `knowledge.md`, `hypotheses.md`, `rules.md` from templates (empty entry sections, valid frontmatter).
4. **Install the mandate.** Merge the loop mandate into the project `CLAUDE.md` between `<!-- knowledge-loop:managed -->` sentinels — the before/after-task rules, the 3+ promotion / contradiction-demotion rules, and the command table. Preserve all existing content. If the repo already has a Wiki-First Mandate, place the loop as a subsection that *reinforces* it (rules point at wiki pages).
5. **Install the SessionStart hook.** Write `templates/sessionstart-knowledge-hook.sh` to `.claude/hooks/knowledge-context.sh`, make it executable, fill its domain→rules map, and register it in `.claude/settings.json` under `hooks.SessionStart` (merge, don't overwrite). The hook prints the active rules for the launch domain so the agent reviews them before the first prompt.
6. **Register with the wiki.** Append a creation entry to `wiki/_log.md` and add a "Knowledge Loop" section to `wiki/_index.md` pointing at `knowledge/INDEX.md`.
7. **Report.** Counts created, mandate + hook installed, and the next commands to run.

### Mode: `review` — *before a task*

1. **Resolve domain(s).** Use `domain` if given, else infer from the task description and match against `INDEX.md`.
2. **Load and present.** Read that domain's `rules.md` and `hypotheses.md`. Output two short lists: **Rules in effect** (these apply by default to the work that follows) and **Testable hypotheses** — hypotheses whose `applies-when` scope matches the task, flagged so today's work can confirm or contradict them.
3. **Flag conflicts.** If a rule and the task's apparent intent disagree, surface it now (the rule may be due for demotion).
4. Keep it tight — this runs at the *start* of work, so it is orientation, not a report.

### Mode: `extract` — *after a task*

Read `references/loop-algorithm.md` first. Then:

1. **Harvest insights** from what just happened (the conversation, diffs, meeting/transcript, results). For each, decide its layer: a discrete observation → **fact**; a candidate generalization → **hypothesis**; direct evidence for/against an existing hypothesis or rule → a **counter increment**.
2. **Write facts** to `knowledge.md` with source + date.
3. **Update hypotheses.** For a new generalization, open a hypothesis with `confirmations: 1`. For evidence supporting an existing one, add a dated, linked evidence bullet and increment `confirmations` — but only if the source is *distinct* from every source already logged on that entry (counter-integrity guard). Evidence against increments `contradictions`.
4. **Auto-promote.** Any hypothesis reaching the promotion bar (default: `confirmations ≥ 3` from distinct sources **and** `contradictions = 0`) moves to `rules.md`, stamped `promoted-on`, evidence trail intact. Note promotion in the run summary and recommend `/knowledge:promote` to bridge it to a wiki page.
5. **Auto-demote.** Any rule contradicted by new evidence moves back to `hypotheses.md` with `status: demoted`, the contradicting source recorded, and `confirmations`/`contradictions` carried over. If it has a bridged wiki page, mark that page `status: revisited` and log it.
6. **Update counts** in `INDEX.md`, append a one-line entry to `wiki/_log.md`, and keep `related:` links bidirectional.

### Mode: `promote` — *the wiki bridge*

1. **Find candidates.** List rules in `rules.md` not yet linked to a wiki page (`wiki-page:` empty), plus any the user named explicitly. Also accept manual `--demote <id>` to push a rule back to hypothesis.
2. **Promote to the wiki.** For each rule, create/update a proper wiki page. Default mapping: an **ADR-style `type: decision` page** (status `approved`, `decision-status` set appropriately) because a confirmed rule is a standing "always do X" decision and `decision` is a lint-valid type. Choose the location by domain (a client → that client's `decisions/`; otherwise `wiki/verndale/playbooks/`). Confirm location/type with `AskUserQuestion` on the first promotion of a run.
3. **Cross-link.** Set the rule's `wiki-page:` to the new page and add the rule entry to the wiki page's `related:`. Bidirectional, per the repo's cross-reference rule.
4. **Log + index.** Append to `wiki/_log.md`; add the new page to `wiki/_index.md`.

### Mode: `audit` — *health check*

Read every domain and report: entry counts per layer; **promotion candidates** (hypotheses at or near the bar); **stale hypotheses** (no new evidence in N days — default 30); **contradiction hotspots** (rules with `contradictions > 0`, hypotheses with confirmations and contradictions both high); **integrity violations** (a counter incremented twice by the same source, or a count that disagrees with its evidence bullets); **bridge gaps** (rules with no `wiki-page:`); and **broken `[[links]]`/`related:`**. Output a prioritized fix list. Read-only unless the user asks for `--fix`.

## Wiki-first compatibility

- The store lives *in* the vault, so it is not "analysis output existing only in raw sources" — it is wiki content.
- Confirmed rules are **promoted to proper wiki pages**, satisfying the mandate that validated knowledge become wiki pages.
- `review` reads rules whose evidence links into wiki meetings/decisions; `extract` writes into the vault; `promote` pushes to the wiki proper. The loop *feeds* the wiki rather than competing with it.
- Always honor the host repo's `CLAUDE.md`: query the wiki first, never modify raw sources, keep cross-references intact, log every operation to `wiki/_log.md`.

## Output discipline

`review` is orientation (short). `extract`/`promote`/`audit` end with a compact summary: what moved between layers, what got promoted/demoted, counts touched, and the single next action. Never rewrite a user's hand-written CLAUDE.md outside the managed block.
