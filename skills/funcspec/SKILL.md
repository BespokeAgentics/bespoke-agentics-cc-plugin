---
name: funcspec
description: >-
  Evaluate a Storybook's pages and composites page-by-page to infer the functionality
  the UI implies, validate the findings against the user's intent via structured
  interviews, and synthesize a full implementation plan (frontend wiring, full-stack
  surface, backlog-ready epics/stories, gap & ambiguity register). Companion to
  design-zip-to-library: that skill recovers the visual layer; this one extracts the
  functional layer. Use when the user says "what does this UI need to do", "evaluate
  the pages", "turn this storybook into an implementation plan", "functional spec from
  the prototype", "what backend does this design imply", "plan the build from these
  screens", or invokes /bespokeagentics:funcspec-evaluate or
  /bespokeagentics:funcspec-plan. Works on any Storybook workspace; uses a
  design-zip-to-library analysis.json as a fast path when present. Runs in ultracode
  mode: page evaluation and deliverable drafting fan out across parallel subagents.
---

**Invocation.** The user points you at a Storybook workspace (often the output of
`design-zip-to-library`) and optionally passes flags, e.g.
`/bespokeagentics:funcspec-evaluate ./foundry-workspace --visual off`. Parse the
workspace path and `--flag value` tokens. If no path is given, look for a workspace in
CWD (a `apps/storybook` + `packages/ui` layout, or any `.storybook/` directory); if
none, ask.

You turn **static pages into a validated implementation plan**. The pages prove what the
app looks like; your job is to determine what it must *do* — then confirm every inference
with the user before it becomes a commitment. Two AskUserQuestion interviews bracket the
analysis: Stage-1 frames it, Stage-2 validates it. Nothing enters the plan unvalidated.

## Configuration (flags)

| Flag | Default | Options | Effect |
|------|---------|---------|--------|
| `--pages` | `all` | `all`, comma-list | Which pages to evaluate. Composites are always evaluated. |
| `--visual` | `auto` | `auto`, `on`, `off` | Visual verification pass. `auto` = run if a browser tool is available and Storybook boots. |
| `--out` | `<workspace>/docs/funcspec` | any path | Where profiles and deliverables are written. |
| `--push` | `ask` | `ask`, `none` | Whether to offer pushing the backlog/plan to connected Jira/Confluence/Linear MCPs at the end. |

## The pipeline

Phases 0–4 are `funcspec-evaluate`; Phases 5–7 are `funcspec-plan` (which runs 0–4
first if no profiles exist). State lives in `--out` so the two commands can run in
separate sessions.

**Ultracode orchestration.** Per-page evaluation (Phase 2) and deliverable drafting
(Phase 6) fan out fully — one subagent per page, one per document, dispatched
simultaneously. The main thread keeps everything that requires global judgment or the
user: inventory confirmation, both interviews, visual verification, synthesis, and the
final consistency/verification gates. The written state files (`context.md`, profiles,
`synthesis.json`) are the contracts that make the fan-out safe.

### Phase 0 — Preflight & inventory

1. Resolve the workspace. **Fast path:** if a `design-zip-to-library` manifest exists
   (`analysis.json` — check `<workspace>/`, `<workspace>/../`, and the `_src` work dir),
   read `screens`, the component inventory, and `files_by_role` from it — that's your
   page list with props already typed. **Generic path:** glob `**/*.stories.@(tsx|ts|jsx|svelte)`,
   classify stories grouped under `Pages/` (or full-viewport `layout: 'fullscreen'`
   stories) as pages, `Composites/` (Shell/Sidebar/TopBar-style) as composites; resolve
   each story to the component source it renders.
2. Write `<out>/page-inventory.json`: `{ pages: [{id, title, source_path, story_id}],
   composites: [...], mock_data_modules: [...], fast_path: bool }`.
3. Report the inventory to the user (count + list) before burning analysis effort on
   the wrong target.

### Phase 1 — Stage-1 interview (frame the analysis)

Use **AskUserQuestion** (max 4 questions per call; 1–2 calls). Read
`references/interview-protocol.md` for the question bank. Must establish: app purpose
& domain, primary user roles, backend reality (greenfield / existing API / BaaS),
auth model, explicit non-goals, integration targets. Write the digest to
`<out>/context.md` — every evaluator agent receives it verbatim. If the user already
supplied this in conversation, confirm rather than re-ask.

### Phase 2 — Page-by-page evaluation (parallel agents)

1. **Composites first, sequentially** — Shell/Sidebar/TopBar profiles carry the route
   map, auth surface, and tenancy cues that pages inherit.
2. **Then ALL pages simultaneously** — full fan-out, one `page-evaluator` agent per
   page, dispatched in a single multi-Agent message (no batch cap; the composite
   profiles being done is the only prerequisite). Each agent gets: page id/path/kind,
   schema path (`assets/templates/page-profile.schema.json`), playbook path
   (`references/evaluation-playbook.md`), the Stage-1 context digest, relevant mock-data
   and composite-profile paths, and `output_path: <out>/profiles/<page-id>.json`.
   Evaluators are read-only and write to disjoint profile paths, so they cannot collide.
3. As profiles land, validate each against the schema (`python3 -c` with
   `json.load` + required-key check is enough; no dependency needed). Re-run failures
   once with the validation error in the prompt; if still failing, evaluate that page
   in the main thread.

### Phase 3 — Visual verification (default on, degrades gracefully)

Skip when `--visual off`, no browser tool is available, or Storybook won't boot —
note the skip in the report; code analysis stands alone. Otherwise follow
`references/visual-verification.md`: boot Storybook (`bun --filter '*storybook*'
storybook` or `bunx storybook dev`), walk each page story, screenshot, and
confirm/extend profiles with visual-only findings (`source: "visual"`, upgrades to
`"both"`). Set `visual_verified: true` on covered profiles.

### Phase 4 — Cross-page synthesis

Follow `references/synthesis.md`. Merge the profiles in the main thread into
`<out>/synthesis.json` + a human-readable draft:

- **Entity model** — merge same-named entities across pages; union fields; reconcile
  type conflicts (conflicts become ambiguities).
- **Route map** — composite navigation + page navigation, joined.
- **Feature inventory** — cluster affordances/operations into named features grouped by
  functional domain; every feature lists its source pages (traceability).
- **Shared services** — cross-cutting requirements seen on ≥2 pages (auth, search,
  notifications, realtime, export, audit).
- **Consolidated ambiguity register** — dedupe across pages; order by `blocking`, then
  by how many pages each touches.

Report headline numbers (pages, features, entities, operations, open ambiguities) and
stop here if running as `funcspec-evaluate`.

### Phase 5 — Stage-2 interview (validate everything)

The alignment gate. Use AskUserQuestion in batches (≤4 questions per call) per
`references/interview-protocol.md`:

1. **Confirm features per domain** — present each domain's inferred features; user
   confirms / corrects / cuts (multiSelect for "which of these are real requirements").
2. **Resolve ambiguities** — blocking first, register `resolution` on each; the user may
   defer non-blocking ones (they stay ⚪ in the gap register).
3. **Prioritize** — P0/P1/P2 per feature and any phasing constraints.

Update profiles and `synthesis.json` in place with resolutions and priorities. Do not
proceed with open *blocking* ambiguities — ask, or get explicit permission to defer.

### Phase 6 — Deliverables (parallel drafting)

Only after Stage-2 is complete — drafting from unvalidated synthesis is the one
parallelism shortcut this skill forbids. Dispatch four `deliverable-writer` agents
**simultaneously**, one per document, each with its `references/deliverables.md`
section, its template from `assets/templates/`, and the validated state
(`synthesis.json`, `profiles/`, `context.md`):

| File | Contents |
|------|----------|
| `functional-spec.md` | Per-page profiles, human-readable, with evidence |
| `implementation-plan.md` | Frontend wiring (state, routing, data-fetching contracts, validation) + full-stack surface (API endpoints, data model, auth boundaries), phased by the Stage-2 priorities |
| `backlog.md` | Epics → user stories with acceptance criteria, sequenced, each story traceable to page + affordance ids |
| `gap-register.md` | Every gap/decision with 🟢 OOTB · 🔵 Config · 🟡 Custom Dev · 🔴 Gap · ⚪ TBD · 🟣 3rd Party status |

`traceability.md` (page → feature → story matrix) is generated **main-thread** from the
synthesis id arrays after the writers return — it's mechanical, and it doubles as the
first consistency probe over the four drafts. Then run the **cross-document check**:
ids join across documents (every backlog `Traces:` id exists in synthesis; every
gap-register row maps to a deferred/resolved ambiguity or flagged state; priorities in
the plan's phasing match the backlog's epic tags), and writer FLAGS are triaged —
fix in synthesis and re-render the affected document, don't hand-patch drift.

### Phase 7 — Wiki, integrations & verification

1. **Wiki-first mandate:** if the repo has a `wiki/` vault, ingest the deliverables
   (`/wiki:ingest-document` per file, type `spec`), add cross-references, and log to
   `wiki/_log.md`. Skip silently if no wiki.
2. **Push offers** (`--push ask`): detect connected Atlassian/Linear MCP tools. If
   present, *offer* — never auto-push — epics/stories → Jira/Linear, plan → Confluence.
3. **Verification pass** before handoff: every story traces to ≥1 affordance id; every
   blocking ambiguity is resolved; every deferred ambiguity appears in the gap register
   as ⚪; profiles are schema-valid; no feature lacks a priority. Report failures
   honestly — an unverified plan is a draft, say so.
4. Summarize: pages evaluated (and how many visually verified), features confirmed/cut,
   ambiguities resolved/deferred, deliverable paths, push actions taken.

## Reference map

Read as the phase calls for them — don't preload.

| Need | Read |
|------|------|
| Affordance → behavior inference taxonomy (the evaluator's core) | `references/evaluation-playbook.md` |
| Stage-1/Stage-2 question banks, batching, answer → requirement deltas | `references/interview-protocol.md` |
| Entity merge, feature clustering, traceability construction | `references/synthesis.md` |
| Deliverable format contracts | `references/deliverables.md` |
| Booting Storybook, walking stories, screenshot workflow, graceful skip | `references/visual-verification.md` |
| The profile contract | `assets/templates/page-profile.schema.json` |

## Principles

- **Evidence or ambiguity.** Every behavior in the plan traces to an element on a page
  or an interview answer. No silent invention — two readings means ask, not pick.
- **The user's intent outranks the inference.** The UI suggests; the interviews decide.
  Stage-2 is a gate, not a courtesy.
- **Composites first.** The shell carries the route map and auth surface; evaluate it
  before the pages that live inside it.
- **Parallel where mechanical, main-thread where judgment.** Per-page extraction and
  per-document drafting fan out fully; synthesis, interviews, and the consistency
  gates do not. Validated written state is what makes the fan-out safe.
- **Degrade gracefully.** No browser, no Storybook boot, no wiki, no Jira — each is a
  noted skip, never a failure.
- **Report honestly.** Open blocking ambiguities or failed verification = draft plan,
  labeled as such.
