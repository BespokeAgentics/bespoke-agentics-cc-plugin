# Deliverables — Format Contracts

Phase 6 writes five files to `<out>/`. Skeletons live in `assets/templates/` — copy and
fill; keep the section structure so downstream tooling (wiki ingest, Jira push) can
parse them. Only validated content enters: confirmed features, resolved or explicitly
deferred ambiguities.

**Parallel drafting (ultracode):** files 1–4 are drafted simultaneously by one
`deliverable-writer` agent each; every agent receives only its own section of this
document plus its template. That makes these contracts load-bearing: ids must be used
verbatim from `synthesis.json` (the cross-document check joins on them), and section
structure must match the template exactly. File 5 (`traceability.md`) is generated
main-thread after the writers return.

## 1. functional-spec.md

Human-readable rendering of the profiles. Frontmatter: `type: spec`, `status: draft|final`,
`date`, `source: funcspec`. Sections:

- **Overview** — purpose, users/roles, backend reality (from `context.md`).
- **Per page** (one H2 per page, composites first): summary, user goals, affordance
  table (`Element | Behavior | Confidence | Evidence`), entities touched, operations,
  navigation, states (flag `implied but not designed`), roles.
- **Explicitly out of scope** — cut features + Stage-1 non-goals.

Audience: anyone asking "what does this app do?". No implementation detail here.

## 2. implementation-plan.md

The engineering document. Sections:

- **Architecture summary** — frontend stack (from the workspace), backend approach
  (from Stage-1), auth model, the 2–4 biggest technical decisions with rationale.
- **Data model** — merged entities: field tables, relations, enums (exact values),
  open conflicts (link to gap register).
- **API surface** — operations grouped by entity: `Method path — intent — request/response
  sketch — auth — consuming pages`. For an existing-API backend, add a "mapping" column.
- **Frontend wiring** (per page): state management needs (server state vs local vs URL
  state — filters/pagination belong in the URL), data-fetching contracts (which
  operations, when), form validation rules, optimistic-update / invalidation notes,
  states to implement (from the profile's `states`).
- **Shared services** — one subsection each: requirement, suggested approach, build-vs-buy
  note (🟣 candidates).
- **Phasing** — P0/P1/P2 from Stage-2; each phase lists features + a "demonstrable
  outcome" (what a stakeholder can click through at phase end).

## 3. backlog.md

Epics and stories, paste-ready for Jira/Linear (and the source for MCP push).

- **Epic** = feature (or shared service). Heading: `## EPIC: <name> [P0] (feature-id)`.
  One-paragraph description + source pages.
- **Story** format:

```
### <epic-shortcode>-<n>: <verb phrase>
As a <role>, I want <capability>, so that <outcome>.
Acceptance criteria:
- [ ] <observable behavior — Given/When/Then where it clarifies>
- [ ] <states covered: loading/empty/error as applicable>
Traces: <page-id>/<aff-id>, <page-id>/<op-id>
Estimate: S | M | L
```

- Sequence stories within an epic by dependency (data model → API → wiring → polish).
- Sizing: S = wiring an existing component to a contract; M = new flow or service
  touchpoint; L = shared service or cross-page concern. No hour estimates — relative only.
- Cross-epic dependencies: explicit `Blocked by:` lines.

## 4. gap-register.md

Table, one row per gap/decision:

| ID | Item | Status | Pages | Decision/Note | Owner |
|----|------|--------|-------|---------------|-------|

Status colors (defined enums only): 🟢 OOTB · 🔵 Config · 🟡 Custom Dev · 🔴 Gap ·
⚪ TBD · 🟣 3rd Party.

Sources: deferred ambiguities (⚪), blocking-deferred (🔴 + "BLOCKED" note), states
implied-but-not-designed (usually 🟡), nav targets without pages (🔴), entity type
conflicts unresolved (⚪), build-vs-buy candidates (🟣). Group by status, 🔴 first.

## 5. traceability.md

Generated mechanically from synthesis id arrays — do not hand-edit:

- **Page → features** table.
- **Feature → stories** table.
- **Orphan check** appendix: affordances with operations that reached no story
  (must be empty to pass verification; if not empty, say so here AND in the closing report).

## Wiki ingestion notes (Phase 7)

When a `wiki/` vault exists: each deliverable becomes a wiki page via
`/wiki:ingest-document '<client>' '<out>/<file>' 'spec'`; add `related:` links between
the five pages and to the client's hub page; log one entry in `wiki/_log.md` covering
the batch. Raw deliverables in `<out>/` are the immutable sources — corrections happen
in the wiki layer, per the wiki-first mandate.
