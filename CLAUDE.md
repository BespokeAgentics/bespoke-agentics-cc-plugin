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
    │  └─ bun-workspace/              # Convert/audit/extend Bun workspace monorepos
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

## Quality Standards

- All wiki pages must have valid YAML frontmatter
- All pages must have at least one `related:` back-reference
- No orphan pages (every page reachable from `_index.md`)
- No broken `[[wiki-links]]`
- Status fields use defined enums only
- Dates use ISO 8601 format (YYYY-MM-DD)
- File names use `lowercase-kebab-case.md`

Run `/wiki:lint --scope full` to check compliance.
