# Verndale Agentics — Agent Instructions

## Wiki-First Mandate

This project maintains a **Karpathy-style LLM wiki** at `wiki/`. The wiki is the single source of truth for all client intelligence, platform knowledge, technical decisions, and business capabilities. Every agent operating in this repository MUST use the wiki as its primary knowledge layer.

### Core Rules

1. **Query the wiki before answering any client or platform question.** Do not rely on memory or general knowledge when wiki pages exist. Run `/wiki:query` or read the relevant wiki pages directly. The wiki contains synthesized, cross-referenced, and validated knowledge that supersedes raw pipeline outputs.

2. **Update the wiki after every content-producing operation.** When a meeting is analyzed, a document is ingested, a decision is made, or a gap is identified — the wiki MUST be updated. No analysis output should exist only in `docs/` or pipeline outputs without a corresponding wiki page. Use `/wiki:ingest-meeting` or `/wiki:ingest-document` to route new content into the wiki.

3. **Never modify raw sources.** Pipeline outputs in `BostonBeerCompany/meetings/`, transcripts, and Confluence exports are immutable. The wiki references them but never edits them. If a raw source contains an error, note the correction in the wiki page and link back to the original.

4. **Maintain cross-references.** Every wiki page must link to related pages via `[[wiki-links]]` and `related:` frontmatter. When creating or updating a page, check for and add bidirectional links. If you mention a feature, link to it. If you reference a decision, link to the gap it resolves.

5. **Follow the schema.** All wiki pages must conform to `wiki/_schema/SCHEMA.md`. Use the templates in `wiki/_schema/templates/` for new pages. Every page requires valid YAML frontmatter with the correct `type` field.

6. **Log everything.** Every ingest, lint, scaffold, or maintenance operation must be recorded in `wiki/_log.md`. This is the audit trail — it answers "what changed, when, and why."

### When to Use Each Wiki Command

| Situation | Command |
|-----------|---------|
| Starting a brand-new wiki vault | `/wiki:init` |
| Adding a new client engagement | `/wiki:new-client '<company>' '<platform>'` |
| After running the migration pipeline on a meeting | `/wiki:ingest-meeting '<company>' '<meeting-dir>' '<label>'` |
| Received an email, spec, RFP, or other document | `/wiki:ingest-document '<company>' '<path>' '<type>'` |
| Someone asks a question about a client or platform | `/wiki:query '<question>' --client <slug>` |
| Weekly maintenance or health check | `/wiki:lint --scope full` |
| Checking wiki statistics | `/wiki:status` |
| Syncing with Confluence | Use the `wiki-confluence-reconcile` skill |

### Agent Workflow Integration

**Before starting any analysis task:**
1. Read `wiki/_schema/SCHEMA.md` to understand conventions
2. Read existing wiki pages for the client (`wiki/clients/{slug}/`)
3. Check `wiki/_index.md` for the current page inventory
4. Check `wiki/_log.md` for recent activity

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

## Project Structure

```
Vendale-Agentics/
├─ wiki/                          # THE WIKI — query and update this first
│  ├─ .obsidian/                  # Obsidian vault configuration
│  ├─ _schema/                    # Schema definition and 7 page templates
│  │  ├─ SCHEMA.md                # Core conventions (read this first)
│  │  └─ templates/               # feature, gap, meeting, decision, question, entity, integration
│  ├─ _index.md                   # Auto-maintained page catalog
│  ├─ _log.md                     # Chronological activity log
│  ├─ clients/                    # Per-client knowledge
│  │  └─ {client-slug}/           # e.g., boston-beer-company/
│  │     ├─ entities/             # Systems, vendors, people
│  │     ├─ features/             # Business capabilities
│  │     ├─ gaps/                 # Missing capabilities
│  │     ├─ decisions/            # Design and scope decisions
│  │     ├─ meetings/             # Meeting summaries
│  │     ├─ integrations/         # External data flows
│  │     └─ questions/            # Open questions
│  ├─ platforms/                  # Shared platform knowledge (reusable)
│  │  ├─ salesforce-b2b-commerce/
│  │  └─ salesforce-lwc/
│  └─ verndale/                   # Internal methodology
│     └─ processes/
├─ BostonBeerCompany/             # RAW SOURCES — immutable pipeline inputs/outputs
│  ├─ meetings/                   # Meeting recordings, transcripts, pipeline analysis
│  ├─ screencast/                 # Video frames, audio, transcripts
│  └─ docs/                       # Pipeline deliverables (gap analysis, etc.)
├─ .claude/
│  ├─ skills/                     # All agent skills
│  │  ├─ wiki-init/               # Initialize a new wiki vault
│  │  ├─ wiki-scaffold-client/    # Scaffold a new client workspace
│  │  ├─ wiki-ingest-meeting/     # Ingest meeting pipeline outputs
│  │  ├─ wiki-ingest-document/    # Ingest emails, specs, PDFs
│  │  ├─ wiki-confluence-reconcile/ # Bidirectional Confluence sync
│  │  ├─ wiki-lint/               # 7-dimension health check
│  │  ├─ wiki-query/              # Natural language search + synthesis
│  │  └─ (15 migration pipeline skills)
│  ├─ commands/wiki/              # Slash commands for wiki operations
│  │  ├─ init.md                  # /wiki:init
│  │  ├─ new-client.md            # /wiki:new-client
│  │  ├─ ingest-meeting.md        # /wiki:ingest-meeting
│  │  ├─ ingest-document.md       # /wiki:ingest-document
│  │  ├─ lint.md                  # /wiki:lint
│  │  ├─ query.md                 # /wiki:query
│  │  └─ status.md                # /wiki:status
│  └─ agents/
│     ├─ wiki-pipeline.md         # Wiki orchestration agent (3 workflows)
│     └─ migration-pipeline.md    # Migration analysis agent
└─ CLAUDE.md                      # THIS FILE — read first
```

## Migration Pipeline

The migration analysis pipeline is documented in `BostonBeerCompany/CLAUDE.md`. It has 6 phases (Preprocessing → Frame Analysis → Migration Analysis → Validation → Elicitation → Confluence Export) with 15 specialized skills and 8 orchestration options (A-H). Pipeline outputs are raw sources — they MUST be ingested into the wiki to become part of the compiled knowledge base.

### Pipeline → Wiki Flow

```
Meeting Recording
    ↓
Migration Pipeline (6 phases, 15 skills)
    ↓
Raw Outputs in docs/ (immutable)
    ↓
/wiki:ingest-meeting (wiki skill)
    ↓
Wiki Pages (evolving, cross-referenced, maintained)
```

**Never skip the wiki ingest step.** Pipeline outputs without wiki pages are invisible to the knowledge system.

## Scheduled Maintenance

A weekly maintenance task runs every Monday at 9am:
1. Full wiki lint (broken links, orphans, contradictions, stale pages)
2. Confluence reconciliation (if configured)
3. Index rebuild

## Quality Standards

- All wiki pages must have valid YAML frontmatter
- All pages must have at least one `related:` back-reference
- No orphan pages (every page reachable from `_index.md`)
- No broken `[[wiki-links]]`
- Status fields use defined enums only
- Dates use ISO 8601 format (YYYY-MM-DD)
- File names use `lowercase-kebab-case.md`

Run `/wiki:lint --scope full` to check compliance.
