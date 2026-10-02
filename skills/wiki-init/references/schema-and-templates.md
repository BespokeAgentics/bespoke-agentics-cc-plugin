# Schema, templates, indexes, and stubs

## Step 5a — `_schema/SCHEMA.md`

The schema is the **constitution** of the wiki. Tailor it to THIS project (interview answers, discovered domain/platforms), don't paste a generic boilerplate. Include these sections:

1. **Purpose** — explain the three-layer model with this project's vocabulary:
   - RAW SOURCES (immutable) — whatever content types exist in this repo.
   - THE WIKI (evolving, LLM-maintained) — the wiki folder structure created above.
   - THE SCHEMA (this file) — conventions, workflows, templates, lint rules.

2. **Architecture** — three-layer diagram using the actual top-level folder names from this project.
   Follow it with a **Vault layout** block that the other wiki skills read instead of assuming names:
   - Grouping folder: `clients/` | `projects/` | `teams/` | `domains/` (the Q3 answer).
   - Platforms: `platforms/` and the platform slugs created in Step 7 (or "none").
   - Default target platform: the platform new workspaces migrate to / build on, if the user named one (or "none — ask per workspace").
   - Org section: `{org-slug}/` from Q5 (or "none").

3. **Design principles**:
   - Immutability of sources — raw outputs never modified.
   - Machine-readable structure — YAML frontmatter, `[[wiki-links]]`, type conventions.
   - Traceability — every page links to source documents.
   - Compounding knowledge — each ingest improves existing pages.
   - 5th principle — adapt to the org structure (multi-client, multi-project, …).

4. **Page types** — all 7, with purpose and required frontmatter:

   | Type | Purpose | Required fields |
   | ---- | ------- | --------------- |
   | feature | Business capability or product feature | title, type, client, status, decision, sources, created, updated, related |
   | gap | Missing capability or limitation | title, type, client, severity, status, sources, created, updated, related |
   | meeting | Meeting summary with decisions | title, type, client, meeting-date, attendees, sources, created, updated, related |
   | decision | Design / scope / architecture decision | title, type, client, status, decision, sources, created, updated, related |
   | question | Open question needing resolution | title, type, client, status, priority, sources, created, updated, related |
   | entity | System, person, org, or tool | title, type, client, entity-type, status, created, updated, related |
   | integration | External system data flow or API | title, type, client, systems, direction, status, created, updated, related |

   The `client` field generalizes to whatever the top-level grouping is (client, project, team, domain).

   **One frontmatter schema, every page type:** `created` (ISO date the page was first written — never changed), `updated` (ISO date of the last substantive edit — ingest, sync and lint fixes bump it; wiki-lint's stale check reads it), `sources` (a YAML list of source paths/URLs the page draws on, appended to on every ingest). `status` is the lifecycle value; `decision` holds the Decision Status Color below. Do not use `date`, `source` or `status-color` — they are not part of the schema.

5. **Decision status colors** — the `decision` frontmatter key; the template comment is `decision: # ootb|config|custom|gap|tbd|third-party`, each value rendering as its color:
   - 🟢 OOTB — out of the box, no customization needed.
   - 🔵 Config — configurable, no custom code required.
   - 🟡 Custom Dev — requires custom development.
   - 🔴 Gap — not possible or requires a major workaround.
   - ⚪ TBD — not yet assessed.
   - 🟣 3rd Party — requires a third-party solution.

6. **Naming conventions** — kebab-case slugs, `.md` extension, ISO 8601 dates.
7. **Cross-reference rules** — `[[wiki-links]]`, `related:` frontmatter, bidirectional links.
8. **Core operations** — Ingest, Query, Lint (described generically).
9. **Wiki metadata files** — `_index.md`, `_log.md` (append-only; one `## YYYY-MM-DD — <operation> — <summary>` heading section per entry — see Step 6b), `_lint-report-{date}.md`.
10. **Quality standards** — valid frontmatter, back-references, no orphans, no broken links.

## Step 5b — Create all 7 page templates in `_schema/templates/`

Templates are structural scaffolds, identical across project types.

**Controlled keys carry their vocabulary as a trailing comment** — `severity: # critical|high|medium|low`,
`status: # open|mitigated|resolved|accepted`, `priority: # P1|P2|P3`. This is the single declaration:
project-db turns it into column docs, wiki-lint Check 6 validates against it, and `/ontology:init` mines
it into the ontology (after which the comment is rewritten to name its binding:
`severity: # gap.severity: critical|high|medium|low`). Do not restate the lists in SCHEMA.md — link to the
templates (or to `_schema/ONTOLOGY.md` once the ontology exists).

- `feature.md` — title, type, client, status, decision, sources, created, updated, related + Overview, Current Implementation, Target Implementation, Decision Status, Open Questions, Source References.
- `gap.md` — title, type, client, severity, status, sources, created, updated, related + Gap Description, Business Impact, Current Workaround, Proposed Resolution, Resolution Status, Source References.
- `meeting.md` — title, type, client, meeting-date, attendees, sources, created, updated, related + Summary, Key Topics, Decisions Made, Action Items, Features/Gaps/Questions Mentioned, Source.
- `decision.md` — title, type, client, status, decision, sources, created, updated, related + Decision, Context, Options Considered, Rationale, Implications, Status, Source References.
- `question.md` — title, type, client, status, priority, sources, created, updated, related + The Question, Context, Current Understanding, Proposed Answer, Related Features, Status, Source References.
- `entity.md` — title, type, client, entity-type, status, created, updated, related + Overview, Role in Project, Key Contacts, Related Systems, Notes.
- `integration.md` — title, type, client, systems, direction, status, created, updated, related + Overview, Current Data Flow, Data Elements table, Frequency & Trigger, Target Architecture, Source References.

## Step 6 — Global wiki files

### 6a. `_index.md`

```markdown
# Wiki Index

> Auto-maintained catalog of all wiki pages. Updated by ingest and lint operations.

**Last Updated**: {today}
**Total Pages**: 0

---

## {Top-Level Section Name}

_No entries yet. Use the appropriate wiki command to scaffold the first workspace._

---

{If platforms section exists:}
## Platforms

{List platform stubs created, or "No platform pages yet."}

---

{If org section exists:}
## {Org Name}

- [[processes/wiki-maintenance]] — Wiki maintenance procedures

---

## Schema

- [[SCHEMA]] — Core schema definition
- Templates: entity, feature, gap, decision, meeting, integration, question
```

### 6b. `_log.md`

```markdown
# Wiki Activity Log

> Chronological record of all wiki operations (oldest first). Every entry is appended at the end of this file as a heading section: `## YYYY-MM-DD — <operation> — <summary>` followed by a short prose/bullet body.

## {today} — wiki-init — Vault initialized

- Created: .obsidian config, `_schema/SCHEMA.md`, 7 templates, `_index.md`, `_log.md`{, N platform stubs}{, org processes}
- First-time setup
```

**Log entry format (every wiki skill writes exactly this):**

```markdown
## YYYY-MM-DD — <operation> — <one-line summary>

<short prose or bullets: scope, pages created/updated, notes>
```

`<operation>` is the skill/command name (`wiki-init`, `scaffold-client`, `ingest-meeting`, `ingest-document`, `query`, `lint`, `confluence-reconcile`, `wiki-to-mcp`, …). Always append at the end of the file; never prepend, never use a table. Record this format in SCHEMA.md section 9.

## Step 7 — Platform stubs (only if Q4 selected platforms)

Create one page per confirmed platform in `platforms/{platform-slug}.md`:

```markdown
---
title: "{Platform Name}"
type: entity
entity-type: platform
status: active
created: {today}
updated: {today}
sources: []
related: []
---

## Platform Overview
{Brief factual description — relevant to how it's used in THIS project}

## Key Capabilities
{Bullet list relevant to this project}

## Architecture Notes
{High-level architecture relevant to this project}
```

If no platforms were selected, skip Step 7 entirely.

## Step 8 — Org process stubs (only if Q5 org name was provided)

Create `{org-slug}/processes/wiki-maintenance.md`:

```markdown
---
title: "Wiki Maintenance Procedures"
type: process
status: active
created: {today}
updated: {today}
sources: []
related: []
---

## Overview
Standard operating procedures for maintaining wiki health, consistency, and completeness.

## On-Demand Operations

| Command | Purpose |
|---------|---------|
| `/wiki:init` | Initialize a new wiki vault |
| `/wiki:lint` | Run health check |
| `/wiki:query` | Search and synthesize knowledge |
| `/wiki:ingest-meeting` | Add meeting analysis to wiki |
| `/wiki:ingest-document` | Add email/spec/PDF to wiki |
| `/wiki:new-client` | Scaffold new client/project workspace |
| `/wiki:status` | View wiki statistics |

## Quality Gates
- No broken `[[wiki-links]]`.
- All pages have valid YAML frontmatter.
- No orphan pages (unreachable from `_index.md`).
- No stale pages (>30 days without update and status=stub).
- Cross-reference consistency.
```

Optionally add additional process pages only if repo discovery revealed concrete workflows (a migration pipeline, build process, research methodology). Never invent processes.

## Step 9 — Final summary

Tailor to what was actually created:

```
================================================================
  Wiki Initialized Successfully
================================================================

Vault:            {WIKI_DIR}
Project:          {project description}
Obsidian:         .obsidian/ (5 config files)
Schema:           _schema/SCHEMA.md + 7 templates
Global files:     _index.md, _log.md
Structure:        {top-level folders created}
Platform stubs:   {list, or "none"}
Process stubs:    {list, or "none"}

Total files created: {count}

Next Steps:
  1. Open the vault in Obsidian
  2. Add your first {client/project/entry}:
     /wiki:new-client '<name>' '<platform>'
  3. Optional: enforce the vocabulary (template value comments → dot-notated ontology + write hook):
     /ontology:init
  4. Ingest content:
     /wiki:ingest-meeting '<name>' '<dir>' '<label>'
     /wiki:ingest-document '<name>' '<path>' '<type>'
  5. Check wiki health:
     /wiki:lint --scope full

Wiki is ready for knowledge accumulation.
================================================================
```
