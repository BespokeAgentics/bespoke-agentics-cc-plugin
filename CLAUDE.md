# Bespoke Agentics — Plugin Instructions

## Response Style

Responses to the user should be brief and specific to the request. Do not provide too much explanation. The user can request additional information if needed.

## Operating Manual (read first)

Every agent operating in this repository is governed by [`OPERATING-MANUAL.md`](OPERATING-MANUAL.md) — the working method for all responses: read the intent beneath the request, decompose into independently checkable pieces, spend verification where errors are expensive, re-derive every fact and figure passing through you, label guesses inline, attack your own conclusion, and lead with the answer. It applies to every task, then the domain-specific rules below apply on top. When a rule there conflicts with a request's phrasing, the rule that protects correctness wins.

## Wiki-First Mandate

When a project has a wiki (at `wiki/` or configured via `/wiki:init`), the wiki is the **single source of truth** for all project intelligence, technical decisions, and business capabilities. Every agent operating in this repository MUST use the wiki as its primary knowledge layer.

### Core Rules

1. **Query the wiki before answering any project question.** Do not rely on memory or general knowledge when wiki pages exist. Run `/wiki:query` or read the relevant wiki pages directly. The wiki contains synthesized, cross-referenced, and validated knowledge that supersedes raw outputs.

2. **Update the wiki after every content-producing operation.** When a meeting is analyzed, a document is ingested, a decision is made, or a gap is identified — the wiki MUST be updated. No analysis output should exist only in raw source directories without a corresponding wiki page. Use `/wiki:ingest-meeting` or `/wiki:ingest-document` to route new content into the wiki.

3. **Never modify raw sources.** Raw pipeline outputs, transcripts, and exports are immutable. The wiki references them but never edits them. If a raw source contains an error, note the correction in the wiki page and link back to the original.

4. **Maintain cross-references.** Every wiki page must link to related pages via `[[wiki-links]]` and `related:` frontmatter. When creating or updating a page, check for and add bidirectional links.

5. **Follow the schema.** All wiki pages must conform to `wiki/_schema/SCHEMA.md`. Use the templates in `wiki/_schema/templates/` for new pages. Every page requires valid YAML frontmatter with the correct `type` field.

6. **Log everything.** Every ingest, lint, scaffold, or maintenance operation must be recorded in `wiki/_log.md`. This is the audit trail.

### When to Use Each Wiki Command

| Situation                                       | Command                                                   |
| ----------------------------------------------- | --------------------------------------------------------- |
| Starting a brand-new wiki vault                 | `/wiki:init`                                              |
| Adding a new client/project workspace           | `/wiki:new-client '<name>' '<platform>'`                  |
| After analyzing a meeting or recording          | `/wiki:ingest-meeting '<name>' '<meeting-dir>' '<label>'` |
| Received an email, spec, RFP, or other document | `/wiki:ingest-document '<name>' '<path>' '<type>'`        |
| Someone asks a question about the project       | `/wiki:query '<question>' --client <slug>`                |
| Weekly maintenance or health check              | `/wiki:lint --scope full`                                 |
| Checking wiki statistics                        | `/wiki:status`                                            |
| Syncing with Confluence                         | Use the `wiki-confluence-reconcile` skill                 |

### When to Use Each Glean Command

| Situation                                                       | Command                                                                |
| --------------------------------------------------------------- | ---------------------------------------------------------------------- |
| Bootstrap a new Glean Agent Toolkit project (Python)            | `/glean:init`                                                          |
| Add a custom `@tool_spec` tool to an existing project           | `/glean:add-tool '<name>' --description '<text>' --params '<n:t,...>'` |
| Wire an additional framework adapter (OpenAI / LangChain / ADK) | `/glean:add-adapter --framework <name>`                                |
| Diagnose a broken Glean agent setup                             | `/glean:doctor` (add `--probe` for a live API ping)                    |

### When to Use Each Bun Workspace Command

| Situation                                                                                      | Command                                                         |
| ---------------------------------------------------------------------------------------------- | --------------------------------------------------------------- |
| Inspect a directory of sibling projects, see what a monorepo migration would look like         | `/bun:analyze [<dir>]`                                          |
| Execute the migration into a Bun workspace (interactive, reversible)                           | `/bun:convert [<dir>] [--layout flat\|buckets] [--scope @org]`  |
| Health-check an existing Bun workspace for drift, nested lockfiles, missing tsconfig extension | `/bun:audit [<dir>] [--fix]`                                    |
| Scaffold a new package into an existing Bun workspace                                          | `/bun:add <package-path> [--name <name>] [--kind library\|app]` |

The Bun Workspace skill manages the _workspace/dependency_ layer; pair it with `/submodule:*` when you also want to pin children at the git layer.

### When to Use Each Progressive Disclosure Command

| Situation                                                                                             | Command                                                                   |
| ----------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------- |
| Set up a layered CLAUDE.md/AGENTS.md context layer across a project or monorepo                       | `/disclosure:map [<root>] [--depth subsystem\|diverge\|deep] [--no-wiki]` |
| Read-only health check of an existing context layer (coverage, drift, broken pointers, settings gaps) | `/disclosure:audit [<root>]`                                              |
| Keep memory files current — update only managed sections, add files for new subsystems                | `/disclosure:refresh [<root>]`                                            |

The Progressive Disclosure skill builds the _context/memory_ layer (per-directory CLAUDE.md is the source of truth; AGENTS.md points to it) plus the supporting `.claude/` config (Read deny rules, `additionalDirectories`, `claudeMdExcludes`, a SessionStart hook, code-intelligence recommendations). It deploys parallel subagents to profile every subsystem and, if a wiki is present, mines it for context and logs the operation. It is complementary to `architect-agents`, which builds the _agent/command_ layer — the two do not overlap.

### When to Use Each Funcspec Command

| Situation                                                                                                              | Command                                                                                    |
| ---------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------ |
| Evaluate a Storybook's pages page-by-page and infer the functionality the UI implies                                   | `/bespoke-agentics:funcspec-evaluate [<workspace>] [--pages a,b] [--visual auto\|on\|off]` |
| Validate findings with the user and generate the implementation plan (spec, plan, backlog, gap register, traceability) | `/bespoke-agentics:funcspec-plan [--push ask\|none]`                                       |
| Check the state of a funcspec run (profiles, ambiguities, deliverables)                                                | `/bespoke-agentics:funcspec-status [<workspace>]`                                          |

The Funcspec skill is the companion to `claude-design-to-app-workflow` (`design-zip-to-library`): that skill recovers the _visual_ layer; `funcspec` extracts the _functional_ layer. It launches parallel `page-evaluator` agents (code-first, with optional visual verification against running Storybook), brackets the analysis with two AskUserQuestion interviews (Stage-1 frames intent, Stage-2 validates every inference), and emits deliverables using the Decision Status Colors below. Works on any Storybook workspace; uses a `design-zip-to-library` `analysis.json` as a fast path when present. Deliverables are wiki-ingested when a vault exists.

### When to Use Each Knowledge Loop Command

| Situation                                                                                            | Command                                                              |
| ---------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------- |
| Stand up the learning loop (scaffold store, install CLAUDE.md mandate + SessionStart hook)           | `/knowledge:init [--path <dir>] [--domains <a,b,c>]`                 |
| Before starting a task — load the rules that apply by default + the hypotheses today's work can test | `/knowledge:review [<task>] [--domain <slug>]`                       |
| After a task — capture insights; auto-promote at 3+ confirmations, auto-demote contradicted rules    | `/knowledge:extract [<what you learned>] [--domain <slug>]`          |
| Bridge confirmed rules into proper wiki pages (or manually promote/demote)                           | `/knowledge:promote [--domain <slug>] [--rule <id>] [--demote <id>]` |
| Health-check the store (promotion candidates, stale entries, integrity, broken links)                | `/knowledge:audit [--domain <slug>] [--stale-days <n>] [--fix]`      |

The Knowledge Loop skill is the project's _learning layer_: a lightweight facts → hypotheses → rules store (one trio per domain) that compounds across tasks. It is **wiki-first compatible by design** — the store lives inside the vault at `wiki/knowledge/` (so `/wiki:query`, `/wiki:lint`, and `/wiki:status` see it), and confirmed rules are **promoted into proper wiki pages**, satisfying the mandate that validated knowledge become wiki content. Evidence is strict: every confirmation/contradiction must cite a distinct, dated, linkable source, so `rules.md` stays trustworthy enough to **apply by default**. `init` writes the before/after-task mandate into `CLAUDE.md` and installs a SessionStart hook that surfaces the active rules, so the loop fires without being invoked. Promotion bar: `confirmations ≥ 3` (distinct) and `contradictions = 0`; a single contradiction demotes a rule back to a hypothesis.

### When to Use Each Project DB Command

| Situation                                                                                        | Command                                            |
| ------------------------------------------------------------------------------------------------ | -------------------------------------------------- |
| Make the wiki (or a no-wiki project's docs + data) queryable with SQL; install hook + mandate     | `/db:init [--mode local\|d1\|both] [--slug <s>]`  |
| Structured question: counts, filters, joins, "what links to X", "which meetings discussed Y"     | `/db:query '<question or SELECT …>'`               |
| Wiki/sources changed, or `views.sql` / `config.json` edited                                      | `/db:sync [--full] [--verify]`                     |
| Publish to Cloudflare D1 and deploy the read-only MCP Worker (modes `d1`, `both`)                | `/db:publish [--dry-run]`                          |

The Project DB skill is the wiki's _query layer_: the wiki stays the record, the database at `.claude/db/project.sqlite` is the index. `init` builds the schema **from** the wiki — base tables (pages, `page_fields`, `links`, `tags`, `sources`, `sections`, `raw_documents`, FTS5) plus one typed view per page type with column docs mined from `_schema/templates/`, and curated views (`open_gaps`, `pending_decisions`, `open_questions`, `backlinks`, `broken_links`, `meeting_mentions`…). It vendors a stdlib-Python engine into `.claude/db/db.py` so the SessionStart hook (incremental sync + banner), the guarded CLI (`db.py query`: read-only authorizer, one statement, 200-row cap, 5 s timeout, CSV, audit log), the local stdio MCP server and the D1 Worker share one policy. Agents read `.claude/db/SCHEMA.md` (generated schema-as-prompt) before writing SQL and promote repeated queries into `.claude/db/views.sql`. With no wiki, `init` interviews + scans the repo, maps sources to collections (`--markdown adr=docs/adr`, `--tabular data/x.csv`) and installs a DB-first mandate that mirrors the Wiki-First Mandate. D1 is SQLite, so one export serves both.

### When to Use Each Project Ontology Command

| Situation                                                                                                   | Command                                                                     |
| ----------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------- |
| Values drift (a client spelled two ways, statuses no template declares); make the vocabulary enforceable    | `/ontology:init [--govern <dir>]`                                           |
| Check pages, the vault, or only what a branch changed against the vocabulary                                | `/ontology:check [<path>\|--all\|--changed-since <ref>]`                   |
| A page genuinely needs a value the vocabulary lacks                                                         | `/ontology:propose <id> --label '…' --definition '…'`                       |
| Decide pending terms (humans only) / retire a term                                                          | `/ontology:approve <id>…` · `/ontology:deprecate <id> --replaced-by <id>`   |
| Rewrite aliases, spelling variants, deprecated values, noncanonical links                                   | `/ontology:apply --dry-run`, then `/ontology:apply`                         |
| Counts, open violations, pending approvals                                                                  | `/ontology:status`                                                          |

The Project Ontology skill is the wiki's _vocabulary layer_. `init` mines what the vault already declares and uses — page types, template `key: # a|b|c` comments, SCHEMA.md value lists, observed values, scope folders, tags, frontmatter link fields — into one declaration, `wiki/_schema/ontology.yaml`, of **dot-notated terms** (`gap.severity.critical`, `client.acme-corp`, `tag.budget-management`, `rel.related-feature`) with a **proposed → approved → deprecated** lifecycle, rendered to `wiki/_schema/ONTOLOGY.md`. **Pages keep plain values** (`severity: critical`); page ids are **derived from paths** (`client.acme.gap.co-op-billing`), never written into pages. Declared values are approved, observed-only values are proposed, spelling variants become proposed aliases — nothing is silently approved — and an interview settles vocabulary conflicts. **One engine** (`.claude/ontology/ontology.py`, stdlib, never PyYAML) enforces it in every place a value can enter or be read: a **PreToolUse hook** reconstructs the post-write file and blocks a Write/Edit that *adds* a strict violation (unregistered, misspelled or deprecated value; broken, ambiguous or noncanonical `[[link]]`; relation target of the wrong type), naming the approved values and the exact propose command — violations already on a page never block (**ratchet**), so a messy vault adopts enforcement on day one; a **PostToolUse hook** reports what still stands; a **Bash guard** turns `approve`/`deprecate`/`init --write` into a permission prompt and blocks shell writes into pages; a guard on `ontology.yaml` rejects agent edits that approve, deprecate, remove, re-spell or loosen anything (**humans own approval**); a **SessionStart banner** keeps counts and rules in context; CI runs `check --changed-since <base>`; **project-db** loads `ontology_terms`, `ontology_aliases`, `ontology_fields`, `ontology_violations` and `pages.ontology_id` at every sync (optional `fail` gate, alias-aware search); **wiki-lint** reports it as Check 8. `apply` rewrites only what has one right answer (aliases, spelling variants, deprecated values with a replacement, uniquely-resolvable links) — every other byte preserved.

### When to Use the Repo Audit Command

| Situation                                                                              | Command                                                                                |
| -------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------- |
| Get an honest, evidence-based health check of a repository with a prioritized fix plan | `/bespoke-agentics:repo-audit [<path>] [--depth quick\|standard\|deep] [--out <file>]` |

The Repo Audit command runs a **read-only**, principal-engineer review in four phases — Discovery & Mapping → evidence-based Audit (every finding severity-rated and `file:line`-cited) → Improvement Strategy → milestone Task Plan — and emits a single graded report (A–F) with a strengths section, flagged quick wins, and open questions. It calibrates rigor to project maturity (`--depth`), prioritizes the core 20% of code that does 80% of the work, and **never modifies anything except the report it writes** (via `--out` or after you accept the save offer). Pair it with `/disclosure:audit` (context-layer health) and the `ux-audit` skill (interface quality) for full-stack coverage.

### When to Use the UI-Issue-to-Plan Command

| Situation                                                                                                           | Command                                                                                                                         |
| ------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------- |
| Turn a narrated screen recording into a code-grounded plan that captures both what to fix AND how to improve the UX | `/bespoke-agentics:ui-issue-to-plan '<video>' [issue-label] [interval] [--mode fix\|improve\|both] [--out <dir>] [--no-ground]` |

The UI-Issue-to-Plan command takes an `.mp4`/`.mov`/`.webm`/`.gif` screencast in which someone narrates a problem, a desired change, or how a flow **should** work better in the UI of the project **open in this session**, and produces an implementation plan in `./plans/`. It treats the video as a **design starting point, not just a bug report**. It reuses the shared video pipeline (`extract-video-frames` → `dedupe-frames` → `elevenlabs-transcribe`), launches parallel `ui-frame-analyst` agents to read the frames + narration and identify the exact UI components referenced (plus the narrator's vision and observed friction), then — the key differentiator from `video-to-deliverables`/`workflow-analyzer` — **grounds every observed component in the real codebase** via parallel `Explore` agents (`file:line` evidence). Unless `--mode fix`, it synthesizes a **curated set of grounded improvement opportunities**. It then runs an **AskUserQuestion** interview that **frames intent** (fix only vs. improve too), confirms each fix, grounds, prioritizes, and lets you **opt into enhancements** — so it elicits what you actually want the flow to become, not just the reported defect. The plan separates **Defect fixes** from **Enhancements (opt-in)**, each prioritized, with on-screen evidence (frame + quote), affected files, a grouped task checklist, deferred opportunities, open questions, and runnable verification. Calibrated so a terse bug video stays lean; degrades gracefully (no `ELEVENLABS_API_KEY` → frames-only + interview; `--no-ground` → video-only). Wiki-ingested when a vault exists. Stops at a validated plan and offers to start the P0 task rather than editing code unprompted.

### When to Use the Highlight Reel Command

| Situation                                                                                                                                          | Command                                                                                                                                                                              |
| -------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Turn a long app-demo screencast into a short, narrated, subtitled highlight video — grounded in this repo so the voiceover is technically accurate | `/bespoke-agentics:highlight-reel '<video>' [reel-label] [interval] [--duration <sec>] [--voice <id>] [--audio duck\|keep\|mute] [--no-subs] [--no-ground] [--no-tts] [--out <dir>]` |

The Highlight Reel command is the **creation** companion to the video-_analysis_ skills: `video-to-deliverables`/`workflow-analyzer`/`ui-issue-to-plan` turn a video into **documents** — this turns a long `.mp4`/`.mov`/`.webm`/`.gif` app-demo screencast into a **new, shorter video**. It reuses the same shared preprocessing pipeline (`extract-video-frames` → `dedupe-frames` → `elevenlabs-transcribe`) and adds the two layers none of the analysis skills have — **TTS narration** (`scripts/tts.py`, the ElevenLabs text-to-speech companion to the transcribe skill's speech-to-text) and **ffmpeg reel assembly** (`scripts/assemble_reel.py`). Parallel frame-analyst agents read the frames + word-timed transcript into a salience-scored **moment catalog** (what happens, when, which feature, how highlight-worthy); parallel `Explore` agents then **ground every demonstrated feature in the real codebase** (`file:line`) so a narration beat may state a _verified_ technical fact ("all four panels come from one query") rather than guess from pixels — narration that can't be grounded stays descriptive, and a repo-mismatch is flagged loudly (unless `--no-ground`). It drafts a ranked cut, then an **AskUserQuestion** interview confirms which moments make it, their order, the target length, the tone/voice, and how to treat the original audio (`duck`/`keep`/`mute`) and captions — **nothing renders before that gate**. It then writes a grounded narration script + `reel-plan.json` (the single-source-of-truth edit-decision list), synthesizes one voiceover clip per beat (unless `--no-tts` → captions-only, no API key needed), and renders: each moment is cut, the voiceover is mixed over the ducked/kept/muted original, any clip shorter than its narration is **freeze-extended** so nothing is cut off, segments are concatenated, and subtitles are burned in (SRT always written as a sidecar). Because `reel-plan.json` drives the render, edits — reword a beat, retime, reorder — are a quick re-run with no re-analysis. Degrades gracefully (no audio → frames-only analysis + interview; no `ELEVENLABS_API_KEY` → captions-only). Wiki-ingested when a vault exists.

### When to Use the Plan-Review Command

| Situation                                                                                                                                                        | Command                                                                                                                                   |
| ---------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------- |
| Pressure-test a written implementation plan, spec, or issue/bug report **before** building it — find the gaps, ambiguities, and risks, grounded in the real code | `/bespoke-agentics:plan-review '<artifact>' [--type plan\|issue\|spec\|auto] [--depth quick\|standard\|deep] [--out <dir>] [--no-ground]` |

The Plan-Review command takes a **local** plan, spec, design doc, or issue/bug-report markdown and reviews it as a skeptical principal engineer would before any code is written. It is the read-only **document** reviewer that complements the others: `repo-audit` audits the codebase, `ux-audit` audits a UI, and `funcspec`/`ui-issue-to-plan` _produce_ plans — `plan-review` is the only one that **audits a written plan or issue against the code**. It decomposes the artifact into tasks, **claims about the codebase**, assumptions, and acceptance criteria; **grounds** every referenced (and _implied_) component in this repo's real source via parallel `Explore` agents (`file:line`) — verifying each checkable claim and surfacing what the plan likely _missed_ (other callers of a changed API, a second implementation, an implied-but-absent migration or error state); then reviews across five lenses (**completeness, feasibility, risk, clarity, scope**), separating **gaps** (missing & needed) from **improvements** (better-with) from **errors** (code contradicts the plan), each severity-rated with an artifact quote _and_ a `file:line`. On `--depth deep` it adversarially refutes each finding before it survives. An **AskUserQuestion** interview then validates which gaps are real and in-scope and sets priority — so the report reflects your intent, not raw model suspicion. It writes a **read-only** review to `./reviews/` with a readiness verdict (🟢/🟡/🔴), a strengths section, severity-grouped findings, a color-coded gap & ambiguity register, open questions, and a "definition of ready" checklist — **never modifying the original**. It then _offers_ (doesn't assume) to apply the P0 fixes into a revised copy. Calibrated so a tight plan gets a short 🟢 review; degrades gracefully (`--no-ground` → document-only, feasibility findings flagged unconfirmed). Wiki-ingested when a vault exists.

### When to Use the Data-UI Craft Command

| Situation                                                                                                                                     | Command                                                                                |
| --------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------- |
| Audit and/or implement the craft details that make a data-dense UI (dashboard, table, admin panel, data grid, list/detail view) actually work | `/bespoke-agentics:data-ui-craft [mode: audit\|implement\|audit-and-implement] [path]` |

The Data-UI Craft command operates on data-display surfaces across **three pillars** distilled from a dashboard-design teaching: **(1) data drives the form** (let each field's _type_ choose its representation — categorical → chips, numeric → right-aligned tabular figures with consistent precision/units, long text → truncate **with a reveal**, inactive records → shaded rows, time-sequenced data → a timeline/chart rather than a time-sorted table); **(2) the right things are hidden until needed** — the **spectrum of explicitness** places every control by _frequency × importance_ (always-visible → popover/menu → revealed on hover/swipe) and **progressive disclosure** sequences onboarding into a checklist/contextual tips instead of one feature-dump modal; **(3) invisible UI makes it all function** — tooltips on icon-only controls, click-to-copy chips, comment/annotation indicators, and the complete set of empty/loading/error/hover/focus states, implemented in-place (popover/drawer/inline) rather than as new pages. It is **stack-aware** (detects framework, styling primitive, data-grid library, and existing utilities so fixes match and nothing is duplicated) with **React + Tailwind** worked examples. In `audit` it writes a severity-rated report in **both** markdown and HTML (`./data-ui-craft-audit.{md,html}`), every finding carrying a rule ID (`DF*`/`PD*`/`IU*`), a `file:line`, user-impact phrasing, and a fix pointer. In `audit-and-implement` (default) an **AskUserQuestion** interview frames intent and confirms which findings are real and in-scope before any edit; it then applies in-place fixes (preferring column-def changes when a data layer exists) and offers a reusable **React/Tailwind primitives kit** (`src/components/data-ui/`: NumericCell, Chip, StatusChip, TruncatedText, DataRow, Popover, HoverActions, OnboardingChecklist, Tooltip, CopyChip, CommentIndicator, TableStates). The destructive step is always gated behind your explicit choice. It complements `ux-audit` (Nielsen/Norman heuristics) — this is the data-display craft layer — and pairs with `ui-issue-to-plan` (when the audit is driven by a screen recording). Wiki-logged when a vault exists.

### When to Use the XState Refactor Command

| Situation                                                                                                                                                                                                          | Command                                                                                                                                                        |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Refactor a feature's ad-hoc state logic + UI into an explicit XState v5 machine, statechart, or actor system — with a validated plan, full state↔UI coverage, deterministic tests, and deprecation of the old code | `/bespoke-agentics:xstate-refactor '<target>' [--mode plan\|implement\|full] [--style machine\|statechart\|actors\|auto] [--out <dir>] [--no-tests] [--force]` |

The XState Refactor command takes a pointer at a slice of the app (file, directory, component name, or a description like "the checkout flow") whose state logic has outgrown its implementation — boolean-flag soup, `useEffect` orchestration, impossible-but-representable states — and migrates it onto **XState v5**. Its premise: the statechart already exists _implicitly_, so Phase 1 is archaeology, not invention — parallel `Explore` agents inventory every state variable and flag combination, every event/effect, and **every UI dependency** (conditional renders, disabled props, consumers outside the target) into a `file:line`-cited behavior map, honestly enumerating the impossible states the types allow. Phase 2 designs the statechart (flat machine vs hierarchical/parallel statechart vs actor system per a decision guide — including the credibility-preserving "don't use XState, use a reducer" recommendation for trivial targets), with a mermaid diagram, an impossible-states-eliminated table, and a draft **state↔UI coverage matrix** where every machine state must end up with a _decided_ visual answer (mapped UI, user-approved "intentionally invisible", or an explicit deferred gap). An **AskUserQuestion** interview validates every inferred state, behavioral divergence ("the code allows loading+error simultaneously — bug or intended?"), and UI-gap resolution, plus the deprecation appetite (delete / deprecate-then-delete / flag). The validated, self-contained migration plan goes to `./plans/`; **no application code is edited before the explicit approval gate**. On approval it implements in behavior-preserving order — XState v5 installed if missing, machine written in isolation with `setup()`, **deterministic tests green before UI wiring** (model-based path coverage via `createTestModel` from `xstate/graph` + guard-boundary unit tests + per-state UI coverage tests mirroring the matrix), UI swapped onto `useMachine`/`useSelector`/`state.matches`/`state.can` one touchpoint at a time — then retires the old state code behind a **grep-verified deprecation checklist** and runs the project's own typecheck/lint/tests. Complements the others: `ui-issue-to-plan` starts from a video, `plan-review` audits a document, `data-ui-craft` fixes display craft — this one restructures state **logic**. Wiki-ingested when a vault exists.

### When to Use the Orchestrate Command

| Situation                                                                                                                                                                   | Command                                                                                                                                                                              |
| --------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Execute an implementation plan (or a raw task) through a managed, gated, multi-agent build — the session model orchestrates, Opus/Sonnet subagents implement and smoke-test | `/bespoke-agentics:orchestrate '<plan-path-or-task>' [--depth quick\|standard\|deep] [--dry-run] [--no-confirm] [--no-smoke] [--no-review] [--single-model <m>] [--resume [<slug>]]` |

The Orchestrate command turns the session's most capable model (Fable) into a **hands-off
engineering orchestrator** that never writes production code itself. Given a plan file it first
**grounds** every `file:line` anchor and claim against current source via read-only agents (anchors
are hints, not gospel), synthesizes a **work order** — waves of work items, each with an assigned
model (Opus for contract-shaped/high-risk work and adversarial review, Sonnet for well-specified
mechanical work and browser smoke-driving) and **exact file ownership** (one owner per file per
wave; parallelism only when file sets are disjoint and no unpublished interface dependency exists)
— and confirms it in one AskUserQuestion gate alongside the plan's open questions. Implementers
receive verbatim packets (plan slice, corrected anchors, guardrails, structured return contract);
after each wave the **orchestrator runs the gates itself** (typecheck/lint/tests discovered from
the repo's own conventions) and routes exact failure output back to the owning agent (max 2
round-trips, then it stops and reports). A Sonnet smoke agent then drives the running app
(claude-in-chrome for UI) with evidence-backed pass/fail — including the **default-path
compatibility invariant** when the plan introduces opt-in behavior — and a read-only Opus reviewer
pressure-tests the diff's invariants (`--depth deep` adversarially verifies findings before they
route back). Given a **raw prompt** instead of a plan, it drafts a plan, saves it per the project's
plans convention, and gets confirmation first. Runs are **resumable**: state, work order, and
verbatim agent reports persist under `.orchestrate/<slug>/`. It closes out per project conventions
(wiki log when a vault exists) and reports faithfully — deviations, residual risks, failures
included — without ever committing or pushing unprompted. Complements the others: `plan-review`
critiques a plan without building it, `funcspec` produces one from a UI — `orchestrate` **executes**
one through subagents.

### When to Use the Workstream-Orchestrate Command

| Situation                                                                                                                                                                                    | Command                                                                                                                                                                                                     |
| -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Turn a plan into a kickoff contract, then build it one workstream at a time — each `code → validate → commit`, with a server-side hard-gate proof and a human checkpoint between workstreams | `/bespoke-agentics:workstream-orchestrate '<plan-path-or-task>' [--from WS-n] [--to WS-m] [--engine workflow\|agent] [--attempts N] [--no-commit] [--no-confirm] [--dry-run] [--resume [<slug>]] [--force]` |

The Workstream-Orchestrate command is the **sequential, commit-as-you-go** sibling of `orchestrate`.
Where `orchestrate` runs parallel implementation waves in one Agent-driven loop and never commits,
this one drives a plan **one workstream at a time** through a bounded `code → validate → commit`
**Workflow** (one Workflow invocation per workstream), and it **generates a first-class kickoff
contract** — a 10-section, human-confirmed document (Mission, Reading list, Branch, Orchestration
shape, Gates, Guardrails, Workstreams, Workflow skeleton, Stop-and-ask, Definition of done), derived
from the plan, that every workstream is built and judged against. Each workstream: an implementer
applies only its scope in the shared tree (no worktree); an **independent, read-only, adversarial
validator** re-runs the gates the orchestrator also runs itself and must **prove or refute the plan's
declared "hard gates"** — invariants that must hold at the _authoritative layer_ (a server-side
resolution function, not client CSS), proven by crafted adversarial input, never "it's hidden in the
UI"; and only a green, validated workstream earns **one Conventional Commit** staging only its files,
followed by a **human checkpoint** before the next begins. Failing validation loops back to code
(≤`--attempts`), then **halts and surfaces the findings** rather than forcing a commit. The driver
**never writes production code** — it grounds the plan's `file:line` anchors, authors the contract
(confirmed in one **AskUserQuestion** batch, where any locked decision that looks wrong is raised,
never overridden), delegates each phase to Opus/Sonnet subagents, runs the gates itself, and reports
faithfully. Given a **raw task** instead of a plan, it drafts and confirms a plan first. Runs are
**resumable** under `.workstream/<slug>/` (contract, per-agent reports, state); committed workstreams
are skipped on resume. Degrades gracefully: no Workflow tool → the identical loop via direct Agent
calls (`--engine agent`); no project `/commit` skill → a plain Conventional Commit via git;
`--dry-run` → contract only. Complements the others: `orchestrate` executes a plan in parallel without
committing, `plan-review` critiques a plan without building it — this one **generates a contract AND
executes it sequentially, committing each validated workstream**. Wiki-ingested when a vault exists.

### When to Use the Agent-Loop Audit Command

| Situation                                                                                                                                                     | Command                                                                                   |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------- |
| Audit (and optionally fix) an AI API/SDK integration for the event-loop defects that cause silent hangs, stalls, and deadlocks in managed-agent architectures | `/bespoke-agentics:agent-loop-audit [mode: audit\|implement\|audit-and-implement] [path]` |

The Agent-Loop Audit command targets the failure class unique to **managed agents**: the
tool-execution loop runs on the provider's servers, so the **bidirectional event stream is the
only control surface** — and most "the API is broken / my app hangs" reports are actually one of a
small set of client-side event-loop defects that never throw. Its rule catalog is **tiered**: a
stack-agnostic core (`EL*` lifecycle — payload-before-listener races, fire-and-forget dispatch,
teardown that deadlocks the server by leaving tool approvals unanswered; `SR*` stop-reason
semantics — idle treated as done instead of branching on the stop reason, requires-action never
answered; `RS*` resilience & steering — undifferentiated transient-vs-hard errors, no silence
watchdog, no reconnect/resume, no interrupt+redirect path; `OB*` observability — event families
undecoded, no layered debug/production surfacing) plus an **Anthropic pack** (`user.message` /
`user.interrupt` input events, `session.status.idle`, `stop_reason` payload semantics,
agent/session/fan output families) that activates when an Anthropic SDK is detected — unknown
vendors get core rules with vendor vocabulary flagged `unconfirmed-vendor`. Detection heuristics
cover **TypeScript/JavaScript and Python**. It writes a severity-rated report
(`./agent-loop-audit.md`) with a 🟢/🟡/🔴 verdict, every finding cited to `file:line` and phrased
as the **user-visible symptom** it produces, plus a per-surface loop-health matrix — then, in
`audit-and-implement` (default), an **AskUserQuestion** interview frames intent and confirms each
finding before any edit; fixes follow the reference patterns in the skill, adapted to the
project's conventions. Complements `ai-transparency` (UI state coverage for AI ops) and
`ai-waiting-ux` (Next.js waiting-UX implementation) — this is the protocol/control-loop
correctness layer beneath both. Wiki-ingested when a vault exists.

### When to Use the Screencast-Capture Command

| Situation                                                                                                                                                                                                                                        | Command                                                                                                                                                                                                        |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Record a browser flow you describe as a screencast — the agent drives Claude-in-Chrome, records it (default gif, or `--engine screen` for native-resolution monitor capture), makes an MP4, and offers to turn it into a narrated highlight reel | `/bespoke-agentics:screencast-capture ['<start-url-or-flow>'] [capture-label] [--engine chrome-gif\|screen] [--display <idx>] [--crf <n>] [--overlays clean\|clicks\|full] [--reel] [--no-reel] [--out <dir>]` |

The Screencast-Capture command is the **capture** companion to `screencast-highlight-reel`: that
skill _polishes_ a finished screencast into a narrated reel — this one _produces_ the screencast
agentically, so a human never has to screen-record themselves. Given a start URL and a flow you
describe, it drives a live **Claude-in-Chrome** session: an **AskUserQuestion** interview turns the
request into a concrete shot list, it opens a fresh tab and **pauses for you to log in / dismiss
banners before recording starts** (credentials and consent clicks never enter the footage — the agent
never types secrets), then records the flow step-by-step with the `gif_creator` tool (**click
indicators only** by default; `--overlays clean/full` to change the look), taking a screenshot
between steps so the capture reads smoothly. That default engine is zero-setup but the Chrome capture is
**hard-capped ~1200px** and the GIF is dithered; for a crisp result, **`--engine screen`** records a
chosen monitor with ffmpeg at **native resolution + configurable bitrate** (`--display` / `--crf`),
auto-cropped to the browser window — it needs macOS Screen-Recording permission and records the whole
monitor. The gif engine exports the GIF and **converts it to a real-duration MP4** (a GIF reports no
container duration, so the reel's frame-extractor would otherwise drift on frame-index timestamps); the
screen engine writes MP4 directly. It then presents the MP4 and, per your choice, **hands off to
`screencast-highlight-reel`** (default:
produce the MP4, then ask; `--reel`/`--no-reel` to force or skip), forwarding `--no-tts` when there's
no `ELEVENLABS_API_KEY` and `--no-ground` when the recorded site isn't this repo's app — the reel runs
its own confirm-before-render gate, so nothing renders unprompted. Degrades gracefully (no ffmpeg →
stops before recording; a login wall it can't clear → captures what's reachable or stops).
Wiki-logged when a vault exists.

### When to Use the Interactive-Wireframe Command

| Situation                                                                                                                    | Command                                                                                                                                                                         |
| ---------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Settle an undecided UI change by building a live, code-grounded HTML wireframe, interviewing against it, and emitting a spec | `/bespoke-agentics:interactive-wireframe '<surface>' [--slug <name>] [--rounds N] [--port N] [--out <dir>] [--spec <path>] [--fresh] [--ttl <days>] [--no-verify] [--no-serve]` |

The Interactive-Wireframe command turns a UI argument into something you can click. Its premise:
**people critique something concrete far better than they answer a hypothetical** — "should the
header stay pinned?" gets a shrug; the same question asked while looking at a real header with the
scroll threshold on a slider gets a decision in ten seconds, and often a different one. Two
properties do the work. **(1) It is grounded in real code** — it detects the stack and lifts design
tokens, typography, the literal enums/labels the surface displays, roles/permission flags, the
existing layout components the change touches, and behavioural constants from actual source, each
cited to a path, into `wireframes/<slug>/grounding.md`; nothing is invented, and a project with no
design system gets values derived from the running app's computed styles, **labelled as derived**.
That is what makes the wireframe _predictive_ rather than illustrative — collisions, real label
widths and contrast failures only appear with real values. **(2) It is interactive** — it emits ONE
self-contained HTML file (inline CSS + JS, no build step, opens by double-click) carrying a **control
overlay generated from the axes that surface actually varies on** (role switcher, entity states,
permission toggles, data extremes, behavioural thresholds, layout variants, per-row config matrices,
zone guides, live state readout), so every control replaces a question that would otherwise be asked
in prose. State is mirrored into the URL, so any configuration is a link you can paste, screenshot,
and re-verify. It serves the file over local HTTP — **starting at 8791 and deliberately never probing
8787** (`wrangler dev`'s default), falling forward to 8799, naming whatever holds a busy port, and
sending `no-store` so a rebuild is always what you measure — because `file://` URLs are rewritten to
`https://file://` and fail under browser automation. Then it **interviews in AskUserQuestion rounds of
≤4, every option carrying a concrete ASCII preview, rebuilding the wireframe between rounds** so
later questions are asked against something real; it actively **hunts contradictions** between
answers and surfaces them (architecturally impossible, semantically empty, duplicated, or the
collision recreated one band lower) instead of silently reconciling, and converts aesthetic
disagreements into switchable variants rendered side by side. The interview is **two-way with the
browser**: a comment mode in the wireframe (✎ or `c`) lets the user pick any element and comment on
it — the comment lands in the session carrying the selector, zone, fragment, and the exact axis
state on screen (`POST /__feedback` → `.feedback.jsonl` on the loopback serve script), and the
agent's replies thread back into the page's comment panel (`.replies.jsonl`, polled ~2s); with the
optional `wireframe-feedback` **channel** registered (`channels/wireframe-feedback/`, launched via
`claude --dangerously-load-development-channels server:wireframe-feedback`), comments push into the
session instantly instead of being drained between rounds. It **verifies by measurement, not
eyeballing** — band/region contiguity, computed WCAG contrast, markup validity (`button button`,
dangling `aria-controls`, unnamed controls), focusables that are tabbable-but-off-screen, and
scripted behavioural sequences — with the backgrounded-tab failure modes encoded as a hard checklist
(in a hidden tab, scroll events, rAF, CSS transitions and `.focus()` all silently no-op, so a
behavioural "failure" is a measurement artifact until proven otherwise; anything unmeasured is
labelled **"not verified"** rather than claimed). It ends at a spec — decisions marked by how each
was settled, the structural contract with its numbers, architecture with real paths, behaviour,
states, verification results, risks, open questions, out of scope, testing — written to the wiki if
one exists, else `./plans/<slug>.md`. Composes both ways with `spec-elicitation` (invoke it
mid-interview to add the wireframe layer, or hand its decision table over for the non-UI
dimensions). Distinct from `ux-audit` (evaluates an interface that already exists) and
`data-ui-craft` (fixes display craft in shipped UI): this one settles a design **before** it is
built. Repeat runs in the same project start **warm**: a per-out-dir **reuse library**
(`wireframes/_index.md` + `wireframes/_library/` — grounding cache, HTML/CSS fragment files,
append-only decisions ledger) is consumed at grounding/build/interview time (TTL-trusted, default 14
days via `--ttl`, every cached value labelled `cached — verified <date>` — labels never lie; past
TTL the `path:line` anchors are re-grepped; drift is re-derived and reported) and **auto-harvested**
after each spec — settled chrome becomes fragments, run-independent grounding merges into the cache,
the spec's decision table appends to the ledger so later runs import verdicts as fixed context with
one "reopen?" affordance instead of re-asking. `--fresh` ignores the library for a run (but still
harvests); a project with prior wireframes and no library gets a one-time backfill offer. **No
production code is written.**

### When to Use the Wireframe-Parity Command

| Situation                                                                | Command                                                                                                                                                       |
| ------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Confirm the UI that was implemented matches the wireframe a spec settled | `/bespoke-agentics:wireframe-parity '<spec-or-slug>' --app <url> [--wireframe <path>] [--depth quick\|standard\|deep] [--out <dir>] [--no-browser] [--force]` |

The Wireframe-Parity command is the **post-implementation** companion to `interactive-wireframe`: that
skill settles a UI and freezes the intended design as measurable truth; this one, once the feature is
built, confirms the **as-built UI matches the wireframe that specified it**. Its premise is that it
does not have to invent the "intended" side — the wireframe already froze it: the spec's **Verification**
table is a snapshot of `__wf` measurements (band contiguity like `0→44→76→131`, contrast ratios +
AA/AAA, `button button` count, off-screen focusables), **The contract** holds the structural invariants
and their numbers, the **Decisions** table + `_library/decisions.md` ledger record what was settled,
and the **States** table is the overlay's axes resolved (each row reproducible as a wireframe URL). It
runs two passes. **(1) Structural** — parallel `Explore` agents ground every settled decision / state /
label in the real implementation (`file:line`), marking each honored / drifted / missing (the floor,
available even under `--no-browser`). **(2) Measured** — it serves the wireframe (reusing
`interactive-wireframe`'s `serve-wireframe.sh`) and injects the **same** dependency-free measurement kit
(`wf-probe.js`, a standalone copy of the wireframe's `__wf`) into **both** the wireframe and the running
app, drives each to the matching state, and diffs band geometry / contrast / markup / focusables /
rendered labels / design tokens **apples-to-apples** — parity being invariant-**within-tolerance**
(±2px geometry, same AA/AAA verdict, contiguity as the contract requires), never pixel-identity.
Unreachable (auth-gated) states are labelled **"not measured"**, never assumed; a behavioural "failure"
in a backgrounded tab is treated as a measurement artifact. Because a wireframe is a settled design that
a build sometimes deliberately evolves past, **spec Decisions are the parity contract** — deviating from
a settled decision is a finding, unspecified details are free — and an **AskUserQuestion** interview
classifies each divergence as **regression** (fix the build), **intended evolution** (the build is right,
the wireframe is now stale), or **out of scope** before anything is called a failure. On `--depth deep`
each divergence is adversarially verified first. It writes a **read-only** report to `./reviews/` with a
parity verdict (🟢 faithful / 🟡 minor drift / 🔴 diverges), a **decision-by-decision parity table**, a
**measured parity table** (intended / spec-frozen / as-built / Δ), label fidelity, a color-coded
divergence register, an honest "not measured" coverage section, and a "definition of parity" checklist —
then **offers** (doesn't assume) to open the P0 regressions as tasks or refresh the stale decisions
ledger. Distinct from `plan-review` (audits a document _before_ build) and `ux-audit` (audits a UI
against heuristics): this audits a **built UI against the wireframe that specified it**. **The
implementation is never modified.**

### When to Use the Reimagine Command

| Situation                                                                                                                        | Command                                                                                                                                                                                                                                         |
| -------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Explore what an existing component/page could become — a live gallery of brand-faithful redesign directions, settled into a spec | `/bespoke-agentics:reimagine '<surface>' [--slug <name>] [--tiers restyle,restructure,rethink] [--variants N] [--rounds N] [--baseline-url <url>] [--port N] [--out <dir>] [--spec <path>] [--fresh] [--ttl <days>] [--no-verify] [--no-serve]` |

The Reimagine command is the **upstream sibling** of the wireframe pair: _reimagine explores **which**
design, `interactive-wireframe` settles **the** design, `wireframe-parity` checks the build_. Point it
at a surface that exists and disappoints and it produces **one self-contained HTML variant gallery** —
the **Current design recreated from source as an honest baseline** (a transcription, not a memory:
structure/labels/tokens cited `path:line` into a Baseline-fidelity section, optionally cross-checked
against the running app via wireframe-parity's `wf-probe.js` with a fidelity chip that never lies) plus
reimagined versions spanning three **ambition tiers that are contracts, not quality levels**: **Restyle**
(DOM and reading order preserved, only treatment changes), **Restructure** (content inventory preserved,
layout/IA changes), **Rethink** (the task preserved, the interaction model changes) — each policed by a
mechanical proxy so "a Rethink that is secretly a restyle" gets demoted, not shipped. Everything is
**brand-faithful**: variants draw from ONE shared grounded token block; a direction that needs to leave
the design system is a legitimate pitch but must say so and get approved. Directions are **pitched as
briefs and picked in an interview round BEFORE anything is built** (two per tier: thesis, changes,
preserves, grounding, risk, ASCII preview; unbuilt briefs feed the spec's Rejected Directions and the
ledger). The gallery derives from the wireframe scaffold (byte-faithful `WF`/`__wf`/`__wfFb` kits, two
marked `RV:` additions, drift-checked) and adds real **sibling panes** per variant — a bottom-docked
switcher, **single/grid/split** views, and **shared axes that hit every pane at once** (flip "empty"
and all variants answer simultaneously — the gallery's strongest interview move); browser comments
arrive tagged with their pane. Served by the parent's `serve-wireframe.sh` **reused in place** (8791,
never 8787). The interview arcs **reaction → per-variant critique (works/breaks/what to steal) →
hybridization — a chosen hybrid is rebuilt as a real pane in `reimagine-v2.html`, never hand-waved —
→ winner**, with per-loser rejection reasons confirmed from critique evidence. The winner gets the full
measurement battery **in single view** (grid/split are for looking, not measuring); the spec lands with
the **divergence-from-current inventory** (Δ rows: Current at `path:line` → becomes → change class —
the implementer's worklist), rejected directions, two verification tables (the winner's in
wireframe-parity-consumable format), and offers — never auto-runs — the `interactive-wireframe`
(fine-grained settlement) and orchestrate (build) handoffs. Shares the wireframe **reuse library**
(`wireframes/_library/`, `_index.md` runs typed `wireframe`|`reimagine`); rejected variants' styles
never harvest. Distinct from `ux-audit` (what's wrong) and `impeccable`/design skills (write real
code): this shows **what it could become**, and **writes no production code.**

### When to Use the Dead-Code-Sweep Command

| Situation                                                                                                                                  | Command                                                                                                         |
| ------------------------------------------------------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------- |
| Right after a coding session — find and remove the dead code the changes left behind (including stale tests), with proof nothing regressed | `/bespoke-agentics:dead-code-sweep [uncommitted\|branch\|project] [--base <ref>] [--report-only] [--out <dir>]` |

The Dead-Code-Sweep command cleans up what a coding session leaves behind — the replaced
implementation nobody deleted, the helper whose last caller vanished, the dangling import, the test
still exercising a function that no longer exists. It resolves a **scope** (`uncommitted` working
tree by default, a branch vs its merge-base, or the whole project — auto-detected and stated),
discovers the repo's **own gates** (typecheck/lint/build/test from package scripts, Makefile,
pyproject, Cargo…) and **runs them first**, so "no regressions" is a claim relative to a recorded
baseline — no gates → autonomous deletion is off; a baseline broken in a way that masks regressions
→ automatic report-only. Candidates come from **tracing the diff** (what did this change stop
referencing?) plus the ecosystem's native detectors (knip, ruff, vulture, cargo machete — candidates,
never verdicts), and every one passes a **liveness checklist** (dynamic/string references, framework
conventions, public-API surface, keep-markers) before classification: **high-confidence items are
auto-removed in gated waves** — gates re-run after every wave, a _new_ failure restores the code (a
failing test just proved the code alive; the test is never deleted to get green), cascade re-scans
catch code orphaned by the removals themselves — **medium items are batch-confirmed in one
AskUserQuestion**, **low items are report-only**. Stale tests, mocks, and snapshots are removed with
their subjects as one unit; out-of-scope observations are reported, never touched. Every edit is
backed up under `.dead-code-sweep/<ts>/` with a one-command restore, the report cites per-unit
evidence (searches run, detectors agreeing) and lists restorations honestly, and git state is never
committed, staged, or stashed. Benchmarked on planted fixtures against skill-less Claude: both find
the dead code — the skill's wins are **governance** (no silent deletion of commented-out code, no
unprompted commits, everything recoverable). Distinct from `repo-audit` (reports, never edits) and
`simplify`-style cleanups (style, not deadness): this one **deletes proven-dead code safely**.

### When to Use the Defect-Intake Command

| Situation                                                                                                                                                    | Command                                                                                |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------------- |
| A defect surfaced mid-session (bug, missing test, swallowed error, contract violation, gap) and it needs proper disposition instead of a note in the summary | `/bespoke-agentics:defect-intake '<defect description, file:line, or failing output>'` |

The Defect-Intake command exists because **noting a defect is not resolving a defect** — a finding
that survives into a session summary, a `TODO`, or a "future work" bullet has been deferred, and the
next session inherits a codebase whose known problems are invisible. It is **user-invoked only**:
deciding a defect is worth stopping for is the operator's call, so the skill never self-triggers on
the mere mention of a bug. The sequence is capture → **verify before editing** (an unreproduced
defect is a hypothesis; the skill guards explicitly against the _phantom defect_ — code that looks
wrong but is load-bearing — and against fixing the first plausible root cause rather than the actual
one) → **classify by blast radius, never by authorship** (fix-now / fold-into-current-change /
escalate-to-user; "we didn't introduce it" is not a disposition) → baseline the repo's **own gates**
so pre-existing red is known before you can misattribute it → **write the failing test first** and
watch it fail, because a test written after the fix passes immediately and proves nothing →
**narrowest fix** that turns it green (the adjacent cleanup is its own item) → re-run gates against
the baseline → document symptom/root cause/fix/**why it was wrong** where that repo keeps durable
knowledge (`references/documentation-targets.md` resolves wiki vs. ADR vs. changelog vs.
comment-plus-test) → resume with an honest account. Two hard lines: **escalation means stopping and
asking in the conversation now** — a TODO, a ticket, or a handoff bullet is deferral wearing
escalation's clothes — and **a failing test is never deleted, skipped, or loosened to reach green**,
because green achieved by silencing the alarm is worse than red. Never commits. Distinct from
`repo-audit` and `dead-code-sweep`, which _hunt_ for problems across a scope: this one dispositions
a **single known defect** and does not go looking for more.

### When to Use the Misunderstanding Command

| Situation                                                                                                                     | Command                                                           |
| ----------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------- |
| A plan step, wiki claim, doc, or earlier turn led the agent to infer something wrong, and work is being built on that reading | `/bespoke-agentics:misunderstanding ['<what was misunderstood>']` |

The Misunderstanding command exists because **restating is not correcting**. By the time a wrong
reading is noticed it has usually already produced decisions and code, and the claim that caused it
is still sitting in the source ready to mislead the next session identically. Like `defect-intake`
it is **user-invoked only** — deciding something was misunderstood is the operator's call, and the
skill never self-triggers on the smell of confusion. It treats a misunderstanding as a **chain, not
a fact**: something was said, it was read a particular way, and something was built — so it
reconstructs an **inference ledger** pairing every belief with the **verbatim source text** that
produced it and labeling each `stated` (the source said it, you read it wrong — the source is fine)
/ `inferred` (the source implied it and you extended it — the source is ambiguous) /
`assumed-from-silence` (the source never addressed it — the source has a hole), because those are
three different defects with three different fixes. Scope is the **blast radius**: the flagged
belief, its **siblings** drawn from the same source (a page stale enough to mislead once makes every
other reading of it suspect), and its **dependents** — explicitly not a session-wide assumption
audit. The interview then does the thing that makes it cheap: the user already said you were wrong,
so the skill's job is to make that **answerable** — every `AskUserQuestion` **quotes its source**,
leads with your current belief as the one-click confirmation, and offers the plausible alternative
readings a competent person could have taken from the same words (≤4 per call, ≤3 rounds, ordered by
blast radius, never open-ended; an `assumed-from-silence` row asks for the missing rule instead).
Contradictions between the correction and what the artifact actually says are **surfaced, never
reconciled** — the artifact may be stale, or the user may be misremembering their own document. It
then **corrects the source** (repo plans/specs edited; wiki pages updated and logged with raw
sources never modified — the correction is noted and linked back; external content reported
verbatim, never edited), **inventories the work built on the error** and offers keep / revise /
revert per item — never auto-reverting, because plenty of work survives its bad premise — records
proportionally via `defect-intake`'s documentation routing, feeds a knowledge store when one exists
(silently skipped when not), and resumes with a corrected restatement in its own words. A verified
non-misunderstanding is a successful run. **Never commits.**

### When to Use the Delivery-Recap Command

| Situation                                                                                                                       | Command                                                                                                       |
| ------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------- |
| A PM, tech lead, or client needs to know what actually shipped — and be able to open the site and verify it without asking you | `/bespoke-agentics:delivery-recap [window] [--author me] [--sessions current\|all\|none] [--out <dir>]` |

The Delivery-Recap command answers the question a status update is really being asked: **"is the
thing I asked for actually there, and how do I go look at it?"** A `git log` with prettier headings
answers a different question — which files changed — so the skill's unit of reporting is the
**deliverable, not the commit**: several commits routinely add up to one outcome, and several more
add up to none. Evidence comes from a bundled deterministic collector (`scripts/collect_window.py`,
stdlib-only) that gathers four sources over a window defaulting to **the last 24 hours** — git
commits, **uncommitted working-tree changes** (labeled as such, because a reader assumes anything
listed is on the branch), **Claude Code session transcripts** (the only source that records what the
engineer was _trying_ to do, in their own words, including intent that produced no commit), and wiki
page edits — emitting one JSON document with a `notes` array of everything unavailable, so blind
spots survive into the report instead of being smoothed over. Each changed path carries a
`bucket_hint` (ui/api/service/db/config) **with the rule that produced it**, because a path guess is
right most of the time and wrong exactly where it matters. The skill then reads the real diffs
(fanning out to parallel `Explore` agents when several areas changed), and — the step that separates
this from a changelog — **traces every changed UI file up to the route that renders it**, since a
reader cannot open `InvoiceTable.tsx`; a shared component's blast radius is enumerated, and a change
that is genuinely invisible (flagged, admin-only, a pure refactor) is _said_ to be invisible. Backend
work is described by effect, not by filename: which column, nullable or not, migration run or not,
backward compatible or not, and **any newly required env var called out in its own sentence** as the
deploy blocker it is. One `AskUserQuestion` confirms the base URL from candidates grepped out of the
README, `.env.example`, and deploy config — then the payload, a numbered walkthrough where each step
names where to go, what to do, and **what the reader should see, contrasted with what it replaced**.
Confidence is content: every claim is labeled **verified** (traced end to end) / **inferred** (the
code implies it) / **unconfirmed**, and a change whose user-visible effect cannot be established gets
its own honest section rather than an invented business rationale — the single failure that makes a
reader stop believing the rest. Lands as markdown in `./reports/recap-YYYY-MM-DD.md` **and** a
shareable Artifact; offers wiki ingestion when a vault exists. Distinct from `repo-audit` (grades
code health) and `proof-of-work` (agent evidence in CI): this one reports **what a human delivered,
to a human who has to trust it**. Read-only — never edits application code, never commits, never
pushes.

### When to Use the Skill-Reverse-Engineer Command

| Situation                                                                                                                         | Command                                                                                                            |
| --------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------ |
| A skill works but behaves differently every run — reverse-engineer it and make it more deterministic, robust, and less AI-reliant | `/bespoke-agentics:skill-reverse-engineer '<skill-path-or-name>' [--mode audit\|apply\|new-version] [--out <dir>]` |

The Skill-Reverse-Engineer command treats a skill as a program whose interpreter is a language
model — and freshly generated skills put _everything_ in the "judged" bucket: mechanical shell
procedures written as prose the model re-derives, report structures described instead of
templated, "verify that X" left to eyeballing, phase handoffs passed as vibes. It reconstructs
what one run of the target actually does into a **step graph**, classifying each step's executor
(`script` / `model-mechanical` / `model-judgment` / `user-gate`) via the **distill test** —
_would two competent runs, given the same inputs, be wrong to differ?_ — then audits against a
rule catalog (`DS*` prose→script, `TP*` generated→template, `CT*` loose contracts, `VF*`
judgment→check, `AM*` ambiguity, `RB*` robustness, `KM*` knowledge materialization), seeded by a
bundled deterministic **inventory script** (prose/code split, ALL-CAPS directives, vague
quantifiers, unrunnable verify-verbs, broken refs, script hygiene). Its differentiator is
**host grounding**: a bounded `host_probe.py` enumerates the invoking project's stack, data
schemas, and data stores; the run classifies host state (`host-grounded`/`host-generic`/
`no-host`) and records, per model step, what _stable host knowledge_ it consumes — so per-run
LLM lookups can be **materialized** into generated fact files (e.g. a configuration matrix mined
from the host's schema) carrying `_provenance` (only `mined` — generator + cited sources + SHA256
`--check` — or `declared`-by-interview is expressible; a frozen model guess is unrepresentable),
consulted via a check → regenerate → derive-fresh-and-label ladder in which a stale artifact is
never trusted silently; an unlabeled hardcoded snapshot is itself a KM5 defect, so
over-materialization is self-indicting. The severity scale is run-to-run consequence; the report
(`./reviews/skill-re-<name>.md` + `host-context.json` sidecar) carries a verdict (🟢
already-hardened — short form, no padding / 🟡 improvisation-dependent / 🔴 vibes-driven), the
step-executor matrix, a materialization-opportunities table, and an **essential-judgment
register** — the AI-reliance that should STAY (design, synthesis, convention-matching), because
a skill flattened into a brittle script bundle is a failure mode, not a win. Nothing is edited
before an **AskUserQuestion gate** (mode, appetite, per-finding confirmation, judgment
overrides, which facts to materialize / where artifacts live / refresh policy); `apply`
refactors in place, `new-version` emits a drop-in hardened copy outside auto-registered paths
with a per-file diff summary, and every shipped script and generator is **executed before it
ships** (usage path, happy path, drift-check tamper test). Behavior-preserving throughout — the
skill does the same job, with less of it improvised. Distinct from `skill-creator` (creates and
eval-iterates skills) and structure auditors (YAML/best-practice compliance): this one
restructures **where the work happens**.

### When to Use Each MicroDots Command

| Situation                                                                                     | Command                                                        |
| --------------------------------------------------------------------------------------------- | -------------------------------------------------------------- |
| Turn a Claude Design prototype into a MicroDots build plan                                    | `/bespoke-agentics:microdots-port-prototype '<artifact.html>'` |
| Port a whole existing app onto the MicroDots framework                                        | `/bespoke-agentics:microdots-port-app '<app-path>'`            |
| Extract ONE feature out of an app into a standalone micro-app                                 | `/bespoke-agentics:microdots-port-feature '<what>'`            |
| Create a new MicroDot — compiler workspace, or repo extension with full host wiring           | `/bespoke-agentics:microdots-new-micro '<name> [brief]'`       |
| Confirm a MicroDots change is actually done (static checks are not sufficient)                | `/bespoke-agentics:microdots-verify`                           |
| A MicroDot is blank, stale, or "could not reach the service"                                  | `/bespoke-agentics:microdots-debug-blank`                      |
| Publish a MicroDots workspace                                                                 | `/bespoke-agentics:microdots-deploy`                           |
| Turn repo history / a shipped plan / a feature into a published post, changelog, or deep-dive | `/bespoke-agentics:microdots-content '<ask>'`                  |
| Build any explainer, recap, or report page in the BespokeAgentics / MicroDots brand           | `/bespoke-agentics:microdots-brand-recap`                      |
| Refine how a MicroDot actually looks (polish, audit, critique, live variants)                 | `/bespoke-agentics:microdots-design`                           |

These ten cover the MicroDots framework (Effect v4 + Foldkit custom elements)
end to end: **plan** (`port-prototype`), **build** (`port-app`, `port-feature`,
`new-micro`), **prove** (`verify`, `debug-blank`), **ship** (`deploy`), **tell**
(`content`, `brand-recap`), and **refine** (`design`, which routes to the
`impeccable-microdots` plugin). All of them **resolve the workspace before acting** — dot
directory (`microdots/` vs `micros/`), runtime/element package specifier, script
names, ports and host URL are read from the project, never assumed, so they work
in any MicroDots workspace rather than only the framework's own repo.

Two things bind across the set. **`Runtime.embed` forks the runtime**, so a
startup defect produces a blank MicroDot with a clean console — typecheck, lint,
tests and build all pass while nothing renders. That is why `microdots-verify`
treats the browser step as the point rather than a formality, and why
`microdots-debug-blank` exists as a separate staged protocol (confirm it is
really blank → isolate bundle/registration/runtime → extract the defect from
`cause.reasons[0].defect` → the three CORS lies → topology gaps that render as a
blank page rather than an error). And **the host seam is exactly four edits** —
registry entry, markup section, topology route, slot-manifest entry — so
`microdots-new-micro` completes the wiring the generator only prints, including
the deploy-discovery registration the generator never mentions.

### When to Use the AI-Native SDLC Command

| Situation                                                                                                                                     | Command                                                                                          |
| ---------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------ |
| Transform the process around agentic coding — score a repo's SDLC maturity, install the playbook's controls, or drive work through the artifact chain | `/bespoke-agentics:ai-native-sdlc [mode: assess\|adopt\|run] [plays or '<work item>'] [--home <dir>] [--out <file>] [--no-confirm]` |

The AI-Native SDLC command implements Anthropic's AI-Native SDLC playbook: when code is no longer
the bottleneck, the human-speed stages around the build phase are — so the process is rebuilt as a
loop of **committed artifacts** (`intent.md` → `spec.md` → `plan.md` → diff+tests → reviewed PR →
incident record), each stage ending by writing one and the next beginning by reading it, with
**humans owning every gate**. `assess` is read-only: it probes the repo for evidence of each of the
16 plays (tuned `CLAUDE.md`, policy skills, guardrail + approval-gate hooks, `REVIEW.md`, agent
evals, `bands.yaml` monitoring tiers, the artifact chain itself) and writes a 🟢/🟡/🔴 scorecard —
with an honest ⚪ for what a repo can't show — plus a dependency-ordered adoption path. `adopt`
scaffolds the chosen plays as **real, working files** adapted to the repo's own commands and named
gate owners (never generic copies), each hook verified against both its allow and block fixtures
before it counts, settings merged additively, nothing committed. `run` drives one work item through
the chain gate by gate — brainstormed intent, skill-constrained spec with flagged concerns, a plan
an uninvolved engineer could implement alone, failing-test-first builds with the plan kept in sync,
and a review-ready close — where a rejected intent is a successful (cheap) outcome. Composes with
the rest of the plugin: `spec-elicitation` can power the spec gate, `plan-review` the plan gate,
`orchestrate`/`workstream-orchestrate` the build. Distinct from `/agentnative:suite`, which makes
the repo a good place for agents to **work** (fast CI, hermetic deploys, evidence) — this one
transforms the **process**: who approves what, which artifact fires which stage, where human
judgment concentrates. Wiki-ingested when a vault exists.

### When to Use Each Agent-Native Engineering Command

| Situation                                                                                                                             | Command                                                                       |
| ------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------- |
| Run the whole suite: readiness scorecard across all six dimensions, then dispatch the skills in dependency order (resumable)          | `/agentnative:suite [mode: assess\|run] [dimensions] [--resume]`              |
| CI is slow; agents wait minutes to verify their work — swap in native tooling (TS7, oxlint/oxfmt, uv, ruff) and split fast/slow lanes | `/agentnative:fast-ci [mode: audit\|implement\|audit-and-implement] [path]`   |
| Trigger coding agents from issue-triage labels — auto-triage, repro-on-label, PoC-on-label                                            | `/agentnative:issue-to-agent [mode: plan\|implement] [labels]`                |
| Put scheduled agents on the chores devs skip — regression backfill, SDK gaps, skill tuning, drift                                     | `/agentnative:chore-crons [mode: plan\|implement] [chores]`                   |
| Give agents the means to prove their work — screenshots, browser checks, diffs, evidence storage + PR comments                        | `/agentnative:proof-of-work [mode: plan\|implement] [scope: local\|ci\|both]` |
| Make the app runnable locally, hermetically, N instances at a time                                                                    | `/agentnative:hermetic-deploy [mode: audit\|implement] [instances]`           |
| Give agents production-realistic seed data as deterministic scenarios                                                                 | `/agentnative:sim-data [mode: plan\|implement] [scenario]`                    |

The Agent-Native Engineering suite makes a codebase a good place for coding agents to work, on
the premise that agent throughput is gated by the verification loop, not by generation. The six
skills form a dependency chain: **fast-ci** shrinks the check cycle (native-toolchain swap
catalog `TC*` + lane rules `LN*`, baseline-measured, reformats blame-ignored); **hermetic-deploy**
gives every agent its own one-command instance (`H*` hermeticity catalog, Compose `-p`
namespacing, ephemeral ports, `scripts/dev-stack.sh up <id>` → healthy URL, isolation proven by
actually running N side by side); **sim-data** fills those instances with statistically honest,
deterministic scenario data (shapes mined as aggregates — values never cross the prod boundary
unmasked; copycat/faker synthesis or Greenmask/anon anonymization with a named-human review
gate; double-seed diff proves determinism); **proof-of-work** lets agents attach evidence instead
of assertions (agent-browser/Playwright capture, `evidence/` manifest convention, presigned-URL
storage, one create-or-update PR evidence comment); **issue-to-agent** dispatches agents from
triage labels with a bounded mandate ending at the handoff (repro branch + failing test + honest
comment — never an unsupervised fix; least-privilege, injection-aware, zizmor-verified); and
**chore-crons** schedules agents onto the neglected tail (evidence-based chore inventory, only
self-verifiable chores get crons, single rolling tracking channel, idempotency double-fire
tested). All are interview-gated before writing, degrade gracefully off the GitHub-first happy
path, and wiki-ingest their reports/conventions when a vault exists. **`/agentnative:suite`** is
the conductor over the six: it probes all dimensions into a 🟢/🟡/🔴 readiness scorecard
(`./plans/agentnative-suite.md`), gates dimension selection/modes/budget behind one interview,
then dispatches each skill in the dependency order above — persisting state in
`.agentnative/suite-state.json` so interrupted runs resume with `--resume` and repeat runs skip
what already landed; a blocked dimension stops the chain rather than building on it.

### Agent Workflow Integration

**Before starting any analysis task:**

1. Check if a wiki exists at `wiki/` — if not, suggest running `/wiki:init`
2. Read `wiki/_schema/SCHEMA.md` to understand conventions
3. Read existing wiki pages for the relevant client/project
4. Check `wiki/_index.md` for the current page inventory
5. Check `wiki/_log.md` for recent activity

**After completing any analysis task:**

1. Ingest results into the wiki using the appropriate skill
2. Verify cross-references are intact
3. Update `wiki/_index.md` if new pages were created
4. Add a log entry to `wiki/_log.md`

**When answering questions:**

1. Search the wiki first — it contains compiled, validated knowledge
2. If the wiki doesn't have the answer, search raw sources
3. If you discover new information while answering, promote it to a wiki page using `/wiki:query --promote`

### Decision Status Colors

When assessing features or making decisions, use the standard color system:

- 🟢 **OOTB** — Out of the box, no customization needed
- 🔵 **Config** — Configurable, no custom code required
- 🟡 **Custom Dev** — Requires custom development
- 🔴 **Gap** — Not possible or requires major workaround
- ⚪ **TBD** — Not yet assessed
- 🟣 **3rd Party** — Requires third-party solution

---

## Plugin Structure

    bespoke-agentics-plugin/
    ├─ skills/                        # All agent skills
    │  ├─ wiki-init/                  # Initialize a new wiki vault
    │  ├─ wiki-scaffold-client/       # Scaffold a new client/project workspace
    │  ├─ wiki-ingest-meeting/        # Ingest meeting pipeline outputs
    │  ├─ wiki-ingest-document/       # Ingest emails, specs, PDFs
    │  ├─ wiki-confluence-reconcile/  # Bidirectional Confluence sync
    │  ├─ wiki-lint/                  # 8-dimension health check (Check 8: ontology, when installed)
    │  ├─ wiki-query/                 # Natural language search + synthesis
    │  ├─ glean-agent-toolkit/        # Scaffold, extend, and triage Glean agents
    │  ├─ bun-workspace/              # Convert/audit/extend Bun workspace monorepos
    │  ├─ progressive-disclosure/     # Layered CLAUDE.md/AGENTS.md + large-codebase config
    │  ├─ claude-design-to-app-workflow/  # Design zip → component library + Storybook
    │  ├─ funcspec/                   # Storybook pages → validated implementation plan
    │  ├─ knowledge-loop/             # Self-improving facts → hypotheses → rules loop
    │  ├─ project-db/                 # Queryable SQLite (+ Cloudflare D1) database over the wiki or docs+data: typed views, guarded SQL CLI, sync hook, MCP, D1 publish
    │  ├─ project-ontology/           # Enforced dot-notated vocabulary over the wiki: mined ontology.yaml, PreToolUse ratchet hook, human approval gate, DB tables, lint Check 8
    │  ├─ ui-issue-to-plan/           # Narrated UI screencast → code-grounded plan (fixes + UX enhancements)
    │  ├─ screencast-highlight-reel/  # Long app-demo screencast → grounded, narrated, subtitled highlight video (TTS + ffmpeg assembly)
    │  ├─ screencast-capture/         # Browser flow → MP4 (gif tab-capture or --engine screen native-res) → hands to screencast-highlight-reel
    │  ├─ interactive-wireframe/      # Undecided UI → code-grounded interactive HTML wireframe → interview → spec
    │  ├─ reimagine/                  # Existing component/page → brand-faithful variant gallery (Restyle/Restructure/Rethink) → winner spec with Δ inventory
    │  ├─ wireframe-parity/           # Built UI vs the wireframe that specified it → read-only parity report (structural + measured)
    │  ├─ plan-review/                # Plan/spec/issue → read-only, code-grounded gap review
    │  ├─ data-ui-craft/              # Data-dense UI audit + fixes + React/Tailwind primitives kit
    │  ├─ xstate-refactor/            # Feature state logic + UI → XState v5 machine/statechart/actors
    │  ├─ dead-code-sweep/            # Post-session dead-code cleanup: diff-seeded, gated waves, tiered confirmation, regression-proofed
    │  ├─ defect-intake/              # Known defect → verify, classify by blast radius, failing-test-first fix, document, resume (user-invoked)
    │  ├─ delivery-recap/            # Time window → PM/tech-lead delivery recap: deliverables, UI routes to click, backend/DB effects, confidence labels
    │  ├─ misunderstanding/           # Wrong inference → source-quoted inference ledger → targeted interview → source correction + work disposition (user-invoked)
    │  ├─ skill-reverse-engineer/     # Target skill → determinism audit (DS/TP/CT/VF/AM/RB/KM + host grounding) → gated refactor or hardened new version
    │  ├─ orchestrate/                # Plan/task → gated multi-agent implementation (Fable orchestrates, Opus/Sonnet implement)
    │  ├─ workstream-orchestrate/     # Plan → kickoff contract → sequential per-WS code→validate→commit (Workflow) + hard-gate proofs
    │  ├─ microdots-port-prototype/   # Claude Design prototype → extracted source → inferred + validated MicroDots build plan
    │  ├─ microdots-port-app/         # Whole app → MicroDots framework port (composition proposal, gated waves)
    │  ├─ microdots-port-feature/     # ONE feature out of an app → standalone micro-app in a micros workspace
    │  ├─ microdots-new-micro/        # New MicroDot: catalog-locked compiler workspace OR repo-extension + full host wiring
    │  ├─ microdots-verify/           # MicroDots change → static checks + build + boot + BROWSER proof (the only real proof)
    │  ├─ microdots-debug-blank/      # Blank/stale/unreachable MicroDot → staged diagnosis of the swallowed startup defect
    │  ├─ microdots-deploy/           # Route a MicroDots deploy: operator deploy screen, or emergency wrangler (never holds creds)
    │  ├─ microdots-content/          # Repo git history + wiki → branded, source-traced posts/changelogs/deep-dives/social
    │  ├─ microdots-brand-recap/      # BespokeAgentics/MicroDots brand shell + tokens + design rules for any explainer page
    │  ├─ microdots-design/           # Router to the impeccable-microdots plugin: visual refinement of real MicroDot views
    │  ├─ agent-loop-audit/           # AI API/SDK integration → event-loop defect audit + gated fixes (silent hangs, stop_reason, deadlocks)
    │  ├─ ai-native-sdlc/             # AI-Native SDLC playbook: assess 16-play maturity, scaffold controls, drive the intent→spec→plan artifact chain
    │  ├─ fast-ci/                    # CI → native-tool swaps (TS7, oxc, uv) + fast/slow lane split
    │  ├─ issue-to-agent/             # Triage labels → auto-dispatched repro/PoC coding agents
    │  ├─ chore-crons/                # Scheduled agents for the chores devs skip (regression backfill, SDK gaps, drift)
    │  ├─ proof-of-work/              # Agent evidence: screenshots, diffs, traces, storage + PR comments
    │  ├─ hermetic-deploy/            # One-command local instances, N at a time (Compose -p isolation)
    │  └─ sim-data/                   # Production-realistic deterministic seed scenarios
    ├─ commands/                      # Slash commands
    │  ├─ wiki/                       # Wiki commands
    │  │  └─ init.md                  # /wiki:init (the other /wiki:* commands are the flat wiki-*.md files below)
    │  ├─ glean/                      # Glean commands (namespaced)
    │  │  ├─ init.md                  # /glean:init
    │  │  ├─ add-tool.md              # /glean:add-tool
    │  │  ├─ add-adapter.md           # /glean:add-adapter
    │  │  └─ doctor.md                # /glean:doctor
    │  ├─ bun/                        # Bun Workspace commands (namespaced)
    │  │  ├─ analyze.md               # /bun:analyze
    │  │  ├─ convert.md               # /bun:convert
    │  │  ├─ audit.md                 # /bun:audit
    │  │  └─ add.md                   # /bun:add
    │  ├─ disclosure/                 # Progressive Disclosure commands (namespaced)
    │  │  ├─ map.md                   # /disclosure:map
    │  │  ├─ audit.md                 # /disclosure:audit
    │  │  └─ refresh.md               # /disclosure:refresh
    │  ├─ agentnative/                # Agent-Native Engineering commands (namespaced)
    │  │  ├─ suite.md                 # /agentnative:suite — scorecard + ordered dispatch of the six
    │  │  ├─ fast-ci.md               # /agentnative:fast-ci
    │  │  ├─ issue-to-agent.md        # /agentnative:issue-to-agent
    │  │  ├─ chore-crons.md           # /agentnative:chore-crons
    │  │  ├─ proof-of-work.md         # /agentnative:proof-of-work
    │  │  ├─ hermetic-deploy.md       # /agentnative:hermetic-deploy
    │  │  └─ sim-data.md              # /agentnative:sim-data
    │  ├─ knowledge/                  # Knowledge Loop commands (namespaced)
    │  │  ├─ init.md                  # /knowledge:init
    │  │  ├─ review.md                # /knowledge:review
    │  │  ├─ extract.md               # /knowledge:extract
    │  │  ├─ promote.md               # /knowledge:promote
    │  │  └─ audit.md                 # /knowledge:audit
    │  ├─ db/                         # Project DB commands (namespaced)
    │  │  ├─ init.md                  # /db:init
    │  │  ├─ query.md                 # /db:query
    │  │  ├─ sync.md                  # /db:sync
    │  │  └─ publish.md               # /db:publish
    │  ├─ ontology/                   # Project Ontology commands (namespaced)
    │  │  ├─ init.md                  # /ontology:init
    │  │  ├─ check.md                 # /ontology:check
    │  │  ├─ propose.md               # /ontology:propose
    │  │  ├─ approve.md               # /ontology:approve
    │  │  ├─ deprecate.md             # /ontology:deprecate
    │  │  ├─ apply.md                 # /ontology:apply
    │  │  └─ status.md                # /ontology:status
    │  ├─ funcspec-evaluate.md        # /bespoke-agentics:funcspec-evaluate
    │  ├─ funcspec-plan.md            # /bespoke-agentics:funcspec-plan
    │  ├─ funcspec-status.md          # /bespoke-agentics:funcspec-status
    │  ├─ repo-audit.md               # /bespoke-agentics:repo-audit
    │  ├─ highlight-reel.md           # /bespoke-agentics:highlight-reel
    │  ├─ codex-prompt.md             # /bespoke-agentics:codex-prompt
    │  ├─ prune-node-modules.md       # /bespoke-agentics:prune-node-modules
    │  ├─ ux-audit-*.md               # /bespoke-agentics:ux-audit-{a11y,code,quick,visual}
    │  └─ wiki-*.md                   # /wiki:new-client, :ingest-meeting, :ingest-document, :lint, :query, :status (flat files, namespaced by `name:`)
    │
    │  NOTE: capabilities that also ship as a skill have NO command file.
    │  They are invoked as /bespoke-agentics:<skill-name> — see skills/ below.
    │  Shipping both put duplicate entries in the slash picker; the wrappers
    │  were folded into their skills and deleted.
    ├─ agents/
    │  ├─ ui-frame-analyst.md         # UI screencast frame + narration analyst
    │  ├─ prototype-screen-analyst.md # Claude Design prototype module → screen profile + theater findings
    │  └─ wiki-pipeline.md            # Wiki orchestration agent (3 workflows)
    ├─ channels/
    │  └─ wireframe-feedback/         # Claude Code channel: wireframe browser comments → session (+ reply tool)
    └─ CLAUDE.md                      # THIS FILE — read first

## Getting Started

1. **Initialize a wiki**: Run `/wiki:init` — it will scan your repo, ask what you are working on, and create a tailored Obsidian vault
2. **Add a client or project**: Run `/wiki:new-client '<name>' '<platform>'`
3. **Ingest content**: Use `/wiki:ingest-meeting` or `/wiki:ingest-document`
4. **Check health**: Run `/wiki:lint --scope full`
5. **Search knowledge**: Run `/wiki:query '<question>'`
6. **Build a Glean agent**: Run `/glean:init` — interviews for framework choice, scaffolds a runnable Python project, and offers to install the upstream Glean SDK skills
7. **Consolidate sibling projects into a Bun workspace**: Run `/bun:analyze <dir>` for a read-only migration plan, then `/bun:convert <dir>` to execute
8. **Set up agent context across a codebase**: Run `/disclosure:map` — parallel subagents profile every subsystem, then it plans (with diffs) a layered CLAUDE.md/AGENTS.md hierarchy plus large-codebase config, and applies on approval. Use `/disclosure:audit` to check health and `/disclosure:refresh` to keep it current.
9. **Turn a Storybook into an implementation plan**: Run `/bespoke-agentics:funcspec-evaluate <workspace>` to infer the functionality the pages imply (page-by-page, with interviews), then `/bespoke-agentics:funcspec-plan` to validate findings and generate the spec, plan, backlog, and gap register.
10. **Make the project learn from every task**: Run `/knowledge:init` to scaffold the facts → hypotheses → rules store (inside `wiki/knowledge/`), install the before/after-task mandate in `CLAUDE.md`, and add a SessionStart hook. Then `/knowledge:review` before a task, `/knowledge:extract` after, `/knowledge:promote` to bridge confirmed rules into the wiki, and `/knowledge:audit` to keep the store honest.
11. **Audit a repository before investing in it**: Run `/bespoke-agentics:repo-audit` for a read-only, four-phase principal-engineer review that grades the repo A–F and returns severity-rated, `file:line`-cited findings plus a milestone fix plan with quick wins — without touching a line of code.
12. **Turn a screen recording into a plan (fix + improve)**: Run `/bespoke-agentics:ui-issue-to-plan '<video>'` — it reads the frames + narration to identify the UI components being referenced, grounds them in this repo's source (`file:line`), surfaces curated improvement opportunities, runs an interview that frames intent (fix vs improve) and lets you opt into enhancements, and writes a code-grounded plan to `./plans/` with separate Defect-fix and Enhancement sections. Use `--mode fix` for a quick bug-only pass.
13. **Pressure-test a plan or issue before you build it**: Run `/bespoke-agentics:plan-review '<artifact>'` — it decomposes a local plan/spec/issue into tasks, claims, assumptions, and acceptance criteria, grounds every referenced (and implied) component in this repo's real source (`file:line`) to surface the gaps the document hides, reviews it across completeness/feasibility/risk/clarity/scope, validates and prioritizes the findings via an interview, and writes a **read-only** review + color-coded gap register to `./reviews/` (the original is never modified). Use `--depth deep` for adversarially-verified findings on a high-stakes plan, or `--no-ground` for a document-only pass.
14. **Make a data-dense UI actually work**: Run `/bespoke-agentics:data-ui-craft` — it audits a dashboard, table, admin panel, or data grid against the three pillars (data drives the form · the right things hidden until needed · invisible UI), writes a severity-rated report in markdown + HTML with `DF*`/`PD*`/`IU*` findings cited to `file:line`, then — after an interview confirms what's in scope — applies the fixes in place and scaffolds a reusable React/Tailwind primitives kit. Use `audit` for a read-only pass.
15. **Make a feature's state logic explicit**: Run `/bespoke-agentics:xstate-refactor '<target>'` — it recovers the statechart the code already implements implicitly (parallel agents map every state variable, flag combination, event, effect, and UI dependency to `file:line`), designs the XState v5 machine/statechart/actor model with a mermaid diagram and a state↔UI coverage matrix, validates every inference via an interview, writes an executable migration plan to `./plans/`, then — only on approval — implements the machine, generates deterministic path-coverage + UI state-coverage tests, wires the UI so every state has a decided visual answer, installs XState if missing, and retires the old state code behind a grep-verified checklist. Use `--mode plan` to stop at the plan.
16. **Execute a plan through a managed multi-agent build**: Run `/bespoke-agentics:orchestrate '<plan.md>'` — the session model acts as orchestrator (it never writes production code): read-only agents re-ground every `file:line` anchor, a confirmed work order assigns each work item to Opus (contract-shaped/high-risk) or Sonnet (mechanical/smoke) with exact file ownership, waves run with orchestrator-executed gates between them, a smoke agent drives the running app with evidence-backed pass/fail, and a read-only Opus reviewer pressure-tests the diff before a faithful final report. Pass a raw task instead of a plan and it drafts + confirms one first; interrupted runs continue with `--resume`.
17. **Stop your AI integration from silently hanging**: Run `/bespoke-agentics:agent-loop-audit` — it detects your stack (TS/JS, Python; Anthropic pack when the SDK is present), discovers every place the code dispatches a task and consumes (or fails to consume) the event stream, audits each surface against the `EL*`/`SR*`/`RS*`/`OB*` catalog (listener-before-payload sequencing, `stop_reason` branching on idle, unanswered tool approvals, error differentiation, reconnect/resume, interrupt+redirect steering), and writes a severity-rated `file:line`-cited report with a loop-health matrix — then, after an interview confirms scope, applies the accepted fixes in place. Use `audit` for a read-only pass.
18. **Make CI fast enough for agents**: Run `/agentnative:fast-ci` — it measures the current `git push`→green wall-clock, audits the toolchain against the `TC*` native-rewrite catalog (TypeScript 7 native tsc, oxlint/oxfmt, uv, ruff, Biome, bun test) and the `LN*` lane rules, then — after an interview confirms each swap and the post-merge failure policy — migrates tools with official migrators, splits the pipeline into a <3-minute fast lane (`pull_request` + `merge_group`) with integration tests in the merge queue or post-merge, and proves the win with before/after timings.
19. **Dispatch agents from triage labels**: Run `/agentnative:issue-to-agent` — it designs a minimal label taxonomy, then generates claude-code-action v1 workflows: auto-triage on issue open, `agent:repro` → failing test on a `claude/` branch + repro-steps comment, `agent:poc` → spike branch + design notes — least-privilege, injection-aware, zizmor-verified, mandate ending at the handoff so the engineer picks up prepared ground, never an unsupervised fix.
20. **Automate the chores devs skip**: Run `/agentnative:chore-crons` — it inventories the neglected tail with git/grep evidence (untested critical paths, SDK coverage gaps, doc examples that no longer compile), scores value × automatability, and generates scheduled runners (Actions cron, Claude Code Routines, or Cowork tasks) where only self-verifiable chores get crons, each with a single rolling tracking channel, turn budgets, and a double-fire idempotency test.
21. **Let agents prove their work**: Run `/agentnative:proof-of-work` — it installs agent-browser (or wires incumbent Playwright), establishes the `evidence/` manifest convention and `scripts/evidence.sh` verify loop, sets up storage (S3/R2 presigned URLs for inline PR images, artifacts v4 for traces) and a create-or-update PR evidence comment — then proves the whole chain once on a throwaway PR, including a determinism check.
22. **Give every agent its own running app**: Run `/agentnative:hermetic-deploy` — it audits against the `H*` hermeticity catalog (fixed host ports, host-shared state, missing healthchecks, unseeded DBs), then builds Compose `-p` namespacing, ephemeral ports, in-stack mocks for externals, and the `scripts/dev-stack.sh` contract (`up <id>` → healthy seeded URL) — verified by actually running N instances side by side with isolation, teardown, and cold-start measured.
23. **Make the whole repo agent-native in one pass**: Run `/agentnative:suite` — it scores all six dimensions 🟢/🟡/🔴 with evidence into `./plans/agentnative-suite.md`, interviews once for dimension selection, per-dimension mode, and budget, then dispatches the skills in dependency order (fast-ci → hermetic-deploy → sim-data → proof-of-work → issue-to-agent → chore-crons), resumable via `--resume`. Use `assess` for the scorecard only.
24. **Seed data that looks like production**: Run `/agentnative:sim-data` — it mines prod shapes via read-only aggregates (skew, null rates, charset reality, the whale account — values never leave unmasked), then builds deterministic scenarios (`default`/`demo`/`edge`/`load`) via copycat + seeded faker or a Greenmask/anon pipeline with a named-human masking review gate, wired into hermetic-deploy's seed hook and proven by double-seed byte-identical diffs.
25. **Turn a long demo recording into a highlight video**: Run `/bespoke-agentics:highlight-reel '<video>'` — the creation companion to the analysis skills. It preprocesses the screencast (frames + word-timed transcript), builds a salience-scored moment catalog, grounds every demonstrated feature in this repo's source (`file:line`) so the voiceover states verified facts, proposes a ranked cut, and runs an interview to confirm the moments/order/length/voice/audio before rendering. It then writes a grounded narration + `reel-plan.json`, synthesizes a voiceover via ElevenLabs TTS (`scripts/tts.py`; omit with `--no-tts` for captions only), and renders a subtitled highlight `.mp4` with ffmpeg (`scripts/assemble_reel.py` — cut, mix, freeze-extend, concat, burn). Edits are a quick re-run off `reel-plan.json`.
26. **Build a plan workstream-by-workstream, committing each**: Run `/bespoke-agentics:workstream-orchestrate '<plan-path-or-task>'` — the sequential, commit-as-you-go sibling of `orchestrate`. It generates a human-confirmed **kickoff contract** from the plan (10 sections: mission, gates, guardrails, workstreams, hard gates, definition of done), then drives it **one workstream at a time** through a bounded `code → validate → commit` **Workflow**: an implementer applies only that workstream's scope, an independent adversarial validator re-runs the gates and **proves or refutes the plan's server-side hard gates** (crafted input against the authoritative layer, never client-side hiding), and only a green, validated workstream earns **one Conventional Commit** — followed by a human checkpoint before the next. Failing validation loops back (≤`--attempts`) then halts and surfaces the findings. The driver never writes production code; given a raw task it drafts and confirms a plan first. Resumable under `.workstream/<slug>/`; degrades to `--engine agent` when the Workflow tool is absent, or `--dry-run` for the contract only.
27. **Record a browser demo, then make a reel**: Run `/bespoke-agentics:screencast-capture '<start-url-or-flow>'` — the **capture** companion to `screencast-highlight-reel`: it _produces_ the screencast that skill polishes, so you never have to screen-record yourself. It drives a live **Claude-in-Chrome** session — an AskUserQuestion interview turns your request into a shot list, it opens a fresh tab and **pauses for you to log in before recording** (credentials stay out of the footage; the agent never types secrets), records the flow step-by-step with the `gif_creator` tool (click indicators only by default), and exports the GIF. For higher fidelity, **`--engine screen`** instead records a chosen monitor with ffmpeg at **native resolution + configurable bitrate** (`--display` / `--crf`) — the fix when the default tab capture (hard-capped ~1200px, dithered GIF) looks grainy; it needs macOS Screen-Recording permission and records the whole monitor (auto-cropped to the browser window). The gif engine then **converts the GIF to a real-duration MP4** (`scripts/gif_to_mp4.sh`; the screen engine writes MP4 directly) — a GIF reports no container duration, so the reel would otherwise drift on frame-index timings — presents the MP4, and (by default) asks whether to hand off to `/bespoke-agentics:highlight-reel` (`--reel`/`--no-reel` to force/skip), forwarding `--no-tts` (no ElevenLabs key) and `--no-ground` (site isn't this repo's app) as needed. Degrades gracefully (no ffmpeg → stops before recording; unclearable login → captures what's reachable or stops).
28. **Settle an undecided UI before building it**: Run `/bespoke-agentics:interactive-wireframe '<surface>'` — it grounds the surface in this repo's real source (design tokens, typography, the literal enums/labels the UI displays, roles and permission flags, the layout components the change touches — each cited to a path, never invented), emits **one self-contained HTML wireframe** (inline CSS + JS, no build step) carrying a **control overlay generated from the axes that surface actually varies on** — role switcher, entity states, permission toggles, data extremes, behavioural thresholds, layout variants, zone guides, live state readout, with state mirrored into the URL so any configuration is a shareable link — serves it on **8791** (8787 is never auto-probed; `file://` fails under browser automation), then interviews in AskUserQuestion rounds of ≤4 with concrete ASCII previews, **rebuilding the wireframe between rounds**, surfacing contradictions between your answers instead of silently reconciling them, and offering switchable variants side by side instead of arguing about aesthetics — while a **browser comment mode** (✎ or `c` in the wireframe) lets you pick any element and comment on it, the comment reaching the session with its selector, zone, and exact on-screen state, and replies threading back into the page's comment panel (instantly, when the optional `wireframe-feedback` channel is loaded; drained between rounds otherwise). It verifies by **measurement** — region contiguity, computed WCAG contrast, markup validity, off-screen focusables, scripted behaviour sequences — with the backgrounded-tab failure modes (scroll events, rAF, transitions and `.focus()` all silently no-op in a hidden tab) encoded as a hard checklist, labelling anything unmeasured "not verified" rather than claiming it. Ends at a spec grounded in real file paths, in the wiki or `./plans/<slug>.md`, then **auto-harvests a per-project reuse library** (`wireframes/_library/`: grounding cache, fragment files, decisions ledger + `wireframes/_index.md`) so the next wireframe in the same repo starts warm — cached values TTL-trusted and honestly labelled (`--ttl`, default 14 days; `--fresh` to bypass), prior verdicts imported as fixed context with one "reopen?" affordance. Composes both ways with `spec-elicitation`. **Writes no production code.**
29. **Confirm the build matches the wireframe**: Run `/bespoke-agentics:wireframe-parity '<spec-or-slug>' --app <url>` — the **post-implementation** companion to `interactive-wireframe`. Once a wireframe spec has been built, it confirms the as-built UI matches what was decided, reusing the intended design the wireframe already froze (the spec's **Verification** `__wf` numbers, **Contract** invariants, **Decisions** table + `_library/decisions.md` ledger, and **States** table). It runs a **structural** pass (parallel `Explore` agents ground every settled decision/state/label in the real implementation at `file:line`, honored/drifted/missing — the floor, available under `--no-browser`) and a **measured** pass (serves the wireframe via `serve-wireframe.sh`, injects the **same** dependency-free probe — `wf-probe.js`, a standalone copy of `__wf` — into **both** the wireframe and the running app, drives each to the matching state, and diffs band geometry / contrast / markup / focusables / rendered labels / tokens apples-to-apples, parity being invariant-**within-tolerance** — ±2px, same AA/AAA verdict, contiguity as required — not pixel-identity). Auth-gated states are labelled **"not measured"**; a backgrounded-tab behavioural "failure" is treated as an artifact. Because **spec Decisions are the parity contract** and a build sometimes evolves past the wireframe on purpose, an **AskUserQuestion** interview classifies each divergence as **regression** / **intended evolution** / **out of scope** before any is called a failure (`--depth deep` adversarially verifies each first). Writes a **read-only** report to `./reviews/` — parity verdict (🟢/🟡/🔴), a decision-by-decision parity table, a measured table (intended / spec-frozen / as-built / Δ), label fidelity, a color-coded divergence register, an honest "not measured" section, and a "definition of parity" checklist — then **offers** to open the P0 regressions as tasks or refresh the stale ledger. Distinct from `plan-review` (audits a document before build) and `ux-audit` (heuristics): this audits a **built UI against the wireframe that specified it**. **The implementation is never modified.**
30. **Explore what an existing surface could become**: Run `/bespoke-agentics:reimagine '<surface>'` — the **upstream sibling** of the wireframe pair (_reimagine explores **which** design, `interactive-wireframe` settles **the** design, `wireframe-parity` checks the build_). It recreates the Current design **from source as an honest baseline** (structure, labels, tokens transcribed and cited `path:line` into a Baseline-fidelity section; optionally cross-checked against the running app via `wf-probe.js`, with a fidelity chip — `cross-checked <date>` or `code-grounded, not pixel-checked` — that never lies), pitches **two direction briefs per ambition tier** (Restyle / Restructure / Rethink — tiers are _contracts_ policed by mechanical proxies, so a Rethink that is secretly a restyle gets demoted), and lets you **pick directions in an interview round before anything is built**. The picked directions become real sibling panes in **one self-contained HTML gallery** (`wireframes/<slug>/reimagine-v1.html`, derived byte-faithfully from the wireframe scaffold, drift-checked) with a variant switcher, **single/grid/split** views, and **shared axes that hit every pane at once** — flip "empty" and all variants answer; browser comments arrive tagged with their pane. All variants are **brand-faithful**: one shared grounded token block; leaving the design system is a pitch that must be approved. Served by the parent's `serve-wireframe.sh` reused in place (8791, never 8787). The interview arcs **reaction → critique (works/breaks/what to steal) → hybridization** — a chosen hybrid is **rebuilt as a real pane** in `reimagine-v2.html`, never hand-waved — **→ winner**, with per-loser rejection reasons confirmed from critique evidence. The winner gets the full measurement battery in single view, and the spec lands with the **divergence-from-current inventory** (Δ rows: Current at `path:line` → becomes → change class — the implementer's worklist), rejected directions (brief vs gallery), two verification tables (the winner's in wireframe-parity-consumable format), and **offered** handoffs to `interactive-wireframe` (fine-grained settlement) and orchestrate (build). Shares the wireframe **reuse library** (runs typed `wireframe`|`reimagine`; rejected variants' styles never harvest). **Writes no production code.**
31. **Clean up after a coding session**: Run `/bespoke-agentics:dead-code-sweep` — it resolves a scope (`uncommitted` by default, `branch` vs its merge-base, or `project`), runs the repo's own gates FIRST to record a baseline (no gates → no autonomous deletion; broken baseline → report-only), finds candidates by tracing what the diff stopped referencing plus the ecosystem's native detectors, cross-checks every candidate against a liveness checklist (dynamic/string references, framework conventions, public API, keep-markers), then removes in gated waves: high-confidence auto-removed with gates re-run after every wave (a new failure restores the code — the failing test proved it alive and is never deleted to get green), medium batch-confirmed in one interview, low report-only. Stale tests/mocks/snapshots go with their subjects; cascades converge in waves; everything is backed up under `.dead-code-sweep/<ts>/` with one-command restore; nothing is ever committed. Use `--report-only` for a read-only pass.
32. **Harden a skill that behaves differently every run**: Run `/bespoke-agentics:skill-reverse-engineer '<skill>'` — it reconstructs what one run of the target skill actually does (step graph, each step classified `script` / `model-mechanical` / `model-judgment` / `user-gate` via the distill test: _would two competent runs be wrong to differ?_), audits it against the `DS*/TP*/CT*/VF*/AM*/RB*/KM*` catalog with a bundled deterministic inventory script, and **grounds the audit in the host project** it runs in (a bounded `host_probe.py` enumerates stack, data schemas, data stores) so the target's per-run LLM lookups can be **materialized** into generated fact files — a configuration matrix mined from the host's schema, with `_provenance` (mined-with-SHA256-`--check` or declared-by-interview; a frozen guess is unrepresentable) consulted via a check → regenerate → derive-fresh-and-label ladder. The report separates findings from the **essential-judgment register** (the AI-reliance that should stay); nothing is edited before the interview gate; `--mode apply` refactors in place, `--mode new-version` emits a drop-in hardened copy with a diff summary, and every shipped script/generator is executed (including a drift-check tamper test) before it ships. Use `--mode audit` for the read-only report.

33. **Turn a Claude Design prototype into a MicroDots build plan**: Run `/bespoke-agentics:microdots-port-prototype '<artifact.html>'` — the front half of a MicroDots port for products that only exist as a design. A Claude Design export is not a screenshot: its `__bundler/manifest` carries the **original hand-written source**, so the run opens with a deterministic extractor (`scripts/extract_design_bundle.py`) that recovers a real source tree — app modules in true load order, vendor libraries separated, design-token stylesheets, fonts — turning an opaque 1.8 MB HTML file into evidence with real `file:line` anchors. It then classifies every module (screen · data-store · chrome · ui-kit · scaffold), maps the `window.*` read/write graph, and runs the analysis a prototype (unlike a real app) requires: **inference, not tracing**. A Stage-1 interview frames purpose, roles, backend reality, auth, non-goals — plus the two questions only a prototype raises: which screens are the product versus demo filler, and how faithful the visual design must stay. Parallel `prototype-screen-analyst` agents then read each module into a schema-valid screen profile, separating what genuinely works from **demo theater** — `setTimeout(…, 720)` standing in for a query, handlers that only mutate local arrays, hardcoded AI answers, no-op controls — because every faked interaction names a service that does not exist yet. Mock data is read as the **entity model's best evidence** (typed conservatively, enums captured, relations inferred), never as seed data. Synthesis merges entities, routes, features and shared services, then crosses the `window.*` graph with the feature domains to derive **candidate MicroDot cut lines** with their crossings — evidence for composition, never the composition decision. A Stage-2 interview validates everything: features confirmed or cut, each theater finding dispositioned **implement / mock / drop**, blocking ambiguities resolved (never silently deferred), priorities set. It then writes the dossier in exactly the artifact names `microdots-port-app` already reads (`trace.md`, `ui-inventory.md`, `synthesis.json`, `seams.md`) plus a `dossier-manifest.json` declaring which phases are pre-satisfied, and **hands off** — port-app runs composition (user-gated), port maps, the Effect-optimization register, spec elicitation, and, on `--mode scaffold|full`, the build. Default `--mode plan` stops at the validated plan; `--serve` adds a real browser walk, without it every UX claim is labeled "not visually verified". Non-Claude-Design input is **redirected, not half-handled** (real app → `microdots-port-app`, Storybook → `funcspec`). Writes no production code.

34. **Refine how a MicroDot looks**: Run `/bespoke-agentics:microdots-design` — a router, not a second copy of design guidance. It resolves the workspace, confirms this is a MicroDots repo, and hands off to the **`impeccable-microdots`** plugin (a fork of [Impeccable](https://github.com/pbakaus/impeccable) by Paul Bakaus, Apache-2.0, adapted for this framework and listed in `.claude-plugin/marketplace.json`). Three things make the fork necessary rather than cosmetic: the class vocabulary is **enforced by a test that fails the build** (`palette-usage.test.ts` rejects every Tailwind palette literal, which otherwise compiles and renders and simply stops responding to `[data-theme]`); four Tailwind defaults are remapped and two invert (`rounded-lg` is 14px, `tracking-tight` is _positive_ button tracking, `text-xs`/`text-sm` do not exist and fail nothing while breaking the type scale); and Foldkit views are **hyperscript**, so a variant cannot be spliced HTML. Live variants are therefore real view functions run inside the dot's own program in a generated harness, because the shells load built bundles and `defineMicroDot` refuses to redefine a registered tag, so a rebuilt bundle is silently discarded in a live page. Accept writes source once and then runs format → `bun run check` → a dot build → a render gate, restoring the file if any fails; `Runtime.embed` swallows startup defects, so a green build can still be a blank panel with a clean console. Sits beside `reimagine` (explores which design), `interactive-wireframe` (settles the design) and `wireframe-parity` (checks the build): those write no production code, this one does.

35. **Correct a wrong inference before it compounds**: Run `/bespoke-agentics:misunderstanding ['<what was misunderstood>']` — for the moment a plan step, a wiki claim, a doc, or an earlier turn led to a reading that was wrong and work is already sitting on top of it. Restating in prose fixes the conversation and nothing else: the misleading claim stays in the source, and the contaminated work stays in the tree. Like `defect-intake` it is **user-invoked only** and never self-triggers. It reconstructs an **inference ledger** — every belief paired with the **verbatim source text** that produced it, labeled `stated` / `inferred` / `assumed-from-silence`, which are three different defects with three different fixes — scopes to the flagged belief's **blast radius** (siblings from the same source, dependents; not a session-wide audit), then interviews in specifics: every `AskUserQuestion` **quotes its source**, leads with the current belief as a one-click confirmation, and offers the alternative readings a competent person could have taken from the same words (≤4 per call, ≤3 rounds, ordered by blast radius). Contradictions between the correction and what the artifact actually says are **surfaced, never reconciled**. It then corrects the source (repo docs edited; wiki updated and logged with **raw sources never modified**; external content reported verbatim, never edited), inventories the work built on the error and offers **keep / revise / revert per item** — never auto-reverting — records proportionally via `defect-intake`'s documentation routing, feeds a knowledge store when one exists, and resumes with a corrected restatement in its own words. A verified non-misunderstanding is a successful run. **Never commits.**

36. **Make the whole development process AI-native**: Run `/bespoke-agentics:ai-native-sdlc` — it implements Anthropic's AI-Native SDLC playbook around the committed-artifact chain (`intent.md` → `spec.md` → `plan.md` → diff+tests → reviewed PR → incident record) with humans at every gate. `assess` (default) probes the repo for evidence of each of the 16 plays and writes a 🟢/🟡/🔴/⚪ scorecard with a dependency-ordered adoption path; `adopt` scaffolds the chosen plays as real, verified files adapted to the repo's own commands and named gate owners (artifact templates, tuned `CLAUDE.md`, seed policy skill, protected-path/secrets/test-protection hooks tested on both allow and block fixtures, `REVIEW.md`, verifier subagent, agent-evals CI, `bands.yaml`) behind one interview, merging settings additively and never committing; `run` drives a single work item through the chain gate by gate, offering the commit at each acceptance because the commit trail is the control. Composes with `spec-elicitation`, `plan-review`, and `orchestrate`; complementary to `/agentnative:suite` (workspace layer vs. process layer).

37. **Tell a PM what actually shipped**: Run `/bespoke-agentics:delivery-recap` — it answers the question behind every status request: *is the thing I asked for there, and how do I go look at it?* A bundled stdlib-only collector gathers the window (default **last 24 hours**; override with "this week", "since Monday", "last 3 days") from four sources — commits, uncommitted working-tree changes, **Claude Code session transcripts** (what the engineer was trying to do, in their own words, including intent that never became a commit), and wiki edits — with a `notes` array recording everything unavailable so the report's blind spots stay visible. It reads the real diffs (parallel `Explore` agents when several areas changed), groups them into **deliverables rather than commits**, and **traces every changed UI file up to the route that renders it** — a reader cannot open `InvoiceTable.tsx`, but they can open `/admin/invoices`; a shared component's blast radius is enumerated and a genuinely invisible change is said to be invisible. Backend work is described by effect (which column, nullable, migration run or not, backward compatible or not), with **new required env vars called out as the deploy blockers they are**. One question confirms the base URL from candidates grepped out of the README and deploy config; then the payload — numbered steps naming what the reader should see, **contrasted with what it replaced**. Every claim is labeled **verified / inferred / unconfirmed**, and anything whose user-visible effect can't be established gets an honest section instead of an invented rationale. Lands as markdown in `./reports/` **and** a shareable Artifact. Read-only: never edits code, never commits.

38. **Give agents SQL over the project**: Run `/db:init` — with a wiki present it builds the schema *from* the wiki (base tables for pages, frontmatter fields, resolved wikilinks, tags, sources, sections, cited raw documents, FTS5; one typed view per page type with column docs mined from `_schema/templates/`; curated views such as `open_gaps`, `pending_decisions`, `backlinks`, `broken_links`), vendors a stdlib-Python engine into `.claude/db/`, and installs the guarded query CLI (read-only authorizer, one statement, 200-row cap, 5 s timeout, CSV, audit log), a SessionStart hook that syncs incrementally and prints a banner, a local stdio MCP server, and a CLAUDE.md block that makes the database the first stop for structured questions while the wiki stays the record. Without a wiki it interviews you, scans the repo, maps sources to collections (`--markdown adr=docs/adr`, `--tabular data/x.csv`) and installs a DB-first mandate. Then `/db:query '<question>'` answers with one SELECT and cites pages, `/db:sync` keeps it fresh, and `/db:publish` pushes the same schema to Cloudflare D1 behind a read-only MCP Worker (modes `d1`/`both`).

39. **Stop vocabulary drift for good**: Run `/ontology:init` — it scans the wiki (page types, template `key: # a|b|c` comments, SCHEMA.md value lists, observed values, scope folders, tags, frontmatter link fields), interviews you only on what the scan cannot decide (template-vs-SCHEMA conflicts, values no one declared, spelling variants of a client, which tags to trust), and writes `wiki/_schema/ontology.yaml` — dot-notated terms (`gap.severity.critical`, `client.acme-corp`, `rel.related-feature`) with a proposed → approved → deprecated lifecycle — plus a rendered `ONTOLOGY.md`, template comments that name their binding, a CLAUDE.md block, a SessionStart banner, and the guard hooks. From then on a Write/Edit that adds an unregistered, misspelled or deprecated value or a broken/ambiguous/noncanonical link is blocked with the approved values and the propose command in the message, while problems already on a page never block (ratchet); a new concept goes through `/ontology:propose` (usable at once) and `/ontology:approve` (humans only); `/ontology:apply` rewrites the mechanical cases; project-db exposes `ontology_violations` for SQL and wiki-lint reports the dimension as Check 8.

## Quality Standards

- All wiki pages must have valid YAML frontmatter
- All pages must have at least one `related:` back-reference
- No orphan pages (every page reachable from `_index.md`)
- No broken `[[wiki-links]]`
- Status fields use defined enums only
- Dates use ISO 8601 format (YYYY-MM-DD)
- File names use `lowercase-kebab-case.md`

Run `/wiki:lint --scope full` to check compliance.
