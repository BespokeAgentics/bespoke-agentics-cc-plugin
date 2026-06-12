# Bespoke Agentics — Wiki Plugin Instructions

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
    │  └─ knowledge-loop/             # Self-improving facts → hypotheses → rules loop
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
    │  └─ wiki-*.md                   # Flat command aliases
    ├─ agents/
    │  └─ wiki-pipeline.md            # Wiki orchestration agent (3 workflows)
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

## Quality Standards

- All wiki pages must have valid YAML frontmatter
- All pages must have at least one `related:` back-reference
- No orphan pages (every page reachable from `_index.md`)
- No broken `[[wiki-links]]`
- Status fields use defined enums only
- Dates use ISO 8601 format (YYYY-MM-DD)
- File names use `lowercase-kebab-case.md`

Run `/wiki:lint --scope full` to check compliance.
