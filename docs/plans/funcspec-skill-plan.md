# funcspec — Storybook Functional Analysis & Implementation Planning

Design plan for the skill/agent/command set that complements `design-zip-to-library`.
That skill recovers the **visual layer**; `funcspec` infers the **functional layer** —
what the UI implies the app must do — validates it against the user's intent via
interviews, and emits a full implementation plan.

## Decisions (locked via interview, 2026-06-07)

| Decision | Choice |
|----------|--------|
| Analysis mode | Code-first (page source = ground truth), visual verification via running Storybook when feasible |
| Interview flow | Two-stage: upfront context interview + post-analysis validation interview (AskUserQuestion) |
| Plan scope | Frontend wiring + full-stack surface + backlog-ready epics/stories + gap & ambiguity register |
| Packaging | New sibling skill + namespaced commands + page-evaluator subagent |
| Namespace | `bespoke-agentics:` (plugin namespace) — skill invoked as `/bespoke-agentics:funcspec`, commands as `/bespoke-agentics:funcspec-*` |
| Integrations | Files always; detect Atlassian/Linear MCPs and *offer* push (Jira issues, Confluence page) |
| Input scope | Any Storybook workspace; `analysis.json` from design-zip-to-library used as fast path when present |

## New plugin components

```
bespoke-agentics-plugin/
├─ skills/funcspec/
│  ├─ SKILL.md                          # orchestrator (pipeline below)
│  ├─ references/
│  │  ├─ evaluation-playbook.md         # affordance → behavior inference taxonomy
│  │  ├─ interview-protocol.md          # stage-1/stage-2 question banks, batching rules
│  │  ├─ synthesis.md                   # entity merge, feature dedup, traceability matrix
│  │  ├─ deliverables.md                # format contracts for the 5 outputs
│  │  └─ visual-verification.md         # boot Storybook, walk stories, screenshot, degrade gracefully
│  ├─ assets/templates/
│  │  ├─ page-profile.schema.json       # THE inter-agent contract (see below)
│  │  ├─ functional-spec.md             # skeletons for each deliverable
│  │  ├─ implementation-plan.md
│  │  ├─ backlog.md
│  │  └─ gap-register.md
│  └─ evals/evals.json
├─ agents/
│  └─ page-evaluator.md                 # parallel per-page analysis subagent
└─ commands/
   ├─ funcspec-evaluate.md              # /bespoke-agentics:funcspec-evaluate
   ├─ funcspec-plan.md                  # /bespoke-agentics:funcspec-plan
   └─ funcspec-status.md                # /bespoke-agentics:funcspec-status
```

Flat command files (no subdirectory) so the plugin's own namespace carries them:
installed as the `bespoke-agentics` plugin, they surface as `/bespoke-agentics:funcspec-*`,
matching how `/bespoke-agentics:ai-waiting-ux` resolves today.

## Commands

| Command | Does |
|---------|------|
| `/bespoke-agentics:funcspec-evaluate [<workspace>] [--pages a,b] [--visual on\|off]` | Phases 0–4: inventory → stage-1 interview → per-page evaluation → visual verify → synthesis. Writes page profiles + draft feature inventory. |
| `/bespoke-agentics:funcspec-plan [--push jira\|confluence\|none]` | Phases 5–7: stage-2 validation interview → deliverables → wiki ingest + push offers. Runs `evaluate` first if no profiles exist. |
| `/bespoke-agentics:funcspec-status` | Show evaluation state: pages profiled, ambiguities open/resolved, deliverables generated. |

## Pipeline (SKILL.md)

**Phase 0 — Preflight.** Resolve workspace path. Fast path: if `analysis.json`
(design-zip-to-library manifest) exists, take `screens`, component inventory, and props
from it. Else scan: `*.stories.tsx` globs, `Pages/` story group, composites. Emit
`docs/funcspec/page-inventory.json`.

**Phase 1 — Stage-1 interview (AskUserQuestion).** Frame the analysis before reading a
line of page code: app purpose & domain, primary user roles, backend reality
(greenfield / existing API / BaaS), auth model, explicit non-goals, integration targets.
≤4 questions per call; batch into 1–2 calls. Answers become the **analysis context**
passed to every evaluator agent.

**Phase 2 — Page-by-page evaluation (parallel subagents).** Launch `page-evaluator`
agents in batches (one per page/composite). Each reads the page source + relevant
primitives + mock data and returns a **Page Functional Profile** conforming to
`page-profile.schema.json`:

- `affordances[]` — element → implied behavior (button verb → mutation, table → list/sort/filter/paginate, form → create/update + validation rules, badge → status enum, search → query endpoint, tabs → view state, empty/error states implied)
- `entities[]` — data objects + fields inferred from props and mock data shapes
- `operations[]` — implied API surface (method, resource, trigger, payload sketch)
- `navigation[]` — route/transition cues
- `roles[]` — permission/visibility cues
- `ambiguities[]` — anything with two plausible readings, pre-tagged ⚪/🔴

**Phase 3 — Visual verification (default on, degrades gracefully).** Boot Storybook
(`bun --filter @<scope>/storybook storybook`), walk each page story with browser tools,
screenshot, and let the evaluator confirm/extend profiles with visual-only cues
(affordances invisible in code, layout-implied hierarchy, disabled/loading states).
Headless or no-browser → skip with a note; code analysis stands alone.

**Phase 4 — Cross-page synthesis (main thread).** Merge per-page profiles into:
unified entity model, route map, shared services (auth, notifications, search),
feature inventory with **page → feature traceability**, consolidated ambiguity register.

**Phase 5 — Stage-2 validation interview (AskUserQuestion).** Present inferred features
per functional domain; confirm/correct each, resolve every register ambiguity (or
explicitly defer it), capture priorities (P0/P1/P2) and phasing constraints. This is the
alignment gate the user asked for — nothing enters the plan unvalidated.

**Phase 6 — Deliverables → `<workspace>/docs/funcspec/`:**

| File | Contents |
|------|----------|
| `functional-spec.md` | Per-page profiles, human-readable |
| `implementation-plan.md` | Frontend wiring (state mgmt, routing, data-fetching contracts, validation) + full-stack surface (API endpoints, data models, auth boundaries), phased |
| `backlog.md` | Epics → user stories with acceptance criteria, sequenced, traceable to pages |
| `gap-register.md` | 🟢 OOTB · 🔵 Config · 🟡 Custom Dev · 🔴 Gap · ⚪ TBD · 🟣 3rd Party |
| `traceability.md` | Page → feature → story matrix |

**Phase 7 — Wiki + integrations.** If `wiki/` exists, ingest deliverables per the
wiki-first mandate (`/wiki:ingest-document`, log entry, cross-refs). Detect connected
Atlassian/Linear MCPs and **offer** (never auto-push): epics/stories → Jira, plan →
Confluence.

**Verification step.** Lightweight QA pass before handoff: every story traces to a page
affordance, every ambiguity resolved or registered, schema-valid profiles, no orphan
features.

## Agent: `page-evaluator`

Single focused subagent; parallelizable because the Page Functional Profile schema is
the contract. Input: one page path + analysis context + token/component references.
Tools: Read/Glob/Grep (+ browser tools only in visual mode). Output: schema-valid JSON +
short prose summary. No user interaction — ambiguities are *recorded*, not asked;
interviewing is the orchestrator's job (keeps AskUserQuestion in the main thread where
it works).

## Integration edits (existing files)

1. `skills/claude-design-to-app-workflow/SKILL.md` Phase 8: add handoff line — "Offer
   `/bespoke-agentics:funcspec-evaluate <workspace>` to turn the rebuilt pages into an
   implementation plan."
2. Root `CLAUDE.md`: add "When to Use Each Funcspec Command" table + plugin-structure entries.

## Build order

1. `page-profile.schema.json` + `evaluation-playbook.md` (the contract everything else consumes)
2. `agents/page-evaluator.md`
3. `skills/funcspec/SKILL.md` (pipeline)
4. Commands (`evaluate`, `plan`, `status`)
5. Remaining references + deliverable templates
6. Integration edits (CLAUDE.md, existing skill handoff)
7. `evals/evals.json` test cases
