---
name: wiki-init
description: "Initialize a brand-new Karpathy-style LLM wiki vault from scratch. Creates the Obsidian vault structure, schema, all 7 page templates, global indexes, platform stubs, and optionally scaffolds the first client."
args:
  - name: wiki-dir
    description: "Path where the wiki vault should be created (default: './wiki'). The directory must not already exist."
    required: false
  - name: first-client
    description: "Optional company name for the first client to scaffold (e.g., 'Boston Beer Company'). If provided, also requires platform-source."
    required: false
  - name: platform-source
    description: "Source platform for the first client (e.g., 'MerchTank', 'Shopify Plus'). Required if first-client is provided."
    required: false
  - name: platform-target
    description: "Target platform for the first client (default: 'Salesforce B2B Commerce'). Optional."
    required: false
---

You are the Wiki Init agent. Your job is to create an entirely new Karpathy-style LLM wiki vault from scratch — the foundational vault structure, Obsidian configuration, schema, all page templates, global indexes, and optionally the first client workspace.

## When to Use This Skill

Use this skill to:
- Create a brand-new wiki vault for a fresh project or team
- Set up the complete Obsidian-compatible knowledge base infrastructure
- Initialize all schema files, templates, and configuration from zero
- Optionally scaffold the first client in the same operation

This is the **first thing you run** when starting a new wiki. It replaces the manual vault setup. After init, use `/wiki:new-client` to add clients, `/wiki:ingest-meeting` to populate content, and `/wiki:lint` to validate health.

## Required Context

- The wiki directory must NOT already exist (safety check)
- The current working directory should be the project root (where `.claude/` lives)

## Process

### Step 1: Pre-flight Validation

1. **Resolve WIKI_DIR**: Use the `wiki-dir` argument if provided, otherwise default to `./wiki`
2. **Check directory does NOT exist**: If `{WIKI_DIR}` already exists, STOP and report:
   ```
   ✗ Wiki already exists at {WIKI_DIR}
     Use /wiki:new-client to add a client, or delete the directory first.
   ```
3. **Validate first-client args**: If `first-client` is provided but `platform-source` is missing, STOP and report:
   ```
   ✗ --platform-source is required when --first-client is specified
   ```

Report pre-flight status:
```
=== Wiki Init ===
Wiki directory:  {WIKI_DIR}
First client:    {first-client or "none"}
Platform source: {platform-source or "n/a"}
Platform target: {platform-target or "Salesforce B2B Commerce"}
Status:          ✓ Ready to initialize
```

### Step 2: Create Root Directory Structure

Create the complete vault skeleton:

```
{WIKI_DIR}/
├─ .obsidian/              # Obsidian app configuration
├─ _schema/                # Schema definition and templates
│  └─ templates/           # 7 page-type templates
├─ clients/                # Per-client knowledge (one folder per engagement)
├─ platforms/              # Shared platform knowledge (reusable across clients)
│  └─ salesforce-b2b-commerce/
│  └─ salesforce-lwc/
├─ verndale/               # Internal methodology and process knowledge
│  └─ processes/
```

Create all directories in individual `mkdir -p` calls (do NOT use brace expansion — it fails in some shells).

### Step 3: Create Obsidian Configuration

#### 3a. `.obsidian/app.json`
```json
{
  "showFrontmatter": true,
  "livePreview": true,
  "defaultViewMode": "source",
  "strictLineBreaks": false,
  "showLineNumber": true,
  "readableLineLength": true
}
```

#### 3b. `.obsidian/appearance.json`
```json
{
  "baseFontSize": 16,
  "theme": "obsidian"
}
```

#### 3c. `.obsidian/core-plugins.json`
```json
[
  "file-explorer",
  "global-search",
  "switcher",
  "graph",
  "backlink",
  "outgoing-link",
  "tag-pane",
  "page-preview",
  "templates",
  "note-composer",
  "command-palette",
  "editor-status",
  "markdown-importer",
  "outline",
  "word-count"
]
```

#### 3d. `.obsidian/graph.json`
```json
{
  "collapse-filter": false,
  "search": "",
  "showTags": true,
  "showAttachments": false,
  "hideUnresolved": false,
  "showOrphans": true,
  "collapse-color-groups": false,
  "colorGroups": [
    { "query": "path:clients", "color": { "a": 1, "rgb": 3447003 } },
    { "query": "path:platforms", "color": { "a": 1, "rgb": 65280 } },
    { "query": "path:verndale", "color": { "a": 1, "rgb": 16750848 } },
    { "query": "tag:#gap", "color": { "a": 1, "rgb": 16711680 } },
    { "query": "tag:#decision", "color": { "a": 1, "rgb": 10040268 } },
    { "query": "tag:#question", "color": { "a": 1, "rgb": 16776960 } }
  ],
  "collapse-display": false,
  "showArrow": true,
  "textFadeMultiplier": 0,
  "nodeSizeMultiplier": 1,
  "lineSizeMultiplier": 1,
  "collapse-forces": true,
  "centerStrength": 0.5,
  "repelStrength": 10,
  "linkStrength": 1,
  "linkDistance": 250
}
```

#### 3e. `.obsidian/workspace.json`
```json
{
  "main": {
    "id": "main",
    "type": "split",
    "children": []
  },
  "left": {
    "id": "left",
    "type": "split",
    "children": [],
    "direction": "horizontal",
    "width": 300
  },
  "right": {
    "id": "right",
    "type": "split",
    "children": [],
    "direction": "horizontal",
    "width": 300
  },
  "active": "main"
}
```

### Step 4: Create the Schema

#### 4a. `_schema/SCHEMA.md`

This is the **core definition file** for the entire wiki. Write the complete schema document including:

1. **Purpose** — Explain the Karpathy three-layer model (Raw Sources → Wiki → Schema). The wiki is a continuously maintained knowledge base that compounds over time. It synthesizes and cross-references knowledge from raw pipeline outputs. It serves both human consultants and LLMs.

2. **Architecture** — The three-layer diagram:
   - RAW SOURCES (Immutable): pipeline outputs, transcripts, emails, Confluence exports
   - THE WIKI (Evolving, LLM-Maintained): `clients/`, `platforms/`, `verndale/`, `_schema/`
   - THE SCHEMA (This File): conventions, workflows, templates, lint rules

3. **Design Principles**:
   - Immutability of Sources — raw outputs never modified, wiki references them
   - Machine-Readable Structure — YAML frontmatter, `[[wiki-links]]`, type conventions
   - Traceability — every page links to source documents and forward to decisions
   - Compounding Knowledge — each ingest adds to and improves existing pages
   - Multi-Client Architecture — shared platform knowledge, client-specific intelligence

4. **Page Types** — Define all 7 page types with their purpose and required frontmatter fields:

   | Type | Purpose | Required Fields |
   |------|---------|----------------|
   | **feature** | Business capability | title, type, client, status, source, date, related |
   | **gap** | Missing capability or limitation | title, type, client, severity, status, source, date, related |
   | **meeting** | Meeting summary with decisions | title, type, client, meeting-date, attendees, source, date, related |
   | **decision** | Design or scope decision | title, type, client, status-color, date, related |
   | **question** | Open question needing resolution | title, type, client, status, priority, source, date, related |
   | **entity** | System, person, or organization | title, type, client, entity-type, status, date, related |
   | **integration** | External system data flow | title, type, client, systems, direction, status, date, related |

5. **Decision Status Colors**:
   - 🟢 OOTB — Out of the box, no customization needed
   - 🔵 Config — Configurable, no custom code required
   - 🟡 Custom Dev — Requires custom development
   - 🔴 Gap — Not possible or requires major workaround
   - ⚪ TBD — Not yet assessed
   - 🟣 3rd Party — Requires third-party solution

6. **Naming Conventions**:
   - File names: `lowercase-kebab-case.md`
   - Client slugs: `lowercase-kebab-case` of company name
   - Platform slugs: `lowercase-kebab-case` of platform name
   - All files use `.md` extension

7. **Cross-Reference Rules**:
   - Use `[[page-name]]` for wiki links (Obsidian-style)
   - Use `related:` frontmatter array for structured back-references
   - Every feature should link to its source meeting
   - Every gap should link to the feature it blocks
   - Every decision should link to the gap or question it resolves

8. **Core Operations**:
   - **Ingest**: New content → read → extract entities → update/create wiki pages → cross-reference → log
   - **Query**: Natural language question → search wiki → synthesize answer → optionally promote to page
   - **Lint**: Periodic health check → broken links, orphans, stale pages, contradictions → report

9. **Wiki Metadata Files**:
   - `_index.md` — Auto-maintained catalog of all pages, grouped by client and type
   - `_log.md` — Chronological record of every ingest, lint, and maintenance operation
   - `_lint-report-{date}.md` — Periodic lint reports

10. **Quality Standards**:
    - Every page must have valid YAML frontmatter
    - Every page must have at least one `related:` back-reference
    - Status fields must use defined enums
    - Dates use ISO 8601 format (YYYY-MM-DD)
    - No orphan pages (every page reachable from _index.md)

#### 4b. Create All 7 Page Templates

Create each template in `_schema/templates/`:

**`_schema/templates/feature.md`**:
```markdown
---
title: "{Feature Name}"
type: feature
client: {client-slug}
status: "{assessed|stub|confirmed|deferred}"
source: "{source-reference}"
date: {YYYY-MM-DD}
related:
  - "{related-page}"
---

## Overview
{Brief description of the business capability}

## Current Implementation
{How it works in the source platform}

## Target Implementation
{How it should work in the target platform}

## Decision Status
{🟢🔵🟡🔴⚪🟣} — {Assessment summary}

## Open Questions
- {Any unresolved questions}

## Source References
- {Links to source documents, meetings, pipeline outputs}
```

**`_schema/templates/gap.md`**:
```markdown
---
title: "{Gap Name}"
type: gap
client: {client-slug}
severity: "{critical|high|medium|low}"
status: "{open|mitigated|accepted|resolved}"
source: "{source-reference}"
date: {YYYY-MM-DD}
related:
  - "{related-feature}"
  - "{related-decision}"
---

## Gap Description
{What capability is missing or limited}

## Business Impact
{Why this matters to the client}

## Current Workaround
{How the client handles this today, if at all}

## Proposed Resolution
{Recommended approach to address the gap}

## Resolution Status
{Current status and next steps}

## Source References
- {Links to source documents where gap was identified}
```

**`_schema/templates/meeting.md`**:
```markdown
---
title: "{Meeting Label}"
type: meeting
client: {client-slug}
meeting-date: {YYYY-MM-DD}
attendees:
  - "{Name (Role)}"
source: "{transcript-path}"
date: {YYYY-MM-DD}
related:
  - "{related-features}"
  - "{related-decisions}"
---

## Summary
{2-3 paragraph executive summary of the meeting}

## Key Topics Discussed
{Major themes and discussion areas}

## Decisions Made
{Decisions reached during the meeting}

## Action Items
- [ ] {Action item with owner and deadline}

## Features Mentioned
- [[{feature-page}]] — {brief context}

## Gaps Identified
- [[{gap-page}]] — {brief context}

## Open Questions
- [[{question-page}]] — {brief context}

## Source
- Transcript: {path to raw transcript}
- Pipeline analysis: {path to pipeline outputs}
```

**`_schema/templates/decision.md`**:
```markdown
---
title: "{Decision Title}"
type: decision
client: {client-slug}
status-color: "{🟢|🔵|🟡|🔴|⚪|🟣}"
date: {YYYY-MM-DD}
related:
  - "{related-feature}"
  - "{related-gap}"
---

## Decision
{Clear statement of the decision}

## Context
{Why this decision was needed — what gap, question, or feature drove it}

## Options Considered
1. **{Option A}** — {pros/cons}
2. **{Option B}** — {pros/cons}

## Rationale
{Why this option was chosen}

## Implications
{What this means for the project — affected features, timeline, resources}

## Status
{status-color} — {OOTB|Config|Custom Dev|Gap|TBD|3rd Party}

## Source References
- {Links to meetings or documents where this was decided}
```

**`_schema/templates/question.md`**:
```markdown
---
title: "{Question}"
type: question
client: {client-slug}
status: "{open|answered|deferred|escalated}"
priority: "{P1|P2|P3}"
source: "{source-reference}"
date: {YYYY-MM-DD}
related:
  - "{related-feature}"
  - "{related-gap}"
---

## The Question
{Question as stated}

## Context
{Why this matters, what depends on the answer}

## Current Understanding
{What we know so far}

## Proposed Answer
{Best answer based on available information, if any}

## Related Features
- [[{feature}]] — {why it's related}

## Status
{Open/Answered/Deferred/Escalated} — {details}

## Source References
- {Where this question was first raised}
```

**`_schema/templates/entity.md`**:
```markdown
---
title: "{Entity Name}"
type: entity
client: {client-slug}
entity-type: "{client|vendor|source-platform|target-platform|erp|person|team}"
status: "{active|inactive|deprecated}"
date: {YYYY-MM-DD}
related:
  - "{related-entity}"
---

## Overview
{Brief description of the entity}

## Role in Migration
{How this entity is involved in the migration project}

## Key Contacts
- {Name, Role, Contact info}

## Related Systems
- [[{system-page}]] — {relationship description}

## Notes
{Additional context}
```

**`_schema/templates/integration.md`**:
```markdown
---
title: "{Integration Name}"
type: integration
client: {client-slug}
systems:
  - "{system-a}"
  - "{system-b}"
direction: "{unidirectional|bidirectional}"
status: "{active|planned|deprecated|unknown}"
date: {YYYY-MM-DD}
related:
  - "{related-entity}"
  - "{related-feature}"
---

## Overview
{What data flows between which systems and why}

## Current Data Flow
{Description of current integration behavior}

## Data Elements
| Field | Source | Target | Transform |
|-------|--------|--------|-----------|
| {field} | {source} | {target} | {transform} |

## Frequency & Trigger
{Real-time, batch, event-driven, scheduled}

## Migration Impact
{How this integration is affected by the platform migration}

## Target Architecture
{How this integration should work post-migration}

## Source References
- {Links to technical documentation, architecture diagrams}
```

### Step 5: Create Global Wiki Files

#### 5a. `_index.md`

```markdown
# Wiki Index

> Auto-maintained catalog of all wiki pages. Updated by ingest and lint operations.

**Last Updated**: {today}
**Total Pages**: 0

---

## Clients

_No clients yet. Use `/wiki:new-client` to scaffold the first client workspace._

---

## Platforms

- [[salesforce-b2b-commerce/overview]] — Salesforce B2B Commerce platform knowledge
- [[salesforce-lwc/overview]] — Salesforce Lightning Web Components reference

---

## Verndale

- [[processes/wiki-maintenance]] — Wiki maintenance procedures
- [[processes/migration-analysis-pipeline]] — 6-phase migration analysis pipeline

---

## Schema

- [[SCHEMA]] — Core schema definition
- Templates: entity, feature, gap, decision, meeting, integration, question
```

#### 5b. `_log.md`

```markdown
# Wiki Activity Log

> Chronological record of all wiki operations. Each row records an ingest, lint, scaffold, or maintenance event.

| Date | Operation | Scope | Details | Notes |
|------|-----------|-------|---------|-------|
| {today} | wiki-init | global | Vault initialized: .obsidian config, schema, 7 templates, global indexes, platform stubs | First-time setup |
```

### Step 6: Create Platform Stub Pages

#### 6a. `platforms/salesforce-b2b-commerce/overview.md`

```markdown
---
title: "Salesforce B2B Commerce"
type: entity
entity-type: target-platform
status: active
date: {today}
related: []
---

## Platform Overview

Salesforce B2B Commerce (formerly CloudCraze) is an enterprise B2B ecommerce platform built natively on the Salesforce Platform. It supports complex B2B buying scenarios including contract pricing, account hierarchies, large catalogs, and reordering workflows.

## Key Capabilities

- Account-based pricing and entitlements
- Complex product catalogs with configurable attributes
- Cart and checkout with B2B-specific logic
- Integration with Salesforce CRM, CPQ, and Service Cloud
- Lightning Web Components (LWC) storefront framework
- Multi-site, multi-language, multi-currency support

## Architecture Notes

Built on Salesforce Platform (Force.com). Storefront uses Lightning Web Runtime (LWR) or Aura. Data model leverages standard and custom Salesforce objects.

## Decision Patterns

Common decision patterns for B2B Commerce migrations are documented per-client in their respective `decisions/` folders.
```

#### 6b. `platforms/salesforce-lwc/overview.md`

```markdown
---
title: "Salesforce Lightning Web Components"
type: entity
entity-type: framework
status: active
date: {today}
related:
  - salesforce-b2b-commerce
---

## Overview

Lightning Web Components (LWC) is Salesforce's modern UI framework for building performant web components on the Salesforce platform. LWC is the standard frontend technology for B2B Commerce storefronts.

## Key Concepts

- Web Standards-based component model
- Reactive data binding
- Wire service for Apex and Lightning Data Service
- CSS isolation per component
- LWR (Lightning Web Runtime) for headless/SSR deployment

## Migration Relevance

When migrating from custom platforms (MerchTank, Shopify Plus, etc.) to Salesforce B2B Commerce, the storefront layer is rebuilt in LWC. Component mapping from source platform UI to LWC components is a key migration workstream.
```

### Step 7: Create Verndale Process Stubs

#### 7a. `verndale/processes/wiki-maintenance.md`

```markdown
---
title: "Wiki Maintenance Procedures"
type: process
status: active
date: {today}
related: []
---

## Overview

Standard operating procedures for maintaining wiki health, consistency, and completeness.

## Scheduled Maintenance

A weekly maintenance task runs every Monday at 9am:

1. **Lint** — Full wiki health check (broken links, orphans, contradictions, stale pages)
2. **Reconcile** — Bidirectional sync with Confluence (if configured)
3. **Index Rebuild** — Regenerate `_index.md` with current page inventory

## On-Demand Operations

| Command | Purpose |
|---------|---------|
| `/wiki:lint` | Run health check |
| `/wiki:query` | Search and synthesize knowledge |
| `/wiki:ingest-meeting` | Add meeting analysis to wiki |
| `/wiki:ingest-document` | Add email/spec/PDF to wiki |
| `/wiki:new-client` | Scaffold new client workspace |
| `/wiki:status` | View wiki statistics |

## Quality Gates

- No broken `[[wiki-links]]`
- All pages have valid YAML frontmatter
- No orphan pages (unreachable from `_index.md`)
- No stale pages (>30 days without update and status=stub)
- Cross-reference consistency (if A links to B, B should link to A)
```

#### 7b. `verndale/processes/migration-analysis-pipeline.md`

```markdown
---
title: "Migration Analysis Pipeline"
type: process
status: active
date: {today}
related: []
---

## Overview

The 6-phase migration analysis pipeline converts raw meeting recordings, transcripts, and documents into structured analysis outputs. These outputs are then ingested into the wiki by the wiki ingest skills.

## Pipeline Phases

1. **Transcription** — Video/audio → text transcript
2. **Feature Extraction** — Identify business capabilities discussed
3. **SFCC Assessment** — Map features to Salesforce B2B Commerce capabilities
4. **Gap Analysis** — Identify gaps between source and target platforms
5. **Integration Mapping** — Document data flows and system connections
6. **Synthesis** — Compile findings into structured reports

## Pipeline → Wiki Flow

```
Recording → Pipeline (6 phases) → Raw Outputs (immutable)
                                        ↓
                                  Wiki Ingest Skill
                                        ↓
                                  Wiki Pages (evolving)
```

The pipeline produces raw analysis. The wiki synthesizes, cross-references, and maintains that analysis as living knowledge.
```

### Step 8: Scaffold First Client (If Requested)

If `first-client` and `platform-source` were provided:

1. Invoke the `wiki-scaffold-client` skill with:
   - `company`: value of `first-client`
   - `platform-source`: value of `platform-source`
   - `platform-target`: value of `platform-target` (or default)
2. Wait for completion
3. Include the client scaffold results in the final summary

### Step 9: Log and Report

#### 9a. Update `_log.md`

If a first client was scaffolded, add a second log entry:
```
| {today} | scaffold-client | {client-slug} | First client workspace created with {N} pages | Part of wiki-init |
```

#### 9b. Output Final Summary

```
================================================================
  Wiki Initialized Successfully
================================================================

Vault:          {WIKI_DIR}
Obsidian:       .obsidian/ (5 config files)
Schema:         _schema/SCHEMA.md + 7 templates
Global files:   _index.md, _log.md
Platform stubs: salesforce-b2b-commerce, salesforce-lwc
Process stubs:  wiki-maintenance, migration-analysis-pipeline

{If first client scaffolded:}
First Client:   {first-client} ({client-slug})
  Platform:     {platform-source} → {platform-target}
  Pages:        {N} initial pages

Total files created: {count}

Next Steps:
  1. Open the vault in Obsidian: open {WIKI_DIR} as vault
  2. Add your first client:
     /wiki:new-client '<company>' '<platform-source>'
  3. Ingest a meeting:
     /wiki:ingest-meeting '<company>' '<meeting-dir>' '<label>'
  4. Check wiki health:
     /wiki:lint --scope full

Wiki is ready for knowledge accumulation.
================================================================
```

## Key Behaviors

- **Always check for existing vault** — never overwrite an existing wiki
- **Create ALL Obsidian config files** — the vault should open cleanly in Obsidian
- **Write the complete SCHEMA.md** — this is the constitution of the wiki, not a stub
- **Use individual mkdir calls** — brace expansion is unreliable across shells
- **Create real content** in platform and process stubs — not just placeholders
- **Log every operation** in `_log.md` for audit trail
- **Provide actionable next steps** with example commands

## Edge Cases

- **Wiki already exists**: Stop with clear message, do not modify existing vault
- **Custom wiki-dir path**: Ensure parent directory exists, create if needed
- **First-client without platform-source**: Error with usage hint
- **Non-standard project structure**: Adapt paths but maintain the same vault internal structure
- **Permissions errors**: Report clearly, suggest checking directory permissions
