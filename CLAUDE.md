# Bespoke Agentics — Plugin Instructions

## Response Style

Responses to the user should be brief and specific to the request; the user will ask for more detail when they want it.

## Operating Manual (read first)

Every agent operating in this repository is governed by [`OPERATING-MANUAL.md`](OPERATING-MANUAL.md) — the working method for all responses: read the intent beneath the request, decompose into independently checkable pieces, spend verification where errors are expensive, re-derive every fact and figure passing through you, label guesses inline, attack your own conclusion, and lead with the answer. It applies to every task, then the domain-specific rules below apply on top. When a rule there conflicts with a request's phrasing, the rule that protects correctness wins.

## Wiki-First Mandate

When a project has a wiki (at `wiki/` or configured via `/wiki:init`), the wiki is the **single source of truth** for all project intelligence, technical decisions, and business capabilities. Every agent operating in this repository MUST use the wiki as its primary knowledge layer.

Full descriptions of every skill: README.md § Skill reference.

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
| Syncing with Confluence                         | `/bespoke-agentics:wiki-confluence-reconcile`             |

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

Builds the _context/memory_ layer (CLAUDE.md/AGENTS.md hierarchy + `.claude/` config); `architect-agents` builds the _agent/command_ layer.

### When to Use Each Funcspec Command

| Situation                                                                                                              | Command                                                                                    |
| ---------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------ |
| Evaluate a Storybook's pages page-by-page and infer the functionality the UI implies                                   | `/bespoke-agentics:funcspec-evaluate [<workspace>] [--pages a,b] [--visual auto\|on\|off]` |
| Validate findings with the user and generate the implementation plan (spec, plan, backlog, gap register, traceability) | `/bespoke-agentics:funcspec-plan [--push ask\|none]`                                       |
| Check the state of a funcspec run (profiles, ambiguities, deliverables)                                                | `/bespoke-agentics:funcspec-status [<workspace>]`                                          |

Extracts the _functional_ layer from a Storybook; `claude-design-to-app-workflow` recovers the _visual_ layer.

### When to Use Each Knowledge Loop Command

| Situation                                                                                            | Command                                                              |
| ---------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------- |
| Stand up the learning loop (scaffold store, install CLAUDE.md mandate + SessionStart hook)           | `/knowledge:init [--path <dir>] [--domains <a,b,c>]`                 |
| Before starting a task — load the rules that apply by default + the hypotheses today's work can test | `/knowledge:review [<task>] [--domain <slug>]`                       |
| After a task — capture insights; auto-promote at 3+ confirmations, auto-demote contradicted rules    | `/knowledge:extract [<what you learned>] [--domain <slug>]`          |
| Bridge confirmed rules into proper wiki pages (or manually promote/demote)                           | `/knowledge:promote [--domain <slug>] [--rule <id>] [--demote <id>]` |
| Health-check the store (promotion candidates, stale entries, integrity, broken links)                | `/knowledge:audit [--domain <slug>] [--stale-days <n>] [--fix]`      |

The project's _learning layer_ (facts → hypotheses → rules), stored inside the wiki at `wiki/knowledge/`.

### When to Use Each Project DB Command

| Situation                                                                                        | Command                                            |
| ------------------------------------------------------------------------------------------------ | -------------------------------------------------- |
| Make the wiki (or a no-wiki project's docs + data) queryable with SQL; install hook + mandate     | `/db:init [--mode local\|d1\|both] [--slug <s>]`  |
| Structured question: counts, filters, joins, "what links to X", "which meetings discussed Y"     | `/db:query '<question or SELECT …>'`               |
| Wiki/sources changed, or `views.sql` / `config.json` edited                                      | `/db:sync [--full] [--verify]`                     |
| Publish to Cloudflare D1 and deploy the read-only MCP Worker (modes `d1`, `both`)                | `/db:publish [--dry-run]`                          |

The wiki's _query layer_: the wiki stays the record, `.claude/db/project.sqlite` is the index.

### When to Use Each Project Ontology Command

| Situation                                                                                                   | Command                                                                     |
| ----------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------- |
| Values drift (a client spelled two ways, statuses no template declares); make the vocabulary enforceable    | `/ontology:init [--govern <dir>]`                                           |
| Check pages, the vault, or only what a branch changed against the vocabulary                                | `/ontology:check [<path>\|--all\|--changed-since <ref>]`                   |
| A page genuinely needs a value the vocabulary lacks                                                         | `/ontology:propose <id> --label '…' --definition '…'`                       |
| Decide pending terms (humans only) / retire a term                                                          | `/ontology:approve <id>…` · `/ontology:deprecate <id> --replaced-by <id>`   |
| Rewrite aliases, spelling variants, deprecated values, noncanonical links                                   | `/ontology:apply --dry-run`, then `/ontology:apply`                         |
| Counts, open violations, pending approvals                                                                  | `/ontology:status`                                                          |

The wiki's _vocabulary layer_: `wiki/_schema/ontology.yaml`, enforced by hooks; only humans approve or deprecate terms.

### When to Use the Repo Audit Command

| Situation                                                                              | Command                                                                                |
| -------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------- |
| Get an honest, evidence-based health check of a repository with a prioritized fix plan | `/bespoke-agentics:repo-audit [<path>] [--depth quick\|standard\|deep] [--out <file>]` |

### When to Use the UI-Issue-to-Plan Command

| Situation                                                                                                           | Command                                                                                                                         |
| ------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------- |
| Turn a narrated screen recording into a code-grounded plan that captures both what to fix AND how to improve the UX | `/bespoke-agentics:ui-issue-to-plan '<video>' [issue-label] [interval] [--mode fix\|improve\|both] [--out <dir>] [--no-ground]` |

Unlike `video-to-deliverables`/`workflow-analyzer`, it grounds each on-screen component in this repo's code and stops at a plan in `./plans/`.

### When to Use the Highlight Reel Command

| Situation                                                                                                                                          | Command                                                                                                                                                                              |
| -------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Turn a long app-demo screencast into a short, narrated, subtitled highlight video — grounded in this repo so the voiceover is technically accurate | `/bespoke-agentics:highlight-reel '<video>' [reel-label] [interval] [--duration <sec>] [--voice <id>] [--audio duck\|keep\|mute] [--no-subs] [--no-ground] [--no-tts] [--out <dir>]` |

### When to Use the Plan-Review Command

| Situation                                                                                                                                                        | Command                                                                                                                                   |
| ---------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------- |
| Pressure-test a written implementation plan, spec, or issue/bug report **before** building it — find the gaps, ambiguities, and risks, grounded in the real code | `/bespoke-agentics:plan-review '<artifact>' [--type plan\|issue\|spec\|auto] [--depth quick\|standard\|deep] [--out <dir>] [--no-ground]` |

Audits a written plan against the code before build (`repo-audit` audits code, `ux-audit` a UI); never modifies the original.

### When to Use the Data-UI Craft Command

| Situation                                                                                                                                     | Command                                                                                |
| --------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------- |
| Audit and/or implement the craft details that make a data-dense UI (dashboard, table, admin panel, data grid, list/detail view) actually work | `/bespoke-agentics:data-ui-craft [mode: audit\|implement\|audit-and-implement] [path]` |

The data-display craft layer; `ux-audit` covers general Nielsen/Norman heuristics.

### When to Use the XState Refactor Command

| Situation                                                                                                                                                                                                          | Command                                                                                                                                                        |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Refactor a feature's ad-hoc state logic + UI into an explicit XState v5 machine, statechart, or actor system — with a validated plan, full state↔UI coverage, deterministic tests, and deprecation of the old code | `/bespoke-agentics:xstate-refactor '<target>' [--mode plan\|implement\|full] [--style machine\|statechart\|actors\|auto] [--out <dir>] [--no-tests] [--force]` |

### When to Use the Orchestrate Command

| Situation                                                                                                                                                                   | Command                                                                                                                                                                              |
| --------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Execute an implementation plan (or a raw task) through a managed, gated, multi-agent build — the session model orchestrates, Opus/Sonnet subagents implement and smoke-test | `/bespoke-agentics:orchestrate '<plan-path-or-task>' [--depth quick\|standard\|deep] [--dry-run] [--no-confirm] [--no-smoke] [--no-review] [--single-model <m>] [--resume [<slug>]]` |

Parallel waves, never commits; `workstream-orchestrate` is the sequential, commit-per-workstream sibling.

### When to Use the Workstream-Orchestrate Command

| Situation                                                                                                                                                                                    | Command                                                                                                                                                                                                     |
| -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Turn a plan into a kickoff contract, then build it one workstream at a time — each `code → validate → commit`, with a server-side hard-gate proof and a human checkpoint between workstreams | `/bespoke-agentics:workstream-orchestrate '<plan-path-or-task>' [--from WS-n] [--to WS-m] [--engine workflow\|agent] [--attempts N] [--no-commit] [--no-confirm] [--dry-run] [--resume [<slug>]] [--force]` |

Sequential sibling of `orchestrate`: one Conventional Commit per validated workstream, with a human checkpoint between.

### When to Use the Agent-Loop Audit Command

| Situation                                                                                                                                                     | Command                                                                                   |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------- |
| Audit (and optionally fix) an AI API/SDK integration for the event-loop defects that cause silent hangs, stalls, and deadlocks in managed-agent architectures | `/bespoke-agentics:agent-loop-audit [mode: audit\|implement\|audit-and-implement] [path]` |

The protocol/control-loop layer beneath `ai-transparency` and `ai-waiting-ux`.

### When to Use the Screencast-Capture Command

| Situation                                                                                                                                                                                                                                        | Command                                                                                                                                                                                                        |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Record a browser flow you describe as a screencast — the agent drives Claude-in-Chrome, records it (default gif, or `--engine screen` for native-resolution monitor capture), makes an MP4, and offers to turn it into a narrated highlight reel | `/bespoke-agentics:screencast-capture ['<start-url-or-flow>'] [capture-label] [--engine chrome-gif\|screen] [--display <idx>] [--crf <n>] [--overlays clean\|clicks\|full] [--reel] [--no-reel] [--out <dir>]` |

Produces the screencast that `highlight-reel` polishes.

### When to Use the Interactive-Wireframe Command

| Situation                                                                                                                    | Command                                                                                                                                                                         |
| ---------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Settle an undecided UI change by building a live, code-grounded HTML wireframe, interviewing against it, and emitting a spec | `/bespoke-agentics:interactive-wireframe '<surface>' [--slug <name>] [--rounds N] [--port N] [--out <dir>] [--spec <path>] [--fresh] [--ttl <days>] [--no-verify] [--no-serve]` |

`reimagine` explores **which** design, `interactive-wireframe` settles **the** design, `wireframe-parity` checks the build; none writes production code.

### When to Use the Wireframe-Parity Command

| Situation                                                                | Command                                                                                                                                                       |
| ------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Confirm the UI that was implemented matches the wireframe a spec settled | `/bespoke-agentics:wireframe-parity '<spec-or-slug>' --app <url> [--wireframe <path>] [--depth quick\|standard\|deep] [--out <dir>] [--no-browser] [--force]` |

Post-build companion to `interactive-wireframe`; read-only — the implementation is never modified.

### When to Use the Reimagine Command

| Situation                                                                                                                        | Command                                                                                                                                                                                                                                         |
| -------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Explore what an existing component/page could become — a live gallery of brand-faithful redesign directions, settled into a spec | `/bespoke-agentics:reimagine '<surface>' [--slug <name>] [--tiers restyle,restructure,rethink] [--variants N] [--rounds N] [--baseline-url <url>] [--port N] [--out <dir>] [--spec <path>] [--fresh] [--ttl <days>] [--no-verify] [--no-serve]` |

Upstream of `interactive-wireframe`: explores which design an existing surface could become; writes no production code.

### When to Use the Dead-Code-Sweep Command

| Situation                                                                                                                                  | Command                                                                                                         |
| ------------------------------------------------------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------- |
| Right after a coding session — find and remove the dead code the changes left behind (including stale tests), with proof nothing regressed | `/bespoke-agentics:dead-code-sweep [uncommitted\|branch\|project] [--base <ref>] [--report-only] [--out <dir>]` |

Deletes proven-dead code in gated, backed-up waves; `repo-audit` only reports. Never commits.

### When to Use the Defect-Intake Command

| Situation                                                                                                                                                    | Command                                                                                |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------------- |
| A defect surfaced mid-session (bug, missing test, swallowed error, contract violation, gap) and it needs proper disposition instead of a note in the summary | `/bespoke-agentics:defect-intake '<defect description, file:line, or failing output>'` |

User-invoked only; dispositions one known defect (`repo-audit`/`dead-code-sweep` hunt across a scope). Never commits.

### When to Use the Misunderstanding Command

| Situation                                                                                                                     | Command                                                           |
| ----------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------- |
| A plan step, wiki claim, doc, or earlier turn led the agent to infer something wrong, and work is being built on that reading | `/bespoke-agentics:misunderstanding ['<what was misunderstood>']` |

User-invoked only; corrects a wrong inference and the source that seeded it. Never commits.

### When to Use the Delivery-Recap Command

| Situation                                                                                                                       | Command                                                                                                       |
| ------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------- |
| A PM, tech lead, or client needs to know what actually shipped — and be able to open the site and verify it without asking you | `/bespoke-agentics:delivery-recap [window] [--author me] [--sessions current\|all\|none] [--out <dir>]` |

Read-only report of what a human delivered, for a human reader (`repo-audit` grades code health).

### When to Use the Skill-Reverse-Engineer Command

| Situation                                                                                                                         | Command                                                                                                            |
| --------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------ |
| A skill works but behaves differently every run — reverse-engineer it and make it more deterministic, robust, and less AI-reliant | `/bespoke-agentics:skill-reverse-engineer '<skill-path-or-name>' [--mode audit\|apply\|new-version] [--out <dir>]` |

Hardens an existing skill; `skill-creator` creates and eval-iterates new ones.

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

The MicroDots framework (Effect v4 + Foldkit) end to end; every command resolves the workspace before acting.

### When to Use the AI-Native SDLC Command

| Situation                                                                                                                                     | Command                                                                                          |
| ---------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------ |
| Transform the process around agentic coding — score a repo's SDLC maturity, install the playbook's controls, or drive work through the artifact chain | `/bespoke-agentics:ai-native-sdlc [mode: assess\|adopt\|run] [plays or '<work item>'] [--home <dir>] [--out <file>] [--no-confirm]` |

Transforms the process (who approves which artifact); `/agentnative:suite` makes the repo a good workspace for agents.

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

Dependency order: fast-ci → hermetic-deploy → sim-data → proof-of-work → issue-to-agent → chore-crons; `/agentnative:suite` conducts them.

### Agent Workflow Integration

**Before starting any analysis task:**

1. Check if a wiki exists at `wiki/` — if not, suggest running `/wiki:init`
2. Read `wiki/_schema/SCHEMA.md` to understand conventions
3. Read existing wiki pages for the relevant client/project
4. Check `wiki/_index.md` for the current page inventory
5. Check `wiki/_log.md` for recent activity

**After completing any analysis task:**

1. Ingest results with `/wiki:ingest-meeting` or `/wiki:ingest-document`
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

## Invocation Policy — manual-only

Nothing in this plugin triggers except manual invocation. Every `skills/*/SKILL.md` and every command
carries `disable-model-invocation: true`, which takes its name and description out of the model's
context; the user reaches it by typing its `/name`. The only exceptions are the eight commands in
`scripts/invocation-policy.json` — the ones that text the plugin installs into a user's project
(the Wiki-First Mandate, the knowledge banner, the project-db and project-ontology blocks) tells an
agent to run unprompted. Each carries its reason there.

When adding or changing a skill, command or agent:

1. **Flag it.** New skills and commands ship with `disable-model-invocation: true`. Adding to the
   allowlist needs an installed mandate that names the command, recorded as its `why`.
2. **Never dispatch a plugin skill through the Skill tool.** The harness refuses a flagged skill
   ("cannot be used with Skill tool due to disable-model-invocation"). A wrapper command, conductor,
   agent, or accepted handoff **loads by path**: read `${CLAUDE_PLUGIN_ROOT}/skills/<name>/SKILL.md`
   and follow it. `${CLAUDE_PLUGIN_ROOT}` is substituted in command and agent bodies; a SKILL.md read
   this way arrives raw, so say that its arguments are the command's and its paths are relative to its
   own directory.
3. **Run the guard.** `python3 scripts/check-invocation-policy.py` and
   `python3 scripts/test-check-invocation-policy.py` (CI: `.github/workflows/invocation-policy.yml`).

Evidence, the probes that settled the undocumented mechanics, and what is not verified:
`docs/plans/plugin-context-reduction.md`.

---

## Plugin Structure

    bespoke-agentics-plugin/
    ├─ skills/                        # One directory per skill (`ls skills/` is the full inventory; highlights below)
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
    │  ├─ orchestrate/                # Plan/task → gated multi-agent implementation (session model orchestrates, Opus/Sonnet implement)
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
    │  ├─ hook/                       # /hook:{add-start,add-stop,design,inspect} (session-hooks)
    │  ├─ submodule/                  # /submodule:{add,convert,init,status} (git-submodules)
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
    │  NOTE: command files are thin wrappers that load one skill by path
    │  (${CLAUDE_PLUGIN_ROOT}/skills/<name>/SKILL.md). A skill with no
    │  wrapper is invoked as /bespoke-agentics:<skill-name> — see skills/ above.
    ├─ agents/                        # Subagent definitions (`ls agents/` is the full inventory; highlights below)
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

## Quality Standards

- All wiki pages must have valid YAML frontmatter
- All pages must have at least one `related:` back-reference
- No orphan pages (every page reachable from `_index.md`)
- No broken `[[wiki-links]]`
- Status fields use defined enums only
- Dates use ISO 8601 format (YYYY-MM-DD)
- File names use `lowercase-kebab-case.md`

Run `/wiki:lint --scope full` to check compliance.
