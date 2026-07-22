# Bespoke Agentics — Wiki Plugin Instructions

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

| Situation | Command |
|-----------|---------|
| Starting a brand-new wiki vault | `/wiki:init` |
| Adding a new client/project workspace | `/wiki:new-client '<name>' '<platform>'` |
| After analyzing a meeting or recording | `/wiki:ingest-meeting '<name>' '<meeting-dir>' '<label>'` |
| Received an email, spec, RFP, or other document | `/wiki:ingest-document '<name>' '<path>' '<type>'` |
| Someone asks a question about the project | `/wiki:query '<question>' --client <slug>` |
| Weekly maintenance or health check | `/wiki:lint --scope full` |
| Checking wiki statistics | `/wiki:status` |
| Syncing with Confluence | Use the `wiki-confluence-reconcile` skill |

### When to Use Each Glean Command

| Situation | Command |
|-----------|---------|
| Bootstrap a new Glean Agent Toolkit project (Python) | `/glean:init` |
| Add a custom `@tool_spec` tool to an existing project | `/glean:add-tool '<name>' --description '<text>' --params '<n:t,...>'` |
| Wire an additional framework adapter (OpenAI / LangChain / ADK) | `/glean:add-adapter --framework <name>` |
| Diagnose a broken Glean agent setup | `/glean:doctor` (add `--probe` for a live API ping) |

### When to Use Each Bun Workspace Command

| Situation | Command |
|-----------|---------|
| Inspect a directory of sibling projects, see what a monorepo migration would look like | `/bun:analyze [<dir>]` |
| Execute the migration into a Bun workspace (interactive, reversible) | `/bun:convert [<dir>] [--layout flat\|buckets] [--scope @org]` |
| Health-check an existing Bun workspace for drift, nested lockfiles, missing tsconfig extension | `/bun:audit [<dir>] [--fix]` |
| Scaffold a new package into an existing Bun workspace | `/bun:add <package-path> [--name <name>] [--kind library\|app]` |

The Bun Workspace skill manages the *workspace/dependency* layer; pair it with `/submodule:*` when you also want to pin children at the git layer.

### When to Use Each Progressive Disclosure Command

| Situation | Command |
|-----------|---------|
| Set up a layered CLAUDE.md/AGENTS.md context layer across a project or monorepo | `/disclosure:map [<root>] [--depth subsystem\|diverge\|deep] [--no-wiki]` |
| Read-only health check of an existing context layer (coverage, drift, broken pointers, settings gaps) | `/disclosure:audit [<root>]` |
| Keep memory files current — update only managed sections, add files for new subsystems | `/disclosure:refresh [<root>]` |

The Progressive Disclosure skill builds the *context/memory* layer (per-directory CLAUDE.md is the source of truth; AGENTS.md points to it) plus the supporting `.claude/` config (Read deny rules, `additionalDirectories`, `claudeMdExcludes`, a SessionStart hook, code-intelligence recommendations). It deploys parallel subagents to profile every subsystem and, if a wiki is present, mines it for context and logs the operation. It is complementary to `architect-agents`, which builds the *agent/command* layer — the two do not overlap.

### When to Use Each Funcspec Command

| Situation | Command |
|-----------|---------|
| Evaluate a Storybook's pages page-by-page and infer the functionality the UI implies | `/bespokeagentics:funcspec-evaluate [<workspace>] [--pages a,b] [--visual auto\|on\|off]` |
| Validate findings with the user and generate the implementation plan (spec, plan, backlog, gap register, traceability) | `/bespokeagentics:funcspec-plan [--push ask\|none]` |
| Check the state of a funcspec run (profiles, ambiguities, deliverables) | `/bespokeagentics:funcspec-status [<workspace>]` |

The Funcspec skill is the companion to `claude-design-to-app-workflow` (`design-zip-to-library`): that skill recovers the *visual* layer; `funcspec` extracts the *functional* layer. It launches parallel `page-evaluator` agents (code-first, with optional visual verification against running Storybook), brackets the analysis with two AskUserQuestion interviews (Stage-1 frames intent, Stage-2 validates every inference), and emits deliverables using the Decision Status Colors below. Works on any Storybook workspace; uses a `design-zip-to-library` `analysis.json` as a fast path when present. Deliverables are wiki-ingested when a vault exists.

### When to Use Each Knowledge Loop Command

| Situation | Command |
|-----------|---------|
| Stand up the learning loop (scaffold store, install CLAUDE.md mandate + SessionStart hook) | `/knowledge:init [--path <dir>] [--domains <a,b,c>]` |
| Before starting a task — load the rules that apply by default + the hypotheses today's work can test | `/knowledge:review [<task>] [--domain <slug>]` |
| After a task — capture insights; auto-promote at 3+ confirmations, auto-demote contradicted rules | `/knowledge:extract [<what you learned>] [--domain <slug>]` |
| Bridge confirmed rules into proper wiki pages (or manually promote/demote) | `/knowledge:promote [--domain <slug>] [--rule <id>] [--demote <id>]` |
| Health-check the store (promotion candidates, stale entries, integrity, broken links) | `/knowledge:audit [--domain <slug>] [--stale-days <n>] [--fix]` |

The Knowledge Loop skill is the project's *learning layer*: a lightweight facts → hypotheses → rules store (one trio per domain) that compounds across tasks. It is **wiki-first compatible by design** — the store lives inside the vault at `wiki/knowledge/` (so `/wiki:query`, `/wiki:lint`, and `/wiki:status` see it), and confirmed rules are **promoted into proper wiki pages**, satisfying the mandate that validated knowledge become wiki content. Evidence is strict: every confirmation/contradiction must cite a distinct, dated, linkable source, so `rules.md` stays trustworthy enough to **apply by default**. `init` writes the before/after-task mandate into `CLAUDE.md` and installs a SessionStart hook that surfaces the active rules, so the loop fires without being invoked. Promotion bar: `confirmations ≥ 3` (distinct) and `contradictions = 0`; a single contradiction demotes a rule back to a hypothesis.

### When to Use the Repo Audit Command

| Situation | Command |
|-----------|---------|
| Get an honest, evidence-based health check of a repository with a prioritized fix plan | `/bespokeagentics:repo-audit [<path>] [--depth quick\|standard\|deep] [--out <file>]` |

The Repo Audit command runs a **read-only**, principal-engineer review in four phases — Discovery & Mapping → evidence-based Audit (every finding severity-rated and `file:line`-cited) → Improvement Strategy → milestone Task Plan — and emits a single graded report (A–F) with a strengths section, flagged quick wins, and open questions. It calibrates rigor to project maturity (`--depth`), prioritizes the core 20% of code that does 80% of the work, and **never modifies anything except the report it writes** (via `--out` or after you accept the save offer). Pair it with `/disclosure:audit` (context-layer health) and the `ux-audit` skill (interface quality) for full-stack coverage.

### When to Use the UI-Issue-to-Plan Command

| Situation | Command |
|-----------|---------|
| Turn a narrated screen recording into a code-grounded plan that captures both what to fix AND how to improve the UX | `/bespokeagentics:ui-issue-to-plan '<video>' [issue-label] [interval] [--mode fix\|improve\|both] [--out <dir>] [--no-ground]` |

The UI-Issue-to-Plan command takes an `.mp4`/`.mov`/`.webm`/`.gif` screencast in which someone narrates a problem, a desired change, or how a flow **should** work better in the UI of the project **open in this session**, and produces an implementation plan in `./plans/`. It treats the video as a **design starting point, not just a bug report**. It reuses the shared video pipeline (`extract-video-frames` → `dedupe-frames` → `elevenlabs-transcribe`), launches parallel `ui-frame-analyst` agents to read the frames + narration and identify the exact UI components referenced (plus the narrator's vision and observed friction), then — the key differentiator from `video-to-deliverables`/`workflow-analyzer` — **grounds every observed component in the real codebase** via parallel `Explore` agents (`file:line` evidence). Unless `--mode fix`, it synthesizes a **curated set of grounded improvement opportunities**. It then runs an **AskUserQuestion** interview that **frames intent** (fix only vs. improve too), confirms each fix, grounds, prioritizes, and lets you **opt into enhancements** — so it elicits what you actually want the flow to become, not just the reported defect. The plan separates **Defect fixes** from **Enhancements (opt-in)**, each prioritized, with on-screen evidence (frame + quote), affected files, a grouped task checklist, deferred opportunities, open questions, and runnable verification. Calibrated so a terse bug video stays lean; degrades gracefully (no `ELEVENLABS_API_KEY` → frames-only + interview; `--no-ground` → video-only). Wiki-ingested when a vault exists. Stops at a validated plan and offers to start the P0 task rather than editing code unprompted.

### When to Use the Highlight Reel Command

| Situation | Command |
|-----------|---------|
| Turn a long app-demo screencast into a short, narrated, subtitled highlight video — grounded in this repo so the voiceover is technically accurate | `/bespokeagentics:highlight-reel '<video>' [reel-label] [interval] [--duration <sec>] [--voice <id>] [--audio duck\|keep\|mute] [--no-subs] [--no-ground] [--no-tts] [--out <dir>]` |

The Highlight Reel command is the **creation** companion to the video-*analysis* skills: `video-to-deliverables`/`workflow-analyzer`/`ui-issue-to-plan` turn a video into **documents** — this turns a long `.mp4`/`.mov`/`.webm`/`.gif` app-demo screencast into a **new, shorter video**. It reuses the same shared preprocessing pipeline (`extract-video-frames` → `dedupe-frames` → `elevenlabs-transcribe`) and adds the two layers none of the analysis skills have — **TTS narration** (`scripts/tts.py`, the ElevenLabs text-to-speech companion to the transcribe skill's speech-to-text) and **ffmpeg reel assembly** (`scripts/assemble_reel.py`). Parallel frame-analyst agents read the frames + word-timed transcript into a salience-scored **moment catalog** (what happens, when, which feature, how highlight-worthy); parallel `Explore` agents then **ground every demonstrated feature in the real codebase** (`file:line`) so a narration beat may state a *verified* technical fact ("all four panels come from one query") rather than guess from pixels — narration that can't be grounded stays descriptive, and a repo-mismatch is flagged loudly (unless `--no-ground`). It drafts a ranked cut, then an **AskUserQuestion** interview confirms which moments make it, their order, the target length, the tone/voice, and how to treat the original audio (`duck`/`keep`/`mute`) and captions — **nothing renders before that gate**. It then writes a grounded narration script + `reel-plan.json` (the single-source-of-truth edit-decision list), synthesizes one voiceover clip per beat (unless `--no-tts` → captions-only, no API key needed), and renders: each moment is cut, the voiceover is mixed over the ducked/kept/muted original, any clip shorter than its narration is **freeze-extended** so nothing is cut off, segments are concatenated, and subtitles are burned in (SRT always written as a sidecar). Because `reel-plan.json` drives the render, edits — reword a beat, retime, reorder — are a quick re-run with no re-analysis. Degrades gracefully (no audio → frames-only analysis + interview; no `ELEVENLABS_API_KEY` → captions-only). Wiki-ingested when a vault exists.

### When to Use the Plan-Review Command

| Situation | Command |
|-----------|---------|
| Pressure-test a written implementation plan, spec, or issue/bug report **before** building it — find the gaps, ambiguities, and risks, grounded in the real code | `/bespokeagentics:plan-review '<artifact>' [--type plan\|issue\|spec\|auto] [--depth quick\|standard\|deep] [--out <dir>] [--no-ground]` |

The Plan-Review command takes a **local** plan, spec, design doc, or issue/bug-report markdown and reviews it as a skeptical principal engineer would before any code is written. It is the read-only **document** reviewer that complements the others: `repo-audit` audits the codebase, `ux-audit` audits a UI, and `funcspec`/`ui-issue-to-plan` *produce* plans — `plan-review` is the only one that **audits a written plan or issue against the code**. It decomposes the artifact into tasks, **claims about the codebase**, assumptions, and acceptance criteria; **grounds** every referenced (and *implied*) component in this repo's real source via parallel `Explore` agents (`file:line`) — verifying each checkable claim and surfacing what the plan likely *missed* (other callers of a changed API, a second implementation, an implied-but-absent migration or error state); then reviews across five lenses (**completeness, feasibility, risk, clarity, scope**), separating **gaps** (missing & needed) from **improvements** (better-with) from **errors** (code contradicts the plan), each severity-rated with an artifact quote *and* a `file:line`. On `--depth deep` it adversarially refutes each finding before it survives. An **AskUserQuestion** interview then validates which gaps are real and in-scope and sets priority — so the report reflects your intent, not raw model suspicion. It writes a **read-only** review to `./reviews/` with a readiness verdict (🟢/🟡/🔴), a strengths section, severity-grouped findings, a color-coded gap & ambiguity register, open questions, and a "definition of ready" checklist — **never modifying the original**. It then *offers* (doesn't assume) to apply the P0 fixes into a revised copy. Calibrated so a tight plan gets a short 🟢 review; degrades gracefully (`--no-ground` → document-only, feasibility findings flagged unconfirmed). Wiki-ingested when a vault exists.

### When to Use the Data-UI Craft Command

| Situation | Command |
|-----------|---------|
| Audit and/or implement the craft details that make a data-dense UI (dashboard, table, admin panel, data grid, list/detail view) actually work | `/bespokeagentics:data-ui-craft [mode: audit\|implement\|audit-and-implement] [path]` |

The Data-UI Craft command operates on data-display surfaces across **three pillars** distilled from a dashboard-design teaching: **(1) data drives the form** (let each field's *type* choose its representation — categorical → chips, numeric → right-aligned tabular figures with consistent precision/units, long text → truncate **with a reveal**, inactive records → shaded rows, time-sequenced data → a timeline/chart rather than a time-sorted table); **(2) the right things are hidden until needed** — the **spectrum of explicitness** places every control by *frequency × importance* (always-visible → popover/menu → revealed on hover/swipe) and **progressive disclosure** sequences onboarding into a checklist/contextual tips instead of one feature-dump modal; **(3) invisible UI makes it all function** — tooltips on icon-only controls, click-to-copy chips, comment/annotation indicators, and the complete set of empty/loading/error/hover/focus states, implemented in-place (popover/drawer/inline) rather than as new pages. It is **stack-aware** (detects framework, styling primitive, data-grid library, and existing utilities so fixes match and nothing is duplicated) with **React + Tailwind** worked examples. In `audit` it writes a severity-rated report in **both** markdown and HTML (`./data-ui-craft-audit.{md,html}`), every finding carrying a rule ID (`DF*`/`PD*`/`IU*`), a `file:line`, user-impact phrasing, and a fix pointer. In `audit-and-implement` (default) an **AskUserQuestion** interview frames intent and confirms which findings are real and in-scope before any edit; it then applies in-place fixes (preferring column-def changes when a data layer exists) and offers a reusable **React/Tailwind primitives kit** (`src/components/data-ui/`: NumericCell, Chip, StatusChip, TruncatedText, DataRow, Popover, HoverActions, OnboardingChecklist, Tooltip, CopyChip, CommentIndicator, TableStates). The destructive step is always gated behind your explicit choice. It complements `ux-audit` (Nielsen/Norman heuristics) — this is the data-display craft layer — and pairs with `ui-issue-to-plan` (when the audit is driven by a screen recording). Wiki-logged when a vault exists.

### When to Use the XState Refactor Command

| Situation | Command |
|-----------|---------|
| Refactor a feature's ad-hoc state logic + UI into an explicit XState v5 machine, statechart, or actor system — with a validated plan, full state↔UI coverage, deterministic tests, and deprecation of the old code | `/bespokeagentics:xstate-refactor '<target>' [--mode plan\|implement\|full] [--style machine\|statechart\|actors\|auto] [--out <dir>] [--no-tests] [--force]` |

The XState Refactor command takes a pointer at a slice of the app (file, directory, component name, or a description like "the checkout flow") whose state logic has outgrown its implementation — boolean-flag soup, `useEffect` orchestration, impossible-but-representable states — and migrates it onto **XState v5**. Its premise: the statechart already exists *implicitly*, so Phase 1 is archaeology, not invention — parallel `Explore` agents inventory every state variable and flag combination, every event/effect, and **every UI dependency** (conditional renders, disabled props, consumers outside the target) into a `file:line`-cited behavior map, honestly enumerating the impossible states the types allow. Phase 2 designs the statechart (flat machine vs hierarchical/parallel statechart vs actor system per a decision guide — including the credibility-preserving "don't use XState, use a reducer" recommendation for trivial targets), with a mermaid diagram, an impossible-states-eliminated table, and a draft **state↔UI coverage matrix** where every machine state must end up with a *decided* visual answer (mapped UI, user-approved "intentionally invisible", or an explicit deferred gap). An **AskUserQuestion** interview validates every inferred state, behavioral divergence ("the code allows loading+error simultaneously — bug or intended?"), and UI-gap resolution, plus the deprecation appetite (delete / deprecate-then-delete / flag). The validated, self-contained migration plan goes to `./plans/`; **no application code is edited before the explicit approval gate**. On approval it implements in behavior-preserving order — XState v5 installed if missing, machine written in isolation with `setup()`, **deterministic tests green before UI wiring** (model-based path coverage via `createTestModel` from `xstate/graph` + guard-boundary unit tests + per-state UI coverage tests mirroring the matrix), UI swapped onto `useMachine`/`useSelector`/`state.matches`/`state.can` one touchpoint at a time — then retires the old state code behind a **grep-verified deprecation checklist** and runs the project's own typecheck/lint/tests. Complements the others: `ui-issue-to-plan` starts from a video, `plan-review` audits a document, `data-ui-craft` fixes display craft — this one restructures state **logic**. Wiki-ingested when a vault exists.

### When to Use the Orchestrate Command

| Situation | Command |
|-----------|---------|
| Execute an implementation plan (or a raw task) through a managed, gated, multi-agent build — the session model orchestrates, Opus/Sonnet subagents implement and smoke-test | `/bespokeagentics:orchestrate '<plan-path-or-task>' [--depth quick\|standard\|deep] [--dry-run] [--no-confirm] [--no-smoke] [--no-review] [--single-model <m>] [--resume [<slug>]]` |

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

| Situation | Command |
|-----------|---------|
| Turn a plan into a kickoff contract, then build it one workstream at a time — each `code → validate → commit`, with a server-side hard-gate proof and a human checkpoint between workstreams | `/bespokeagentics:workstream-orchestrate '<plan-path-or-task>' [--from WS-n] [--to WS-m] [--engine workflow\|agent] [--attempts N] [--no-commit] [--no-confirm] [--dry-run] [--resume [<slug>]] [--force]` |

The Workstream-Orchestrate command is the **sequential, commit-as-you-go** sibling of `orchestrate`.
Where `orchestrate` runs parallel implementation waves in one Agent-driven loop and never commits,
this one drives a plan **one workstream at a time** through a bounded `code → validate → commit`
**Workflow** (one Workflow invocation per workstream), and it **generates a first-class kickoff
contract** — a 10-section, human-confirmed document (Mission, Reading list, Branch, Orchestration
shape, Gates, Guardrails, Workstreams, Workflow skeleton, Stop-and-ask, Definition of done), derived
from the plan, that every workstream is built and judged against. Each workstream: an implementer
applies only its scope in the shared tree (no worktree); an **independent, read-only, adversarial
validator** re-runs the gates the orchestrator also runs itself and must **prove or refute the plan's
declared "hard gates"** — invariants that must hold at the *authoritative layer* (a server-side
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

| Situation | Command |
|-----------|---------|
| Audit (and optionally fix) an AI API/SDK integration for the event-loop defects that cause silent hangs, stalls, and deadlocks in managed-agent architectures | `/bespokeagentics:agent-loop-audit [mode: audit\|implement\|audit-and-implement] [path]` |

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

| Situation | Command |
|-----------|---------|
| Record a browser flow you describe as a screencast — the agent drives Claude-in-Chrome, records it (default gif, or `--engine screen` for native-resolution monitor capture), makes an MP4, and offers to turn it into a narrated highlight reel | `/bespokeagentics:screencast-capture ['<start-url-or-flow>'] [capture-label] [--engine chrome-gif\|screen] [--display <idx>] [--crf <n>] [--overlays clean\|clicks\|full] [--reel] [--no-reel] [--out <dir>]` |

The Screencast-Capture command is the **capture** companion to `screencast-highlight-reel`: that
skill *polishes* a finished screencast into a narrated reel — this one *produces* the screencast
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

| Situation | Command |
|-----------|---------|
| Settle an undecided UI change by building a live, code-grounded HTML wireframe, interviewing against it, and emitting a spec | `/bespokeagentics:interactive-wireframe '<surface>' [--slug <name>] [--rounds N] [--port N] [--out <dir>] [--spec <path>] [--fresh] [--ttl <days>] [--no-verify] [--no-serve]` |

The Interactive-Wireframe command turns a UI argument into something you can click. Its premise:
**people critique something concrete far better than they answer a hypothetical** — "should the
header stay pinned?" gets a shrug; the same question asked while looking at a real header with the
scroll threshold on a slider gets a decision in ten seconds, and often a different one. Two
properties do the work. **(1) It is grounded in real code** — it detects the stack and lifts design
tokens, typography, the literal enums/labels the surface displays, roles/permission flags, the
existing layout components the change touches, and behavioural constants from actual source, each
cited to a path, into `wireframes/<slug>/grounding.md`; nothing is invented, and a project with no
design system gets values derived from the running app's computed styles, **labelled as derived**.
That is what makes the wireframe *predictive* rather than illustrative — collisions, real label
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

| Situation | Command |
|-----------|---------|
| Confirm the UI that was implemented matches the wireframe a spec settled | `/bespokeagentics:wireframe-parity '<spec-or-slug>' --app <url> [--wireframe <path>] [--depth quick\|standard\|deep] [--out <dir>] [--no-browser] [--force]` |

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
ledger. Distinct from `plan-review` (audits a document *before* build) and `ux-audit` (audits a UI
against heuristics): this audits a **built UI against the wireframe that specified it**. **The
implementation is never modified.**

### When to Use Each Agent-Native Engineering Command

| Situation | Command |
|-----------|---------|
| Run the whole suite: readiness scorecard across all six dimensions, then dispatch the skills in dependency order (resumable) | `/agentnative:suite [mode: assess\|run] [dimensions] [--resume]` |
| CI is slow; agents wait minutes to verify their work — swap in native tooling (TS7, oxlint/oxfmt, uv, ruff) and split fast/slow lanes | `/agentnative:fast-ci [mode: audit\|implement\|audit-and-implement] [path]` |
| Trigger coding agents from issue-triage labels — auto-triage, repro-on-label, PoC-on-label | `/agentnative:issue-to-agent [mode: plan\|implement] [labels]` |
| Put scheduled agents on the chores devs skip — regression backfill, SDK gaps, skill tuning, drift | `/agentnative:chore-crons [mode: plan\|implement] [chores]` |
| Give agents the means to prove their work — screenshots, browser checks, diffs, evidence storage + PR comments | `/agentnative:proof-of-work [mode: plan\|implement] [scope: local\|ci\|both]` |
| Make the app runnable locally, hermetically, N instances at a time | `/agentnative:hermetic-deploy [mode: audit\|implement] [instances]` |
| Give agents production-realistic seed data as deterministic scenarios | `/agentnative:sim-data [mode: plan\|implement] [scenario]` |

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
    │  ├─ wiki-lint/                  # 7-dimension health check
    │  ├─ wiki-query/                 # Natural language search + synthesis
    │  ├─ glean-agent-toolkit/        # Scaffold, extend, and triage Glean agents
    │  ├─ bun-workspace/              # Convert/audit/extend Bun workspace monorepos
    │  ├─ progressive-disclosure/     # Layered CLAUDE.md/AGENTS.md + large-codebase config
    │  ├─ claude-design-to-app-workflow/  # Design zip → component library + Storybook
    │  ├─ funcspec/                   # Storybook pages → validated implementation plan
    │  ├─ knowledge-loop/             # Self-improving facts → hypotheses → rules loop
    │  ├─ ui-issue-to-plan/           # Narrated UI screencast → code-grounded plan (fixes + UX enhancements)
    │  ├─ screencast-highlight-reel/  # Long app-demo screencast → grounded, narrated, subtitled highlight video (TTS + ffmpeg assembly)
    │  ├─ screencast-capture/         # Browser flow → MP4 (gif tab-capture or --engine screen native-res) → hands to screencast-highlight-reel
    │  ├─ interactive-wireframe/      # Undecided UI → code-grounded interactive HTML wireframe → interview → spec
    │  ├─ wireframe-parity/           # Built UI vs the wireframe that specified it → read-only parity report (structural + measured)
    │  ├─ plan-review/                # Plan/spec/issue → read-only, code-grounded gap review
    │  ├─ data-ui-craft/              # Data-dense UI audit + fixes + React/Tailwind primitives kit
    │  ├─ xstate-refactor/            # Feature state logic + UI → XState v5 machine/statechart/actors
    │  ├─ orchestrate/                # Plan/task → gated multi-agent implementation (Fable orchestrates, Opus/Sonnet implement)
    │  ├─ workstream-orchestrate/     # Plan → kickoff contract → sequential per-WS code→validate→commit (Workflow) + hard-gate proofs
    │  ├─ agent-loop-audit/           # AI API/SDK integration → event-loop defect audit + gated fixes (silent hangs, stop_reason, deadlocks)
    │  ├─ fast-ci/                    # CI → native-tool swaps (TS7, oxc, uv) + fast/slow lane split
    │  ├─ issue-to-agent/             # Triage labels → auto-dispatched repro/PoC coding agents
    │  ├─ chore-crons/                # Scheduled agents for the chores devs skip (regression backfill, SDK gaps, drift)
    │  ├─ proof-of-work/              # Agent evidence: screenshots, diffs, traces, storage + PR comments
    │  ├─ hermetic-deploy/            # One-command local instances, N at a time (Compose -p isolation)
    │  └─ sim-data/                   # Production-realistic deterministic seed scenarios
    ├─ commands/                      # Slash commands
    │  ├─ wiki/                       # Wiki commands (namespaced)
    │  │  ├─ init.md                  # /wiki:init
    │  │  ├─ new-client.md            # /wiki:new-client
    │  │  ├─ ingest-meeting.md        # /wiki:ingest-meeting
    │  │  ├─ ingest-document.md       # /wiki:ingest-document
    │  │  ├─ lint.md                  # /wiki:lint
    │  │  ├─ query.md                 # /wiki:query
    │  │  └─ status.md                # /wiki:status
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
    │  ├─ funcspec-evaluate.md        # /bespokeagentics:funcspec-evaluate
    │  ├─ funcspec-plan.md            # /bespokeagentics:funcspec-plan
    │  ├─ funcspec-status.md          # /bespokeagentics:funcspec-status
    │  ├─ repo-audit.md               # /bespokeagentics:repo-audit
    │  ├─ ui-issue-to-plan.md         # /bespokeagentics:ui-issue-to-plan
    │  ├─ highlight-reel.md           # /bespokeagentics:highlight-reel
    │  ├─ screencast-capture.md      # /bespokeagentics:screencast-capture
    │  ├─ interactive-wireframe.md   # /bespokeagentics:interactive-wireframe
    │  ├─ wireframe-parity.md        # /bespokeagentics:wireframe-parity
    │  ├─ plan-review.md              # /bespokeagentics:plan-review
    │  ├─ data-ui-craft.md            # /bespokeagentics:data-ui-craft
    │  ├─ xstate-refactor.md          # /bespokeagentics:xstate-refactor
    │  ├─ orchestrate.md              # /bespokeagentics:orchestrate
    │  ├─ workstream-orchestrate.md   # /bespokeagentics:workstream-orchestrate
    │  ├─ agent-loop-audit.md         # /bespokeagentics:agent-loop-audit
    │  └─ wiki-*.md                   # Flat command aliases
    ├─ agents/
    │  ├─ ui-frame-analyst.md         # UI screencast frame + narration analyst
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
9. **Turn a Storybook into an implementation plan**: Run `/bespokeagentics:funcspec-evaluate <workspace>` to infer the functionality the pages imply (page-by-page, with interviews), then `/bespokeagentics:funcspec-plan` to validate findings and generate the spec, plan, backlog, and gap register.
10. **Make the project learn from every task**: Run `/knowledge:init` to scaffold the facts → hypotheses → rules store (inside `wiki/knowledge/`), install the before/after-task mandate in `CLAUDE.md`, and add a SessionStart hook. Then `/knowledge:review` before a task, `/knowledge:extract` after, `/knowledge:promote` to bridge confirmed rules into the wiki, and `/knowledge:audit` to keep the store honest.
11. **Audit a repository before investing in it**: Run `/bespokeagentics:repo-audit` for a read-only, four-phase principal-engineer review that grades the repo A–F and returns severity-rated, `file:line`-cited findings plus a milestone fix plan with quick wins — without touching a line of code.
12. **Turn a screen recording into a plan (fix + improve)**: Run `/bespokeagentics:ui-issue-to-plan '<video>'` — it reads the frames + narration to identify the UI components being referenced, grounds them in this repo's source (`file:line`), surfaces curated improvement opportunities, runs an interview that frames intent (fix vs improve) and lets you opt into enhancements, and writes a code-grounded plan to `./plans/` with separate Defect-fix and Enhancement sections. Use `--mode fix` for a quick bug-only pass.
13. **Pressure-test a plan or issue before you build it**: Run `/bespokeagentics:plan-review '<artifact>'` — it decomposes a local plan/spec/issue into tasks, claims, assumptions, and acceptance criteria, grounds every referenced (and implied) component in this repo's real source (`file:line`) to surface the gaps the document hides, reviews it across completeness/feasibility/risk/clarity/scope, validates and prioritizes the findings via an interview, and writes a **read-only** review + color-coded gap register to `./reviews/` (the original is never modified). Use `--depth deep` for adversarially-verified findings on a high-stakes plan, or `--no-ground` for a document-only pass.
14. **Make a data-dense UI actually work**: Run `/bespokeagentics:data-ui-craft` — it audits a dashboard, table, admin panel, or data grid against the three pillars (data drives the form · the right things hidden until needed · invisible UI), writes a severity-rated report in markdown + HTML with `DF*`/`PD*`/`IU*` findings cited to `file:line`, then — after an interview confirms what's in scope — applies the fixes in place and scaffolds a reusable React/Tailwind primitives kit. Use `audit` for a read-only pass.
15. **Make a feature's state logic explicit**: Run `/bespokeagentics:xstate-refactor '<target>'` — it recovers the statechart the code already implements implicitly (parallel agents map every state variable, flag combination, event, effect, and UI dependency to `file:line`), designs the XState v5 machine/statechart/actor model with a mermaid diagram and a state↔UI coverage matrix, validates every inference via an interview, writes an executable migration plan to `./plans/`, then — only on approval — implements the machine, generates deterministic path-coverage + UI state-coverage tests, wires the UI so every state has a decided visual answer, installs XState if missing, and retires the old state code behind a grep-verified checklist. Use `--mode plan` to stop at the plan.
16. **Execute a plan through a managed multi-agent build**: Run `/bespokeagentics:orchestrate '<plan.md>'` — the session model acts as orchestrator (it never writes production code): read-only agents re-ground every `file:line` anchor, a confirmed work order assigns each work item to Opus (contract-shaped/high-risk) or Sonnet (mechanical/smoke) with exact file ownership, waves run with orchestrator-executed gates between them, a smoke agent drives the running app with evidence-backed pass/fail, and a read-only Opus reviewer pressure-tests the diff before a faithful final report. Pass a raw task instead of a plan and it drafts + confirms one first; interrupted runs continue with `--resume`.
17. **Stop your AI integration from silently hanging**: Run `/bespokeagentics:agent-loop-audit` — it detects your stack (TS/JS, Python; Anthropic pack when the SDK is present), discovers every place the code dispatches a task and consumes (or fails to consume) the event stream, audits each surface against the `EL*`/`SR*`/`RS*`/`OB*` catalog (listener-before-payload sequencing, `stop_reason` branching on idle, unanswered tool approvals, error differentiation, reconnect/resume, interrupt+redirect steering), and writes a severity-rated `file:line`-cited report with a loop-health matrix — then, after an interview confirms scope, applies the accepted fixes in place. Use `audit` for a read-only pass.
18. **Make CI fast enough for agents**: Run `/agentnative:fast-ci` — it measures the current `git push`→green wall-clock, audits the toolchain against the `TC*` native-rewrite catalog (TypeScript 7 native tsc, oxlint/oxfmt, uv, ruff, Biome, bun test) and the `LN*` lane rules, then — after an interview confirms each swap and the post-merge failure policy — migrates tools with official migrators, splits the pipeline into a <3-minute fast lane (`pull_request` + `merge_group`) with integration tests in the merge queue or post-merge, and proves the win with before/after timings.
19. **Dispatch agents from triage labels**: Run `/agentnative:issue-to-agent` — it designs a minimal label taxonomy, then generates claude-code-action v1 workflows: auto-triage on issue open, `agent:repro` → failing test on a `claude/` branch + repro-steps comment, `agent:poc` → spike branch + design notes — least-privilege, injection-aware, zizmor-verified, mandate ending at the handoff so the engineer picks up prepared ground, never an unsupervised fix.
20. **Automate the chores devs skip**: Run `/agentnative:chore-crons` — it inventories the neglected tail with git/grep evidence (untested critical paths, SDK coverage gaps, doc examples that no longer compile), scores value × automatability, and generates scheduled runners (Actions cron, Claude Code Routines, or Cowork tasks) where only self-verifiable chores get crons, each with a single rolling tracking channel, turn budgets, and a double-fire idempotency test.
21. **Let agents prove their work**: Run `/agentnative:proof-of-work` — it installs agent-browser (or wires incumbent Playwright), establishes the `evidence/` manifest convention and `scripts/evidence.sh` verify loop, sets up storage (S3/R2 presigned URLs for inline PR images, artifacts v4 for traces) and a create-or-update PR evidence comment — then proves the whole chain once on a throwaway PR, including a determinism check.
22. **Give every agent its own running app**: Run `/agentnative:hermetic-deploy` — it audits against the `H*` hermeticity catalog (fixed host ports, host-shared state, missing healthchecks, unseeded DBs), then builds Compose `-p` namespacing, ephemeral ports, in-stack mocks for externals, and the `scripts/dev-stack.sh` contract (`up <id>` → healthy seeded URL) — verified by actually running N instances side by side with isolation, teardown, and cold-start measured.
23. **Make the whole repo agent-native in one pass**: Run `/agentnative:suite` — it scores all six dimensions 🟢/🟡/🔴 with evidence into `./plans/agentnative-suite.md`, interviews once for dimension selection, per-dimension mode, and budget, then dispatches the skills in dependency order (fast-ci → hermetic-deploy → sim-data → proof-of-work → issue-to-agent → chore-crons), resumable via `--resume`. Use `assess` for the scorecard only.
24. **Seed data that looks like production**: Run `/agentnative:sim-data` — it mines prod shapes via read-only aggregates (skew, null rates, charset reality, the whale account — values never leave unmasked), then builds deterministic scenarios (`default`/`demo`/`edge`/`load`) via copycat + seeded faker or a Greenmask/anon pipeline with a named-human masking review gate, wired into hermetic-deploy's seed hook and proven by double-seed byte-identical diffs.
25. **Turn a long demo recording into a highlight video**: Run `/bespokeagentics:highlight-reel '<video>'` — the creation companion to the analysis skills. It preprocesses the screencast (frames + word-timed transcript), builds a salience-scored moment catalog, grounds every demonstrated feature in this repo's source (`file:line`) so the voiceover states verified facts, proposes a ranked cut, and runs an interview to confirm the moments/order/length/voice/audio before rendering. It then writes a grounded narration + `reel-plan.json`, synthesizes a voiceover via ElevenLabs TTS (`scripts/tts.py`; omit with `--no-tts` for captions only), and renders a subtitled highlight `.mp4` with ffmpeg (`scripts/assemble_reel.py` — cut, mix, freeze-extend, concat, burn). Edits are a quick re-run off `reel-plan.json`.
26. **Build a plan workstream-by-workstream, committing each**: Run `/bespokeagentics:workstream-orchestrate '<plan-path-or-task>'` — the sequential, commit-as-you-go sibling of `orchestrate`. It generates a human-confirmed **kickoff contract** from the plan (10 sections: mission, gates, guardrails, workstreams, hard gates, definition of done), then drives it **one workstream at a time** through a bounded `code → validate → commit` **Workflow**: an implementer applies only that workstream's scope, an independent adversarial validator re-runs the gates and **proves or refutes the plan's server-side hard gates** (crafted input against the authoritative layer, never client-side hiding), and only a green, validated workstream earns **one Conventional Commit** — followed by a human checkpoint before the next. Failing validation loops back (≤`--attempts`) then halts and surfaces the findings. The driver never writes production code; given a raw task it drafts and confirms a plan first. Resumable under `.workstream/<slug>/`; degrades to `--engine agent` when the Workflow tool is absent, or `--dry-run` for the contract only.
27. **Record a browser demo, then make a reel**: Run `/bespokeagentics:screencast-capture '<start-url-or-flow>'` — the **capture** companion to `screencast-highlight-reel`: it *produces* the screencast that skill polishes, so you never have to screen-record yourself. It drives a live **Claude-in-Chrome** session — an AskUserQuestion interview turns your request into a shot list, it opens a fresh tab and **pauses for you to log in before recording** (credentials stay out of the footage; the agent never types secrets), records the flow step-by-step with the `gif_creator` tool (click indicators only by default), and exports the GIF. For higher fidelity, **`--engine screen`** instead records a chosen monitor with ffmpeg at **native resolution + configurable bitrate** (`--display` / `--crf`) — the fix when the default tab capture (hard-capped ~1200px, dithered GIF) looks grainy; it needs macOS Screen-Recording permission and records the whole monitor (auto-cropped to the browser window). The gif engine then **converts the GIF to a real-duration MP4** (`scripts/gif_to_mp4.sh`; the screen engine writes MP4 directly) — a GIF reports no container duration, so the reel would otherwise drift on frame-index timings — presents the MP4, and (by default) asks whether to hand off to `/bespokeagentics:highlight-reel` (`--reel`/`--no-reel` to force/skip), forwarding `--no-tts` (no ElevenLabs key) and `--no-ground` (site isn't this repo's app) as needed. Degrades gracefully (no ffmpeg → stops before recording; unclearable login → captures what's reachable or stops).
28. **Settle an undecided UI before building it**: Run `/bespokeagentics:interactive-wireframe '<surface>'` — it grounds the surface in this repo's real source (design tokens, typography, the literal enums/labels the UI displays, roles and permission flags, the layout components the change touches — each cited to a path, never invented), emits **one self-contained HTML wireframe** (inline CSS + JS, no build step) carrying a **control overlay generated from the axes that surface actually varies on** — role switcher, entity states, permission toggles, data extremes, behavioural thresholds, layout variants, zone guides, live state readout, with state mirrored into the URL so any configuration is a shareable link — serves it on **8791** (8787 is never auto-probed; `file://` fails under browser automation), then interviews in AskUserQuestion rounds of ≤4 with concrete ASCII previews, **rebuilding the wireframe between rounds**, surfacing contradictions between your answers instead of silently reconciling them, and offering switchable variants side by side instead of arguing about aesthetics — while a **browser comment mode** (✎ or `c` in the wireframe) lets you pick any element and comment on it, the comment reaching the session with its selector, zone, and exact on-screen state, and replies threading back into the page's comment panel (instantly, when the optional `wireframe-feedback` channel is loaded; drained between rounds otherwise). It verifies by **measurement** — region contiguity, computed WCAG contrast, markup validity, off-screen focusables, scripted behaviour sequences — with the backgrounded-tab failure modes (scroll events, rAF, transitions and `.focus()` all silently no-op in a hidden tab) encoded as a hard checklist, labelling anything unmeasured "not verified" rather than claiming it. Ends at a spec grounded in real file paths, in the wiki or `./plans/<slug>.md`, then **auto-harvests a per-project reuse library** (`wireframes/_library/`: grounding cache, fragment files, decisions ledger + `wireframes/_index.md`) so the next wireframe in the same repo starts warm — cached values TTL-trusted and honestly labelled (`--ttl`, default 14 days; `--fresh` to bypass), prior verdicts imported as fixed context with one "reopen?" affordance. Composes both ways with `spec-elicitation`. **Writes no production code.**
29. **Confirm the build matches the wireframe**: Run `/bespokeagentics:wireframe-parity '<spec-or-slug>' --app <url>` — the **post-implementation** companion to `interactive-wireframe`. Once a wireframe spec has been built, it confirms the as-built UI matches what was decided, reusing the intended design the wireframe already froze (the spec's **Verification** `__wf` numbers, **Contract** invariants, **Decisions** table + `_library/decisions.md` ledger, and **States** table). It runs a **structural** pass (parallel `Explore` agents ground every settled decision/state/label in the real implementation at `file:line`, honored/drifted/missing — the floor, available under `--no-browser`) and a **measured** pass (serves the wireframe via `serve-wireframe.sh`, injects the **same** dependency-free probe — `wf-probe.js`, a standalone copy of `__wf` — into **both** the wireframe and the running app, drives each to the matching state, and diffs band geometry / contrast / markup / focusables / rendered labels / tokens apples-to-apples, parity being invariant-**within-tolerance** — ±2px, same AA/AAA verdict, contiguity as required — not pixel-identity). Auth-gated states are labelled **"not measured"**; a backgrounded-tab behavioural "failure" is treated as an artifact. Because **spec Decisions are the parity contract** and a build sometimes evolves past the wireframe on purpose, an **AskUserQuestion** interview classifies each divergence as **regression** / **intended evolution** / **out of scope** before any is called a failure (`--depth deep` adversarially verifies each first). Writes a **read-only** report to `./reviews/` — parity verdict (🟢/🟡/🔴), a decision-by-decision parity table, a measured table (intended / spec-frozen / as-built / Δ), label fidelity, a color-coded divergence register, an honest "not measured" section, and a "definition of parity" checklist — then **offers** to open the P0 regressions as tasks or refresh the stale ledger. Distinct from `plan-review` (audits a document before build) and `ux-audit` (heuristics): this audits a **built UI against the wireframe that specified it**. **The implementation is never modified.**

## Quality Standards

- All wiki pages must have valid YAML frontmatter
- All pages must have at least one `related:` back-reference
- No orphan pages (every page reachable from `_index.md`)
- No broken `[[wiki-links]]`
- Status fields use defined enums only
- Dates use ISO 8601 format (YYYY-MM-DD)
- File names use `lowercase-kebab-case.md`

Run `/wiki:lint --scope full` to check compliance.
