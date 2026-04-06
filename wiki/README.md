# Verndale Agentics — Karpathy Obsidian RAG Wiki

> **21 Skills | 9 Commands | 4 Agents | 67 Wiki Pages | 1 Scheduled Task**
> Multi-client architecture for continuous knowledge compilation

A continuously maintained, LLM-powered knowledge base built on [Andrej Karpathy's LLM Wiki pattern](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f). It compounds knowledge over time by ingesting meeting recordings, emails, documents, and Confluence exports into a cross-referenced Obsidian vault — then keeps it healthy with automated lint, reconciliation, and maintenance.

---

## Table of Contents

1. [System Architecture](#1-system-architecture)
2. [Wiki Content Structure](#2-wiki-content-structure)
3. [Page Types & Frontmatter](#3-page-types--frontmatter)
4. [Skills Reference (21 Total)](#4-skills-reference-21-total)
5. [Commands Reference (9 Total)](#5-commands-reference-9-total)
6. [Agents Reference (4 Total)](#6-agents-reference-4-total)
7. [Scheduled Tasks](#7-scheduled-tasks)
8. [Day-to-Day Workflows](#8-day-to-day-workflows)
9. [Boston Beer Company Wiki Status](#9-boston-beer-company-wiki-status)
10. [Lint & Health Monitoring](#10-lint--health-monitoring)
11. [Adding a New Client](#11-adding-a-new-client)
12. [File Inventory](#12-file-inventory)

---

## 1. System Architecture

The system implements Karpathy's three-layer LLM Wiki pattern, adapted for enterprise Salesforce B2B Commerce migration consulting.

### Three-Layer Model

```
┌─────────────────────────────────────────────────────────┐
│ LAYER 1 — RAW SOURCES (Immutable)                       │
│ ├─ BostonBeerCompany/meetings/                          │
│ │  ├─ transcripts (video → text)                        │
│ │  ├─ frames (video frame analysis)                     │
│ │  └─ analysis/ (pipeline outputs: SFCC, gaps, etc.)    │
│ └─ Emails, Confluence exports, architecture docs        │
├─────────────────────────────────────────────────────────┤
│ LAYER 2 — THE WIKI (Evolving, LLM-Maintained)           │
│ ├─ wiki/clients/{client-slug}/                          │
│ │  ├─ entities/, features/, gaps/, decisions/            │
│ │  ├─ meetings/, integrations/, questions/               │
│ ├─ wiki/platforms/{platform-slug}/                      │
│ ├─ wiki/verndale/ (methodology, playbooks)              │
│ └─ wiki/_schema/ (this schema, templates, lint rules)   │
├─────────────────────────────────────────────────────────┤
│ LAYER 3 — THE SCHEMA                                     │
│ ├─ wiki/_schema/SCHEMA.md (conventions + workflows)     │
│ ├─ wiki/_index.md (auto-maintained content catalog)     │
│ └─ wiki/_log.md (chronological activity record)         │
└─────────────────────────────────────────────────────────┘
```

The wiki sits alongside (not replaces) the existing migration analysis pipeline. The pipeline produces raw analysis artifacts. The wiki consumes them as sources and maintains compiled, cross-referenced knowledge that compounds with every new client interaction.

### Design Principles

- **Immutability of Sources** — Raw pipeline outputs and transcripts are never modified. The wiki references them.
- **Machine-Readable Structure** — YAML frontmatter, `[[wiki-links]]`, and type conventions enable both human and LLM parsing.
- **Traceability** — Every wiki page links back to source documents and forward to derived decisions.
- **Compounding Knowledge** — Each new meeting, email, or document updates existing pages rather than creating isolated artifacts.
- **Multi-Client Architecture** — Client knowledge is siloed under `wiki/clients/{slug}/` but shares platform knowledge.

---

## 2. Wiki Content Structure

The Obsidian vault lives at `Vendale-Agentics/wiki/` and follows this directory convention:

| Path | Purpose |
|------|---------|
| `wiki/_schema/` | Schema definition, page templates (7), lint rules |
| `wiki/_index.md` | Auto-maintained content catalog with page counts and statistics |
| `wiki/_log.md` | Chronological record of all ingest, query, and lint operations |
| `wiki/clients/{slug}/features/` | Business capabilities: catalog, ordering, budget, fulfillment, etc. |
| `wiki/clients/{slug}/gaps/` | Current vs. target state gaps with severity and resolution path |
| `wiki/clients/{slug}/meetings/` | Meeting summaries linking to features, gaps, and questions |
| `wiki/clients/{slug}/decisions/` | Design and scope decisions with status tracking |
| `wiki/clients/{slug}/questions/` | Open questions needing stakeholder input, prioritized P1/P2/P3 |
| `wiki/clients/{slug}/entities/` | Systems, vendors, organizations (MerchTank, Oracle ERP, etc.) |
| `wiki/clients/{slug}/integrations/` | External system data flows and API connections |
| `wiki/platforms/{slug}/` | Shared platform knowledge reusable across clients |
| `wiki/verndale/processes/` | Internal methodology (pipeline architecture, wiki maintenance) |

The `wiki/clients/_template/` directory provides an empty scaffold that the `wiki-scaffold-client` skill clones for new engagements.

---

## 3. Page Types & Frontmatter

Every wiki page has YAML frontmatter that makes it machine-readable. Seven page types are defined, each with a template in `wiki/_schema/templates/`.

### Required YAML Fields (All Pages)

```yaml
---
type: feature | entity | decision | meeting | gap | integration | question
client: boston-beer-company   # or "shared" for platform pages
status: active | resolved | deprecated | blocked
created: YYYY-MM-DD
updated: YYYY-MM-DD
sources: []                   # paths to raw source documents
tags: []                      # lowercase, category-prefixed
---
```

### Page Type Reference

| Type | Purpose | Key Extra Fields | Links To |
|------|---------|------------------|----------|
| **Feature** | Business capability or function | `decision`, `effort` (S/M/L/XL), `priority` (P1/P2/P3), `category` | Gaps, Meetings, Decisions, Integrations |
| **Gap** | Current vs. target state deficit | `severity` (critical/high/medium/low), `resolution-approach` | Features, Meetings, Questions |
| **Meeting** | Client interaction summary | `meeting-date`, `attendees`, `recording-path`, `transcript-path` | Features, Gaps, Decisions, Questions |
| **Decision** | Design/scope decision with rationale | `decision-status`, `decided-date`, `decided-by` | Features, Gaps, Questions |
| **Question** | Open item needing stakeholder input | `priority` (P1/P2/P3), `category`, `owner` | Features, Gaps, Decisions |
| **Entity** | System, vendor, person, or org | `category` (system/vendor/person/organization) | Features, Integrations, Gaps |
| **Integration** | External system data flow | `direction`, `frequency`, `auth-method` | Entities, Features, Gaps |

### Decision Status Color System

Carried forward from the existing Confluence gap analysis format:

| Badge | Status | Meaning |
|-------|--------|---------|
| 🟢 | OOTB / Configuration | Standard platform capability, no code required |
| 🔵 | Configuration | Requires admin configuration, not development |
| 🟡 | Custom Dev | Requires custom Lightning/Apex development |
| 🔴 | Gap / New Build | No platform equivalent — net-new development |
| ⚪ | TBD | Awaiting client input or further analysis |
| 🟣 | 3rd Party | AppExchange or external solution recommended |

---

## 4. Skills Reference (21 Total)

Skills are specialized instruction sets that LLM agents follow autonomously. Each is a `SKILL.md` file in `.claude/skills/{name}/`.

### Wiki Skills (6)

These power the wiki's continuous maintenance cycle:

| Skill | Purpose | Arguments |
|-------|---------|-----------|
| **`wiki-ingest-meeting`** | Ingests a complete meeting pipeline output into the wiki. Creates/updates feature, gap, and question pages. Builds meeting summary. Handles contradictions with existing content. | `company`, `meeting-dir`, `meeting-label` |
| **`wiki-ingest-document`** | Lightweight ingest for emails, PDFs, specs, Slack messages. Surgically updates affected wiki pages without full pipeline run. | `company`, `document-path`, `document-type`, `summary` |
| **`wiki-confluence-reconcile`** | Bidirectional sync between wiki and Confluence exports. Detects drift, flags contradictions, optionally pushes/pulls updates. | `company`, `confluence-dir`, `direction` |
| **`wiki-lint`** | Health checks across 7 dimensions: broken links, orphans, contradictions, stale pages, missing cross-refs, invalid frontmatter, decision drift. | `scope`, `fix` |
| **`wiki-query`** | Searches wiki to answer natural language questions. Synthesizes from compiled knowledge. Optionally promotes good answers to new pages. | `question`, `client`, `promote` |
| **`wiki-scaffold-client`** | Creates a new client workspace from template. Directory structure, initial entity pages, optional initial context extraction. | `company`, `platform-source`, `platform-target`, `initial-context` |

### Migration Pipeline Skills (15)

These power the Salesforce B2B Commerce migration analysis pipeline:

**Preprocessing (Phase 0)**

| Skill | Purpose |
|-------|---------|
| **`extract-video-frames`** | Extracts PNG frames and AAC audio segments from video files using ffmpeg. Produces `manifest.json`. |
| **`dedupe-frames`** | Removes near-duplicate frames via perceptual hashing (dhash). Typically 50–80% reduction. |
| **`elevenlabs-transcribe`** | Transcribes audio via ElevenLabs Scribe v2 API with speaker diarization and domain key-term biasing. |

**Analysis (Phase 1–2)**

| Skill | Purpose |
|-------|---------|
| **`frame-analyst`** | Parallel visual analysis of video frames. Catalogs UI components, form fields, navigation, text. Runs as 5 parallel instances. |
| **`frame-synthesis`** | Merges 5 parallel frame analysis outputs into Screen Catalog, Component Library, and System Architecture Map. |
| **`transcript-analyst`** | Extracts features, business rules, pain points from raw transcripts. Works without video. |
| **`meeting-analyst`** | Combines transcript + frames + synthesis outputs into Feature Inventory. |
| **`sfcc-b2b-expert`** | Maps features to Salesforce B2B Commerce capabilities. Assesses config vs. custom needs. |
| **`ui-migration`** | Maps UI components to Experience Cloud / LWC equivalents. |
| **`integration-api`** | Catalogs integration points and designs Salesforce integration architecture. |
| **`data-schema`** | Maps entities to Salesforce standard and custom objects. Outlines data migration strategy. |
| **`gap-analysis`** | Synthesizes all inputs into client-specific, workflow-organized gap analysis. |

**Validation & Export (Phase 2.5–3)**

| Skill | Purpose |
|-------|---------|
| **`sfcc-validator`** | Web-search validation of SFCC claims against live Salesforce docs, Trailhead, and AppExchange. |
| **`client-elicitor`** | Consolidates open questions from all sources. Maps to stakeholders. Produces meeting prep guide. |
| **`confluence-gap-analysis`** | Converts gap analysis to Confluence Storage Format (XHTML) and Wiki Markup. |

---

## 5. Commands Reference (9 Total)

Slash commands provide the quick-access interface for daily operations. Invoke from Claude Code.

### /wiki Namespace (6 Commands)

#### `/wiki:ingest-meeting`

```
/wiki:ingest-meeting '<company>' '<meeting-dir>' '<meeting-label>'
```

Full meeting ingest into the wiki after a pipeline run. Creates/updates feature, gap, question, and meeting pages. Updates index and log.

**Example:**
```
/wiki:ingest-meeting 'Boston Beer Company' 'BostonBeerCompany/meetings/04-fulfillment-demo' 'fulfillment-demo'
```

---

#### `/wiki:ingest-document`

```
/wiki:ingest-document '<company>' '<doc-path>' '<type>' [--summary '...']
```

Lightweight ingest of a single document (email, PDF, spec, Slack message). Surgically updates affected pages. Types: `email`, `pdf`, `spec`, `slack`, `other`.

**Example:**
```
/wiki:ingest-document 'Boston Beer Company' 'emails/scope-decision.eml' 'email' --summary 'Client confirmed budget enforcement is hard stop'
```

---

#### `/wiki:query`

```
/wiki:query '<question>' [--client <slug>] [--promote]
```

Ask the wiki a natural language question. Synthesizes answer from compiled knowledge with `[[wiki-link]]` citations. `--promote` creates a new page from the answer.

**Example:**
```
/wiki:query 'Which features are blocked by the Oracle ERP decision?' --client boston-beer-company
```

---

#### `/wiki:lint`

```
/wiki:lint [--scope full|client:<slug>|recent] [--fix]
```

Run health checks across all wiki pages. Reports broken links, orphans, contradictions, stale pages, decision drift. `--fix` auto-repairs safe issues.

**Example:**
```
/wiki:lint --scope client:boston-beer-company --fix
```

---

#### `/wiki:status`

```
/wiki:status [--client <slug>]
```

Dashboard showing page counts by type, recent operations from the log, and health score from the last lint run.

**Example:**
```
/wiki:status
/wiki:status --client boston-beer-company
```

---

#### `/wiki:new-client`

```
/wiki:new-client '<company>' '<platform-source>' [--target '...'] [--context '...']
```

Scaffold a new client workspace from template. Creates directory structure, initial entity pages, and prints next steps.

**Example:**
```
/wiki:new-client 'Burlington Medical' 'Magento' --context 'reference-docs/project/BurMed_SF_B2B_Technical_Plan.md'
```

---

### /verndale Namespace (3 Commands)

Existing pipeline commands that produce the raw analysis artifacts the wiki consumes:

| Command | Purpose |
|---------|---------|
| **`/verndale:migration-pipeline`** | Full end-to-end pipeline: raw video → frames → transcript → analysis → gap analysis → Confluence export. Options A–H for different input scenarios. |
| **`/verndale:meeting-review`** | Analyze a gap analysis review meeting against the source document. Extracts agreements, changes, revisions needed, and verbal context. |
| **`/verndale:enrich-batch`** | Enrich an existing gap analysis batch with additional meeting data or context. |

---

## 6. Agents Reference (4 Total)

Agents are multi-step orchestrators that coordinate skills and commands into complex workflows. Located in `.claude/agents/`.

### wiki-pipeline

Orchestrator for complex multi-step wiki operations. Three workflows:

**Full Meeting Ingest** — After a migration pipeline run:
1. Ingest meeting → 2. Confluence reconcile → 3. Lint new content → 4. Report

```
wiki-pipeline 'full-meeting-ingest' '<company>' '<meeting-dir>' '<meeting-label>'
```

**Bulk Bootstrap** — New client with multiple existing meetings:
1. Scaffold client → 2. Ingest all meetings chronologically → 3. Lint → 4. Generate index

```
wiki-pipeline 'bulk-bootstrap' '<company>' '<meetings-base-dir>'
```

**Maintenance Cycle** — Weekly maintenance:
1. Full lint → 2. Reconcile all clients → 3. Rebuild index → 4. Report trends

```
wiki-pipeline 'maintenance-cycle'
```

### migration-pipeline

Full Salesforce B2B Commerce migration analysis pipeline (6 phases):

- **Phase 0:** Video extraction + transcription
- **Phase 1:** 5x parallel frame analysis + meeting analysis
- **Phase 2:** SFCC assessment + UI migration + data schema + integration
- **Phase 3:** Gap analysis synthesis
- **Phase 4:** SFCC validation (web search fact-checking)
- **Phase 5:** Client deliverables + Confluence export
- **Phase 6:** Summary with statistics

### video-analysis-pipeline

Specialized pipeline for meeting video → transcripts → frame analysis.

### documentation-pipeline

Orchestrates parallel URL documentation gathering for frontend page audits.

---

## 7. Scheduled Tasks

### wiki-weekly-maintenance

| Property | Value |
|----------|-------|
| **Schedule** | Every Monday at 9:00 AM (local time) |
| **Location** | Scheduled section in Claude sidebar |

**What it does:**

1. Runs `wiki-lint` with `scope=full` across all wiki pages
2. Runs `wiki-confluence-reconcile` for all clients
3. Rebuilds `wiki/_index.md` with current page counts
4. Appends maintenance summary to `wiki/_log.md`
5. Reports health score and action items

**Output:** `wiki/_lint-report-{date}.md` + log entry + notification

> **Tip:** Run the task manually once from the sidebar to pre-approve tool permissions, so future automated Monday runs don't pause waiting for approval.

---

## 8. Day-to-Day Workflows

### New Meeting Recording Arrives

1. **Run the migration pipeline** to produce raw analysis:
   ```
   /verndale:migration-pipeline 'meeting-dir' 'Company' 'label'
   ```
2. **Ingest pipeline outputs** into the wiki:
   ```
   /wiki:ingest-meeting 'Company' 'meeting-dir' 'label'
   ```
3. **Check for issues:** `/wiki:lint --scope recent`
4. **Review status:** `/wiki:status`

### Client Email with a Decision

1. Save the email to the project folder
2. Ingest it:
   ```
   /wiki:ingest-document 'Company' 'path/to/email' 'email' --summary 'decision summary'
   ```
3. The skill identifies affected pages, updates features/gaps, and creates Decision pages if needed.

### Preparing for a Client Call

1. **Query open questions:**
   ```
   /wiki:query 'What are all P1 open questions for BBC?'
   ```
2. **Check for contradictions:**
   ```
   /wiki:query 'What contradictions exist in BBC features?'
   ```
3. **Review unprocessed meetings:** `/wiki:status --client boston-beer-company`

### Weekly Maintenance (Automated)

Every Monday at 9 AM, the `wiki-weekly-maintenance` task automatically runs lint, Confluence reconciliation, and index rebuild. You receive a notification with the health report.

If critical issues are found:
- `/wiki:lint --fix` to auto-repair safe issues (broken links, missing frontmatter)
- Manual review for contradictions and decision drift
- `/wiki:reconcile` to sync Confluence if drift is detected

### New Client Engagement

1. **Scaffold:** `/wiki:new-client 'Company Name' 'Source Platform'`
2. **Run migration pipeline** on the first meeting recording
3. **Ingest into wiki:** `/wiki:ingest-meeting ...`
4. **Add supporting documents:** `/wiki:ingest-document ...` (emails, specs, RFPs)
5. **Run lint:** `/wiki:lint --scope client:{slug}`
6. **Repeat** steps 2–5 for each subsequent meeting

---

## 9. Boston Beer Company Wiki Status

Current state of the bootstrapped wiki content for the BBC MerchTank → Salesforce B2B Commerce migration:

| Category | Count | Details |
|----------|-------|---------|
| **Features** | 19 | 18 custom, 1 config. Budget, VW, fulfillment, ordering, catalog, account, creative requests. |
| **Gaps** | 10 | 4 critical, 5 high, 1 medium. Budget engine, VW model, custom POS, co-op billing. |
| **Meetings** | 5 | 3 fully processed (02, 03, 04), 1 partial (01), 1 unprocessed (05). |
| **Questions** | 5 | 4 P1, 1 P2. Budget enforcement, upstream system, Oracle ERP, VW usage, OMS licensing. |
| **Entities** | 4 | Boston Beer Company, MerchTank, Oracle ERP, TradeWearables. |
| **Integrations** | 4 | Oracle ERP, vendor fulfillment, TradeWearables API, SSO/dual-auth. |
| **Platforms** | 3 | Salesforce B2B Commerce, Salesforce LWC, MerchTank. |
| **Verndale** | 2 | Migration pipeline process, wiki maintenance playbook. |

### Known Gaps in Coverage

- 🔴 **Meeting 05 (Finance Workflow)** is unprocessed — raw MP4 only. Blocks financial constraint discovery.
- 🟡 **Meeting 01 (MerchTank Overview)** has only partial analysis. Early frame analysis exists but no full pipeline run.
- 🟡 **Decision pages** not yet created as standalone pages — decisions are embedded in feature and gap pages.
- 🟡 **Question coverage** limited to P1/P2 blocking items. P3 questions not yet extracted.
- 🔵 **Wiki-link naming mismatch:** ~434 broken links from meeting pages referencing features by friendly names vs. actual file slugs.

---

## 10. Lint & Health Monitoring

The `wiki-lint` skill checks 7 health dimensions:

| Check | What It Detects | Severity |
|-------|-----------------|----------|
| **Broken Links** | `[[wiki-links]]` that point to non-existent pages | Critical |
| **Orphan Pages** | Pages with zero incoming links from other pages | Medium |
| **Contradictions** | Same feature/gap assessed differently across pages | High |
| **Stale Pages** | Pages not updated since newer sources were ingested | Low |
| **Missing Cross-Refs** | Features without gaps, gaps without meetings, etc. | Medium |
| **Invalid Frontmatter** | Missing required YAML fields (type, client, status, etc.) | Medium |
| **Decision Drift** | Assessment changed between meetings without reconciliation | High |

**Health score target: >90%.** Calculated as `(total pages - total issues) / total pages`. Lint reports are saved to `wiki/_lint-report-{date}.md` and referenced in `wiki/_log.md`.

---

## 11. Adding a New Client

The multi-client architecture supports onboarding new engagements without affecting existing client data.

### Step-by-Step

1. **Scaffold:** `/wiki:new-client 'Company Name' 'Source Platform'`
   - Creates `wiki/clients/{company-slug}/` with all 7 subdirectories
   - Creates initial entity pages for the client and source platform
   - Updates `wiki/_index.md` with new client section

2. **Run first meeting pipeline:** `/verndale:migration-pipeline ...`
   - Produces gap analysis, feature inventory, SFCC assessment, etc.

3. **Ingest into wiki:** `/wiki:ingest-meeting ...`
   - Creates feature, gap, question, and meeting pages from pipeline output

4. **Add supporting documents:** `/wiki:ingest-document ...`
   - Emails, specs, RFPs, existing gap analysis PDFs

5. **Run lint:** `/wiki:lint --scope client:{slug}`
   - Checks initial content health

6. **Repeat** steps 2–5 for each subsequent meeting

Platform knowledge pages (`wiki/platforms/`) are shared across all clients. If the new client uses Salesforce B2B Commerce, the existing platform pages apply automatically. If they use a different target platform, create new platform pages.

---

## 12. File Inventory

### Wiki Content

| Location | Files | Lines |
|----------|-------|-------|
| `wiki/` (total) | 67 | ~16,400 |
| `wiki/clients/boston-beer-company/features/` | 19 + 1 index | |
| `wiki/clients/boston-beer-company/gaps/` | 10 + 1 index | |
| `wiki/clients/boston-beer-company/meetings/` | 5 | |
| `wiki/clients/boston-beer-company/questions/` | 5 | |
| `wiki/clients/boston-beer-company/entities/` | 4 | |
| `wiki/clients/boston-beer-company/integrations/` | 4 | |
| `wiki/platforms/` | 3 | |
| `wiki/verndale/processes/` | 2 | |
| `wiki/_schema/` | 1 + 7 templates | |

### Skills

| Category | Count | Total Lines |
|----------|-------|-------------|
| Wiki skills (`.claude/skills/wiki-*`) | 6 | ~2,650 |
| Migration pipeline skills | 15 | |
| **Total skills** | **21** | |

### Commands & Agents

| Category | Count | Location |
|----------|-------|----------|
| `/wiki:` commands | 6 | `.claude/commands/wiki/` |
| `/verndale:` commands | 3 | `.claude/commands/verndale/` |
| Agents | 4 | `.claude/agents/` |
| Scheduled tasks | 1 | Mondays 9am |

---

## Quick Start

1. **Open** `Vendale-Agentics/wiki/` as an Obsidian vault to browse the knowledge graph
2. **Run** `/wiki:status` for a health dashboard
3. **Run** `/wiki:query 'your question'` to search compiled knowledge
4. **After any pipeline run**, follow up with `/wiki:ingest-meeting` to keep the wiki current
