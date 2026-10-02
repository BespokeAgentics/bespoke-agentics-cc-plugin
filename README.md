# bespoke-agentics

A Claude Code plugin with AI transparency auditing, agent architecture generation, Pi harness customization, UX evaluation, video-to-deliverables pipelines, workflow analysis, and a Karpathy-style LLM wiki knowledge system.

## Installation

Add this repository as a marketplace, then install the plugin:

```bash
# Add the marketplace
claude plugin install bespoke-agentics@https://github.com/BespokeAgentics/bespoke-agentics-cc-plugin

# Or test locally during development
claude --plugin-dir ./bespoke-agentics-plugin
```

## Skills

> Every skill and command is manual-only (`disable-model-invocation: true`): type `/bespoke-agentics:<name>` to run it. The only exceptions are the eight commands in `scripts/invocation-policy.json`, which installed mandates tell an agent to run.

### Primary Skills

| Skill | Description |
|-------|-------------|
| **ai-transparency** | Audit and fix AI operations lacking UI state coverage (loading, streaming, logs, errors). Enforces the "No Black Boxes" policy. |
| **architect-agents** | Analyze a project and generate a complete `.claude/agents/` and `.claude/commands/` architecture with documentation. |
| **ux-audit** | Comprehensive UX evaluation using Nielsen's 10 Heuristics and Norman's 6 Design Principles. See ux-audit-* variants below for narrower scopes. |
| **video-to-deliverables** | End-to-end video analysis pipeline. Transforms recordings into workflow docs, migration analysis, meeting summaries, or training guides. |
| **workflow-analyzer** | Client workflow analysis from video recordings. Produces application inventory, challenge mapping, and AI automation recommendations. |
| **setup-plugin** | Scaffold, optimize, and package a folder as a well-formed Claude Code plugin. Converts `.claude/` directories into distributable plugins. |
| **pi-assistant** | Understand the pi.dev coding agent, customize its harness, build Pi skills/extensions/packages, and search for or install Pi packages. |
| **spec-elicitation** | Interview-driven spec development that turns vague ideas into complete implementation specifications. Also available as `/bespoke-agentics:spec-elicitation`. |
| **biome-guardrails** | Install Biome.js + sidecar ESLint as strict AI-code guardrails in a JS/TS project — or audit an existing codebase for weak-typing debt (`--audit`) and install ratchet enforcement that blocks new `any` and oversized files without breaking the build (`--ratchet`). |
| **bun-workspace** | Convert sibling Node/Bun repos into a Bun workspace monorepo, audit one, or add a package. |
| **git-submodules** | Add/convert/init/audit Git submodules safely. |
| **session-hooks** | Design Claude Code SessionStart/SessionEnd/Stop hooks via interview. |
| **mcp-server-scaffold** | Scaffold a safe-by-default HTTPS MCP server in Bun or Go, add tools to one, or audit one. |
| **glean-agent-toolkit** | Scaffold/extend Glean Agent Toolkit (Python) projects across OpenAI SDK / LangChain / Google ADK. |
| **ai-waiting-ux** | Audit/scaffold real-time AI waiting UX in Next.js + claude-agent-sdk projects. |
| **codex-prompt-builder** | Convert session context, bug reports, or feature notes into a Codex prompt. |

### Pi Assistant

All Pi tasks route through the `pi-assistant` skill. Describe the task in natural language ("build a Pi extension that…", "search Pi packages for browser automation", "review my local Pi setup", "install Pi package X globally") and the skill routes to the right surface — harness customization, extension/skill/package authoring, package search, install, or setup review. See `skills/pi-assistant/SKILL.md` and its `references/` for surface-by-surface guidance.

### UX Audit Variants

| Command | Description |
|---------|-------------|
| `/bespoke-agentics:ux-audit-code` | Code-only audit against UX anti-pattern library |
| `/bespoke-agentics:ux-audit-visual` | Visual analysis of screenshots, GIFs, or video |
| `/bespoke-agentics:ux-audit-quick` | Quick heuristic spot-check on a single component |
| `/bespoke-agentics:ux-audit-a11y` | Accessibility-focused audit (ARIA, keyboard nav, color) |

### Wiki Skills

A Karpathy-style LLM wiki system that serves as the single source of truth for project intelligence, technical decisions, and business capabilities. Built on Obsidian-compatible Markdown with YAML frontmatter, cross-referenced `[[wiki-links]]`, and schema-enforced page types.

| Skill | Command | Description |
|-------|---------|-------------|
| **Wiki Init** | `/wiki:init` | Initialize a new Obsidian wiki vault. Scans the repo for context, asks clarifying questions, then creates the vault structure, schema, page templates, and global indexes. |
| **Wiki Scaffold Client** | `/wiki:new-client` | Create a new client workspace from a template. Derives folder structure, creates entity pages, ingests initial context documents, and populates a README with project overview. |
| **Wiki Ingest Meeting** | `/wiki:ingest-meeting` | Ingest a meeting transcript or analysis pipeline output. Creates or updates feature, gap, question, and decision pages, then links all entities to the new meeting summary. |
| **Wiki Ingest Document** | `/wiki:ingest-document` | Ingest a lightweight document (email, PDF, spec, Slack message). Updates affected feature, gap, decision, and question pages with new information. |
| **Wiki Query** | `/wiki:query` | Natural language search across wiki pages. Synthesizes answers with citations and optionally promotes substantive answers to new wiki pages. |
| **Wiki Lint** | `/wiki:lint` | Run an 8-dimension health check: broken links, orphaned pages, contradictions, stale content, missing cross-references, frontmatter errors (against the vault's own vocabulary), decision drift, and — with project-ontology installed — ontology violations. Optionally auto-fixes. |
| **Wiki Confluence Reconcile** | Skill only | Detect drift between the wiki and Confluence exports, generate reconciliation reports, and optionally sync changes bidirectionally. |

**Wiki slash commands** provide quick access to common operations:

| Command | Description |
|---------|-------------|
| `/wiki:init` | Initialize a new wiki vault |
| `/wiki:new-client '<name>' '<platform>'` | Scaffold a client workspace |
| `/wiki:ingest-meeting '<name>' '<dir>' '<label>'` | Ingest meeting outputs |
| `/wiki:ingest-document '<name>' '<path>' '<type>'` | Ingest a document |
| `/wiki:query '<question>'` | Search and synthesize wiki knowledge |
| `/wiki:lint --scope full` | Run full health check |
| `/wiki:status` | Display wiki health dashboard |

### Project DB — SQL for agents

Gives agents **one tool, SQL, over everything the project knows**, with the guardrails a data team puts in front of a read replica. With a wiki present, the schema is built *from* the wiki: base tables (pages, frontmatter fields, wikilinks, tags, sources, sections, cited raw documents, FTS5) plus one typed view per page type whose column docs come from the page templates, and curated cross-type views (`open_gaps`, `pending_decisions`, `backlinks`, `broken_links`…). Without a wiki it interviews you, scans the codebase, designs the schema, and installs a DB-first mandate. Same schema on SQLite locally and Cloudflare D1 remotely.

| Command | Description |
|---------|-------------|
| `/db:init [--mode local\|d1\|both]` | Build the database, vendor the engine into `.claude/db/`, install the guarded query CLI, SessionStart sync hook, local MCP server, and the CLAUDE.md mandate |
| `/db:query '<question or SELECT>'` | Answer a structured question with one read-only SELECT (row cap, timeout, CSV, audit log), then cite the source pages |
| `/db:sync [--full]` | Incremental refresh by content hash; regenerates typed views, re-applies `views.sql`, rebuilds FTS, rewrites `SCHEMA.md` |
| `/db:publish` | Export to D1, dry-run on local D1, push with wrangler, deploy the read-only MCP Worker, smoke-test, log |

Guardrails: read-only connection + SQLite authorizer, one statement per call, 200-row cap, 5 s timeout, cells truncated at 400 chars, every query audited (`python3 .claude/db/db.py audit --top` shows which repeated queries deserve a view). Requires `python3`; `uv` for the local MCP server; `wrangler` for D1.

### Project Ontology — an enforced, dot-notated vocabulary

A vocabulary written in a schema document drifts the week it is written: this plugin's own sample wiki had four disagreeing value lists and one client spelled two ways across 50 pages. `/ontology:init` mines what the vault already declares and uses — page types, template `key: # a|b|c` comments, SCHEMA.md value lists, observed values, scope folders, tags, link fields — into one file, `wiki/_schema/ontology.yaml`, of dot-notated terms (`gap.severity.critical`, `client.acme-corp`, `tag.budget-management`, `rel.related-feature`) with a proposed → approved → deprecated lifecycle. Pages keep plain values; page ids are derived from paths (`client.acme.gap.co-op-billing`). Declared values are approved, observed-only values are proposed — nothing is silently approved — and an interview settles the conflicts.

One engine enforces it everywhere: a **PreToolUse hook** blocks any write that *adds* a strict violation (unregistered or misspelled value, deprecated term, broken/ambiguous/noncanonical `[[link]]`, wrong relation target) and names the approved values and the propose command — violations already on a page never block (ratchet), so an existing vault adopts it on day one; a **PostToolUse hook** reports what still stands; a **Bash guard** turns approvals into a permission prompt and blocks shell writes into pages; a **SessionStart banner** keeps the vocabulary in context; CI runs `check --changed-since`; **project-db** loads `ontology_terms` / `ontology_violations`; **wiki-lint** reports it as Check 8.

| Command | Description |
|---------|-------------|
| `/ontology:init` | Scan the vault, interview on conflicts and outside values, write `ontology.yaml` + `ONTOLOGY.md`, sync template comments, install hooks, banner and CLAUDE.md block |
| `/ontology:check [<path>\|--all\|--changed-since <ref>]` | The write hook's rules on demand; exit 1 on strict violations; `--format lint\|json` |
| `/ontology:propose <id> --label … --definition …` | Register a value the vocabulary lacks (usable at once, flagged until approved) |
| `/ontology:approve <id>…` | Human gate: confirm pending terms and record who approved them |
| `/ontology:deprecate <id> --replaced-by <id>` | Human gate: retire a term; pages using it are flagged and `apply` rewrites them |
| `/ontology:apply [--dry-run]` | Rewrite aliases, spelling variants, deprecated values and noncanonical links to canonical form — nothing else |
| `/ontology:status` | Terms by status, policy, open violations by rule, pending approvals |

Requires `python3` only (stdlib; never PyYAML, so every machine checks the same way).

### Utility Skills

These are shared across the video and workflow pipelines:

| Skill | Description |
|-------|-------------|
| **extract-video-frames** | Extract frames and audio segments from video files using FFmpeg |
| **dedupe-frames** | Remove near-duplicate frames using perceptual hashing |
| **elevenlabs-transcribe** | Transcribe audio/video using ElevenLabs Scribe v2 API |

## Skill reference

Full descriptions of each skill family. The command tables that route to them live in [`CLAUDE.md`](CLAUDE.md) § Wiki-First Mandate.

### When to Use Each Progressive Disclosure Command

The Progressive Disclosure skill builds the _context/memory_ layer (per-directory CLAUDE.md is the source of truth; AGENTS.md points to it) plus the supporting `.claude/` config (Read deny rules, `additionalDirectories`, `claudeMdExcludes`, a SessionStart hook, code-intelligence recommendations). It deploys parallel subagents to profile every subsystem and, if a wiki is present, mines it for context and logs the operation. It is complementary to `architect-agents`, which builds the _agent/command_ layer — the two do not overlap.

### When to Use Each Funcspec Command

The Funcspec skill is the companion to `claude-design-to-app-workflow` (`design-zip-to-library`): that skill recovers the _visual_ layer; `funcspec` extracts the _functional_ layer. It launches parallel `page-evaluator` agents (code-first, with optional visual verification against running Storybook), brackets the analysis with two AskUserQuestion interviews (Stage-1 frames intent, Stage-2 validates every inference), and emits deliverables using the Decision Status Colors below. Works on any Storybook workspace; uses a `design-zip-to-library` `analysis.json` as a fast path when present. Deliverables are wiki-ingested when a vault exists.

### When to Use Each Knowledge Loop Command

The Knowledge Loop skill is the project's _learning layer_: a lightweight facts → hypotheses → rules store (one trio per domain) that compounds across tasks. It is **wiki-first compatible by design** — the store lives inside the vault at `wiki/knowledge/` (so `/wiki:query`, `/wiki:lint`, and `/wiki:status` see it), and confirmed rules are **promoted into proper wiki pages**, satisfying the mandate that validated knowledge become wiki content. Evidence is strict: every confirmation/contradiction must cite a distinct, dated, linkable source, so `rules.md` stays trustworthy enough to **apply by default**. `init` writes the before/after-task mandate into `CLAUDE.md` and installs a SessionStart hook that surfaces the active rules, so the loop fires without being invoked. Promotion bar: `confirmations ≥ 3` (distinct) and `contradictions = 0`; a single contradiction demotes a rule back to a hypothesis.

### When to Use Each Project DB Command

The Project DB skill is the wiki's _query layer_: the wiki stays the record, the database at `.claude/db/project.sqlite` is the index. `init` builds the schema **from** the wiki — base tables (pages, `page_fields`, `links`, `tags`, `sources`, `sections`, `raw_documents`, FTS5) plus one typed view per page type with column docs mined from `_schema/templates/`, and curated views (`open_gaps`, `pending_decisions`, `open_questions`, `backlinks`, `broken_links`, `meeting_mentions`…). It vendors a stdlib-Python engine into `.claude/db/db.py` so the SessionStart hook (incremental sync + banner), the guarded CLI (`db.py query`: read-only authorizer, one statement, 200-row cap, 5 s timeout, CSV, audit log), the local stdio MCP server and the D1 Worker share one policy. Agents read `.claude/db/SCHEMA.md` (generated schema-as-prompt) before writing SQL and promote repeated queries into `.claude/db/views.sql`. With no wiki, `init` interviews + scans the repo, maps sources to collections (`--markdown adr=docs/adr`, `--tabular data/x.csv`) and installs a DB-first mandate that mirrors the Wiki-First Mandate. D1 is SQLite, so one export serves both.

### When to Use Each Project Ontology Command

The Project Ontology skill is the wiki's _vocabulary layer_. `init` mines what the vault already declares and uses — page types, template `key: # a|b|c` comments, SCHEMA.md value lists, observed values, scope folders, tags, frontmatter link fields — into one declaration, `wiki/_schema/ontology.yaml`, of **dot-notated terms** (`gap.severity.critical`, `client.acme-corp`, `tag.budget-management`, `rel.related-feature`) with a **proposed → approved → deprecated** lifecycle, rendered to `wiki/_schema/ONTOLOGY.md`. **Pages keep plain values** (`severity: critical`); page ids are **derived from paths** (`client.acme.gap.co-op-billing`), never written into pages. Declared values are approved, observed-only values are proposed, spelling variants become proposed aliases — nothing is silently approved — and an interview settles vocabulary conflicts. **One engine** (`.claude/ontology/ontology.py`, stdlib, never PyYAML) enforces it in every place a value can enter or be read: a **PreToolUse hook** reconstructs the post-write file and blocks a Write/Edit that *adds* a strict violation (unregistered, misspelled or deprecated value; broken, ambiguous or noncanonical `[[link]]`; relation target of the wrong type), naming the approved values and the exact propose command — violations already on a page never block (**ratchet**), so a messy vault adopts enforcement on day one; a **PostToolUse hook** reports what still stands; a **Bash guard** turns `approve`/`deprecate`/`init --write` into a permission prompt and blocks shell writes into pages; a guard on `ontology.yaml` rejects agent edits that approve, deprecate, remove, re-spell or loosen anything (**humans own approval**); a **SessionStart banner** keeps counts and rules in context; CI runs `check --changed-since <base>`; **project-db** loads `ontology_terms`, `ontology_aliases`, `ontology_fields`, `ontology_violations` and `pages.ontology_id` at every sync (optional `fail` gate, alias-aware search); **wiki-lint** reports it as Check 8. `apply` rewrites only what has one right answer (aliases, spelling variants, deprecated values with a replacement, uniquely-resolvable links) — every other byte preserved.

### When to Use the Repo Audit Command

The Repo Audit command runs a **read-only**, principal-engineer review in four phases — Discovery & Mapping → evidence-based Audit (every finding severity-rated and `file:line`-cited) → Improvement Strategy → milestone Task Plan — and emits a single graded report (A–F) with a strengths section, flagged quick wins, and open questions. It calibrates rigor to project maturity (`--depth`), prioritizes the core 20% of code that does 80% of the work, and **never modifies anything except the report it writes** (via `--out` or after you accept the save offer). Pair it with `/disclosure:audit` (context-layer health) and the `ux-audit` skill (interface quality) for full-stack coverage.

### When to Use the UI-Issue-to-Plan Command

The UI-Issue-to-Plan command takes an `.mp4`/`.mov`/`.webm`/`.gif` screencast in which someone narrates a problem, a desired change, or how a flow **should** work better in the UI of the project **open in this session**, and produces an implementation plan in `./plans/`. It treats the video as a **design starting point, not just a bug report**. It reuses the shared video pipeline (`extract-video-frames` → `dedupe-frames` → `elevenlabs-transcribe`), launches parallel `ui-frame-analyst` agents to read the frames + narration and identify the exact UI components referenced (plus the narrator's vision and observed friction), then — the key differentiator from `video-to-deliverables`/`workflow-analyzer` — **grounds every observed component in the real codebase** via parallel `Explore` agents (`file:line` evidence). Unless `--mode fix`, it synthesizes a **curated set of grounded improvement opportunities**. It then runs an **AskUserQuestion** interview that **frames intent** (fix only vs. improve too), confirms each fix, grounds, prioritizes, and lets you **opt into enhancements** — so it elicits what you actually want the flow to become, not just the reported defect. The plan separates **Defect fixes** from **Enhancements (opt-in)**, each prioritized, with on-screen evidence (frame + quote), affected files, a grouped task checklist, deferred opportunities, open questions, and runnable verification. Calibrated so a terse bug video stays lean; degrades gracefully (no `ELEVENLABS_API_KEY` → frames-only + interview; `--no-ground` → video-only). Wiki-ingested when a vault exists. Stops at a validated plan and offers to start the P0 task rather than editing code unprompted.

### When to Use the Highlight Reel Command

The Highlight Reel command is the **creation** companion to the video-_analysis_ skills: `video-to-deliverables`/`workflow-analyzer`/`ui-issue-to-plan` turn a video into **documents** — this turns a long `.mp4`/`.mov`/`.webm`/`.gif` app-demo screencast into a **new, shorter video**. It reuses the same shared preprocessing pipeline (`extract-video-frames` → `dedupe-frames` → `elevenlabs-transcribe`) and adds the two layers none of the analysis skills have — **TTS narration** (`scripts/tts.py`, the ElevenLabs text-to-speech companion to the transcribe skill's speech-to-text) and **ffmpeg reel assembly** (`scripts/assemble_reel.py`). Parallel frame-analyst agents read the frames + word-timed transcript into a salience-scored **moment catalog** (what happens, when, which feature, how highlight-worthy); parallel `Explore` agents then **ground every demonstrated feature in the real codebase** (`file:line`) so a narration beat may state a _verified_ technical fact ("all four panels come from one query") rather than guess from pixels — narration that can't be grounded stays descriptive, and a repo-mismatch is flagged loudly (unless `--no-ground`). It drafts a ranked cut, then an **AskUserQuestion** interview confirms which moments make it, their order, the target length, the tone/voice, and how to treat the original audio (`duck`/`keep`/`mute`) and captions — **nothing renders before that gate**. It then writes a grounded narration script + `reel-plan.json` (the single-source-of-truth edit-decision list), synthesizes one voiceover clip per beat (unless `--no-tts` → captions-only, no API key needed), and renders: each moment is cut, the voiceover is mixed over the ducked/kept/muted original, any clip shorter than its narration is **freeze-extended** so nothing is cut off, segments are concatenated, and subtitles are burned in (SRT always written as a sidecar). Because `reel-plan.json` drives the render, edits — reword a beat, retime, reorder — are a quick re-run with no re-analysis. Degrades gracefully (no audio → frames-only analysis + interview; no `ELEVENLABS_API_KEY` → captions-only). Wiki-ingested when a vault exists.

### When to Use the Plan-Review Command

The Plan-Review command takes a **local** plan, spec, design doc, or issue/bug-report markdown and reviews it as a skeptical principal engineer would before any code is written. It is the read-only **document** reviewer that complements the others: `repo-audit` audits the codebase, `ux-audit` audits a UI, and `funcspec`/`ui-issue-to-plan` _produce_ plans — `plan-review` is the only one that **audits a written plan or issue against the code**. It decomposes the artifact into tasks, **claims about the codebase**, assumptions, and acceptance criteria; **grounds** every referenced (and _implied_) component in this repo's real source via parallel `Explore` agents (`file:line`) — verifying each checkable claim and surfacing what the plan likely _missed_ (other callers of a changed API, a second implementation, an implied-but-absent migration or error state); then reviews across five lenses (**completeness, feasibility, risk, clarity, scope**), separating **gaps** (missing & needed) from **improvements** (better-with) from **errors** (code contradicts the plan), each severity-rated with an artifact quote _and_ a `file:line`. On `--depth deep` it adversarially refutes each finding before it survives. An **AskUserQuestion** interview then validates which gaps are real and in-scope and sets priority — so the report reflects your intent, not raw model suspicion. It writes a **read-only** review to `./reviews/` with a readiness verdict (🟢/🟡/🔴), a strengths section, severity-grouped findings, a color-coded gap & ambiguity register, open questions, and a "definition of ready" checklist — **never modifying the original**. It then _offers_ (doesn't assume) to apply the P0 fixes into a revised copy. Calibrated so a tight plan gets a short 🟢 review; degrades gracefully (`--no-ground` → document-only, feasibility findings flagged unconfirmed). Wiki-ingested when a vault exists.

### When to Use the Data-UI Craft Command

The Data-UI Craft command operates on data-display surfaces across **three pillars** distilled from a dashboard-design teaching: **(1) data drives the form** (let each field's _type_ choose its representation — categorical → chips, numeric → right-aligned tabular figures with consistent precision/units, long text → truncate **with a reveal**, inactive records → shaded rows, time-sequenced data → a timeline/chart rather than a time-sorted table); **(2) the right things are hidden until needed** — the **spectrum of explicitness** places every control by _frequency × importance_ (always-visible → popover/menu → revealed on hover/swipe) and **progressive disclosure** sequences onboarding into a checklist/contextual tips instead of one feature-dump modal; **(3) invisible UI makes it all function** — tooltips on icon-only controls, click-to-copy chips, comment/annotation indicators, and the complete set of empty/loading/error/hover/focus states, implemented in-place (popover/drawer/inline) rather than as new pages. It is **stack-aware** (detects framework, styling primitive, data-grid library, and existing utilities so fixes match and nothing is duplicated) with **React + Tailwind** worked examples. In `audit` it writes a severity-rated report in **both** markdown and HTML (`./data-ui-craft-audit.{md,html}`), every finding carrying a rule ID (`DF*`/`PD*`/`IU*`), a `file:line`, user-impact phrasing, and a fix pointer. In `audit-and-implement` (default) an **AskUserQuestion** interview frames intent and confirms which findings are real and in-scope before any edit; it then applies in-place fixes (preferring column-def changes when a data layer exists) and offers a reusable **React/Tailwind primitives kit** (`src/components/data-ui/`: NumericCell, Chip, StatusChip, TruncatedText, DataRow, Popover, HoverActions, OnboardingChecklist, Tooltip, CopyChip, CommentIndicator, TableStates). The destructive step is always gated behind your explicit choice. It complements `ux-audit` (Nielsen/Norman heuristics) — this is the data-display craft layer — and pairs with `ui-issue-to-plan` (when the audit is driven by a screen recording). Wiki-logged when a vault exists.

### When to Use the XState Refactor Command

The XState Refactor command takes a pointer at a slice of the app (file, directory, component name, or a description like "the checkout flow") whose state logic has outgrown its implementation — boolean-flag soup, `useEffect` orchestration, impossible-but-representable states — and migrates it onto **XState v5**. Its premise: the statechart already exists _implicitly_, so Phase 1 is archaeology, not invention — parallel `Explore` agents inventory every state variable and flag combination, every event/effect, and **every UI dependency** (conditional renders, disabled props, consumers outside the target) into a `file:line`-cited behavior map, honestly enumerating the impossible states the types allow. Phase 2 designs the statechart (flat machine vs hierarchical/parallel statechart vs actor system per a decision guide — including the credibility-preserving "don't use XState, use a reducer" recommendation for trivial targets), with a mermaid diagram, an impossible-states-eliminated table, and a draft **state↔UI coverage matrix** where every machine state must end up with a _decided_ visual answer (mapped UI, user-approved "intentionally invisible", or an explicit deferred gap). An **AskUserQuestion** interview validates every inferred state, behavioral divergence ("the code allows loading+error simultaneously — bug or intended?"), and UI-gap resolution, plus the deprecation appetite (delete / deprecate-then-delete / flag). The validated, self-contained migration plan goes to `./plans/`; **no application code is edited before the explicit approval gate**. On approval it implements in behavior-preserving order — XState v5 installed if missing, machine written in isolation with `setup()`, **deterministic tests green before UI wiring** (model-based path coverage via `createTestModel` from `xstate/graph` + guard-boundary unit tests + per-state UI coverage tests mirroring the matrix), UI swapped onto `useMachine`/`useSelector`/`state.matches`/`state.can` one touchpoint at a time — then retires the old state code behind a **grep-verified deprecation checklist** and runs the project's own typecheck/lint/tests. Complements the others: `ui-issue-to-plan` starts from a video, `plan-review` audits a document, `data-ui-craft` fixes display craft — this one restructures state **logic**. Wiki-ingested when a vault exists.

### When to Use the Orchestrate Command

The Orchestrate command turns the session model into a **hands-off
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

## Agents

| Agent | Description |
|-------|-------------|
| `ai-transparency` | Read-only scanner that reports AI transparency violations with file:line references |
| `video-to-deliverables` | Video analysis subagent for producing configurable deliverables |
| `wiki-pipeline` | Orchestrator for complex multi-step wiki operations: Full Meeting Ingest, Bulk Bootstrap, and Weekly Maintenance workflows |

## Hooks

The plugin includes a **PostToolUse** hook that automatically checks files after edits for AI transparency violations. When you edit a file that contains AI/LLM SDK calls, the hook warns about missing:

- Progress/activity logging
- Status tracking fields
- UI status subscriptions
- Error handling states

The hook is framework-agnostic and detects Anthropic, OpenAI, Vercel AI SDK, LangChain, Cohere, and Google AI patterns.

## Prerequisites

Some skills require external tools:

- **FFmpeg**: Required for `extract-video-frames` (frame extraction and audio splitting)
- **Python 3.10+**: Required for `dedupe-frames` (with `imagehash` and `Pillow` packages)
- **uv**: Required for `elevenlabs-transcribe` (auto-installs dependencies via PEP 723)
- **ElevenLabs API key**: Set `ELEVENLABS_API_KEY` environment variable for transcription

## License

MIT
