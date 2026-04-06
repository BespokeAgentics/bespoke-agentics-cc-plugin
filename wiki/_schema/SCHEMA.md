# Verndale Wiki Schema

## 1. Purpose

This wiki is a **continuously maintained knowledge base** that compounds over time. It is the single source of truth for client-specific intelligence, technical decisions, and business capabilities across all Verndale Salesforce B2B Commerce migration engagements.

Unlike raw analysis pipeline outputs (stored immutably in `BostonBeerCompany/meetings/` and similar client folders), the wiki **synthesizes, cross-references, and maintains knowledge as a living system**. It evolves with each client interaction, meeting, and discovery phase. The wiki serves both human consultants and LLMs running queries or ingest workflows.

### What the Wiki Is Not

- Not a replacement for the analysis pipeline
- Not a raw transcript repository (sources stay in `BostonBeerCompany/`)
- Not write-once documentation
- Not a status dashboard

### What the Wiki Is

- A Karpathy-style LLM-friendly knowledge base with machine-readable structure
- A cross-referenced, interconnected entity-relationship system
- A gap-to-decision-to-question traceability matrix
- A living artifact that evolves with each client engagement
- A reusable foundation for platform knowledge (templates, patterns, decision trees)

---

## 2. Architecture

### Three-Layer Model

```
┌─────────────────────────────────────────────────────────┐
│ RAW SOURCES (Immutable)                                  │
│ ├─ BostonBeerCompany/meetings/                          │
│ │  ├─ transcripts/ (video→text)                         │
│ │  ├─ frames/ (video frame analysis)                    │
│ │  └─ analysis/ (pipeline outputs: SFCC assess, gaps)  │
│ └─ Emails, Confluence exports, architecture docs        │
├─────────────────────────────────────────────────────────┤
│ THE WIKI (Evolving, LLM-Maintained)                     │
│ ├─ wiki/clients/{client-slug}/                          │
│ │  ├─ entities/, features/, gaps/, decisions/           │
│ │  ├─ meetings/, integrations/, questions/              │
│ ├─ wiki/platforms/{platform-slug}/                      │
│ │  ├─ Decision trees, reusable patterns, templates      │
│ ├─ wiki/verndale/                                       │
│ │  ├─ Capabilities, methodologies, playbooks            │
│ └─ wiki/_schema/ (this file, templates, lint rules)    │
├─────────────────────────────────────────────────────────┤
│ THE SCHEMA (This File)                                   │
│ ├─ Conventions, workflow definitions, templates         │
│ ├─ _index.md (auto-maintained content catalog)         │
│ └─ _log.md (chronological record of all activity)      │
└─────────────────────────────────────────────────────────┘
```

### Design Principles

1. **Immutability of Sources** — Raw pipeline outputs and transcripts are never modified. The wiki *references* them, never edits them.
2. **Machine-Readable Structure** — Frontmatter (YAML), wiki-links (`[[]]`), and type conventions enable both human reading and LLM parsing.
3. **Traceability** — Every wiki page links back to source documents and forward to derived decisions.
4. **Compounding Knowledge** — Older pages inform newer pages. Contradictions surface as lint errors.
5. **Client-Centric Organization** — Each client's knowledge is siloed under `wiki/clients/{slug}/` but can reference shared platform knowledge.

---

## 3. Folder Structure Convention

```
wiki/
├─ _schema/                                    # Schema, templates, lint rules
│  ├─ SCHEMA.md                               # This file
│  ├─ TEMPLATES.md                            # Page templates (frontmatter + structure)
│  ├─ LINT_RULES.md                           # Health checks and contradiction detection
│  └─ LINT_LOG.md                             # Output from periodic lint runs
├─ _index.md                                   # Auto-maintained catalog of all pages
├─ _log.md                                     # Chronological ingest/query/lint activity log
├─ clients/
│  └─ boston-beer-company/                    # Client slug: lowercase-hyphenated
│     ├─ entities/                            # Systems, people, vendors (e.g., MerchTank.md)
│     ├─ features/                            # Business capabilities (e.g., budget-management.md)
│     ├─ gaps/                                # Identified gaps (e.g., dynamic-discount-gap.md)
│     ├─ decisions/                           # Design/scope decisions (e.g., som-licensing.md)
│     ├─ meetings/                            # Meeting summaries (e.g., 2024-03-15-discovery.md)
│     ├─ integrations/                        # External data flows (e.g., oracle-erp-sync.md)
│     ├─ questions/                           # Open questions (e.g., payment-tokenization.md)
│     └─ README.md                            # Client overview (auto-maintained)
├─ platforms/
│  └─ salesforce-b2b-commerce/                # Platform slug: lowercase-hyphenated
│     ├─ ootb-features/                       # OOTB capabilities by module
│     ├─ decision-trees/                      # "Is my use case in-platform?" decision flows
│     ├─ patterns/                            # Reusable patterns (e.g., budget-enforcement.md)
│     ├─ integrations/                        # AppExchange and 3rd-party solutions
│     └─ architecture/                        # Technical deep-dives
└─ verndale/
   ├─ capabilities/                           # Verndale service offerings
   ├─ methodologies/                          # Engagement playbooks, discovery frameworks
   ├─ case-studies/                           # De-identified case studies, lessons learned
   └─ templates/                              # Reusable proposal/SOW templates
```

### Key Rules

- **Client slugs**: `lowercase-hyphenated` (e.g., `boston-beer-company`)
- **Platform slugs**: `lowercase-hyphenated` (e.g., `salesforce-b2b-commerce`)
- **File names**: `kebab-case`, descriptive, no spaces (e.g., `budget-management.md`)
- **Never nest clients or platforms** — a client folder is never inside another
- **Shared platform pages** — If knowledge applies to all SFCC implementations, put it under `platforms/salesforce-b2b-commerce/`

---

## 4. Page Types & Templates

Every wiki page MUST have a **type** declared in frontmatter. This enables automated workflows (lint, cross-referencing, queries).

### 4.1 Entity

**Definition**: A system, person, organization, vendor, or application that exists in the client's environment.

**Examples**: MerchTank (legacy supplier system), Oracle ERP, TradeWearables (API partner), CFO (stakeholder), Salesforce Commerce Cloud

**Frontmatter**:
```yaml
---
type: entity
client: boston-beer-company
entity_type: system|person|vendor|organization  # Subcategory
status: active|deprecated|unknown
owner: Name/Role  # Who maintains this entity
created: YYYY-MM-DD
updated: YYYY-MM-DD
sources: [path/to/source/doc.md, BostonBeerCompany/meetings/2024-03-15-transcript.md]
tags: [legacy, external-api, critical]
---
```

**Structure**:
```markdown
# {Entity Name}

## Overview
[1-2 sentence definition and context]

## Current State
- Role in existing architecture
- Key capabilities or limitations
- Integration points with Verndale engagement

## Relationship to Salesforce B2B Commerce
- Does it integrate with SFCC?
- Is it being replaced, retained, or evolving?
- Relevant gaps or decisions

## Key Contacts
- [Name] — [Role] — [contact info if known]

## Links
- [[Feature or Gap that depends on this entity]]
- [[Integration that connects to this entity]]
```

---

### 4.2 Feature

**Definition**: A specific business capability or technical function (may be OOTB, custom, or a gap).

**Examples**: Budget Management, Co-op Billing, Virtual Warehouse Inventory, Purchase Order Routing, Variant Search

**Frontmatter**:
```yaml
---
type: feature
client: boston-beer-company
status: active|deprecated|in-discovery
current_platform: legacy-system|salesforce-b2b-commerce|hybrid|tbd
priority: p0|p1|p2|p3  # P0 = blockers for go-live
created: YYYY-MM-DD
updated: YYYY-MM-DD
sources: [BostonBeerCompany/analysis/sfcc-assessment.md, BostonBeerCompany/meetings/2024-03-15-transcript.md]
tags: [b2b-specific, custom-dev-required, strategic]
discovered_by_meeting: [[2024-03-15-discovery]]
---
```

**Structure**:
```markdown
# {Feature Name}

## Definition
[What is this feature? What business problem does it solve?]

## Current Behavior (Legacy System)
- Key workflows
- User roles involved
- Integration points
- Any known limitations or pain points

## Target Behavior (Salesforce B2B Commerce)
- How should this work in SFCC?
- If gaps exist, see [[{feature}-gap]]
- If decisions are pending, see [[{feature}-decision]]

## Assessment
- **OOTB Status**: ✓ (fully supported) | ⚠️ (partial) | ✗ (not supported)
- **Estimated Effort**: days/weeks/months
- **Risks or Dependencies**: [list]
- **References**: [[Decision on {feature}]], [[Integration needed for {feature}]]

## Meeting History
- [[2024-03-15-discovery]] — First mentioned, core capability
- [[2024-04-10-deep-dive]] — Detailed requirements gathered
- [[2024-05-01-design-review]] — Design approved with custom development

## Next Steps
- [ ] Finalize detailed requirements with Product team
- [ ] Create design spec
- [ ] Estimate custom development effort
```

---

### 4.3 Decision

**Definition**: A design choice, scope decision, or architectural commitment with tracked status. Maps to color system for in-platform vs. custom vs. gap.

**Examples**: "License Salesforce Order Management?", "Build co-op billing calculator in Apex or use Vlocity?", "Sync inventory real-time or nightly batch?"

**Frontmatter**:
```yaml
---
type: decision
client: boston-beer-company
status: pending|approved|implemented|rejected|under-review
decision_category: architecture|scope|vendor|technical
color: 🟢|🔵|🟡|🔴|⚪|🟣  # See color code table below
owner: Stakeholder Name
due_date: YYYY-MM-DD  # When decision needed
approved_by: Name, Name  # Who signed off
created: YYYY-MM-DD
updated: YYYY-MM-DD
sources: [meeting/transcript, email, Confluence doc]
tags: [licensing, custom-dev, critical-path]
question: [[Does SFCC support co-op billing?]]
related_features: [[Budget Management]], [[Co-op Billing]]
related_gaps: [[Co-op Billing Gap]]
---
```

**Color Code System**:

| Color | Meaning | Description |
|-------|---------|-------------|
| 🟢 | OOTB | Standard platform feature, no custom work needed |
| 🔵 | Config | Salesforce configuration (no code changes) |
| 🟡 | Custom Dev | Requires Apex, Lightning, or JavaScript development |
| 🔴 | Gap / New Build | No in-platform equivalent, net-new development required |
| ⚪ | TBD | Awaiting client input or further analysis |
| 🟣 | 3rd Party | AppExchange app or external vendor solution |

**Structure**:
```markdown
# {Decision Name}

## Question
What problem or choice drove this decision?
- See [[Question]]

## Options Considered
1. **Option A** — Description, pros, cons, effort estimate
2. **Option B** — Description, pros, cons, effort estimate
3. **Option C** — Description, pros, cons, effort estimate

## Decision
**Status**: [pending | approved | implemented | rejected]
**Color**: [🟢🔵🟡🔴⚪🟣]
**Owner**: [Name]
**Approved**: [Date or "Pending approval"]

[1-2 sentence justification]

## Rationale
- Business driver
- Technical rationale
- Risk mitigation
- Stakeholder alignment

## Implementation
- Effort estimate
- Timeline
- Dependencies
- Success criteria

## Related
- **Question**: [[Does SFCC support co-op billing?]]
- **Features**: [[Co-op Billing]], [[Budget Management]]
- **Gaps**: [[Co-op Billing Gap]]
- **Meetings**: [[2024-03-15-discovery]], [[2024-04-10-deep-dive]]

## Review History
- *2024-03-20*: Proposed in discovery meeting
- *2024-04-01*: Drafted spec with Product team
- *2024-04-15*: Reviewed with stakeholders
- *2024-04-25*: Approved (CEO, CFO sign-off)
```

---

### 4.4 Meeting

**Definition**: A summary of a client interaction (kickoff, discovery, design, status, demo, decision gate).

**Frontmatter**:
```yaml
---
type: meeting
client: boston-beer-company
meeting_date: YYYY-MM-DD
meeting_type: discovery|design|status|demo|decision-gate|retrospective
attendees: [Name (Title), Name (Title)]
duration_minutes: 60
created: YYYY-MM-DD
updated: YYYY-MM-DD
sources: [BostonBeerCompany/meetings/transcripts/2024-03-15.md, BostonBeerCompany/meetings/frames/frame-analysis-2024-03-15.json]
tags: [discovery, stakeholder-alignment, critical-blocker]
---
```

**Structure**:
```markdown
# {Date} — {Meeting Type/Topic}

## Context
- Meeting type: [discovery | design | status | etc.]
- Attendees: [Names and roles]
- Duration: [minutes]
- Raw transcript: [link to source]

## Key Takeaways
1. [Major insight or decision]
2. [Major insight or decision]
3. [Major insight or decision]

## Features Discovered / Discussed
- [[Feature Name]] — [context: new, refined, blocked]
- [[Feature Name]] — [context: new, refined, blocked]

## Gaps Identified
- [[Gap Name]] — [description, severity]
- [[Gap Name]] — [description, severity]

## Decisions Made / Pending
- [[Decision Name]] — **Status**: [approved | pending | rejected]
- [[Decision Name]] — **Status**: [approved | pending | rejected]

## Open Questions
- [[Question Name]] — Owner: [Name], Due: [YYYY-MM-DD]
- [[Question Name]] — Owner: [Name], Due: [YYYY-MM-DD]

## Action Items
- [ ] Owner: [action] — Due [date]
- [ ] Owner: [action] — Due [date]

## Raw Evidence
- [Quote from transcript, frame numbers, or artifact references]
- "Customers are asking for dynamic pricing, but our legacy system can't handle it real-time"

## Next Steps
- [Follow-up meeting type and timing]
- [Data to gather before next meeting]
```

---

### 4.5 Gap

**Definition**: A specific difference between the current (legacy) platform and the target (SFCC) platform, with evidence and proposed resolution.

**Frontmatter**:
```yaml
---
type: gap
client: boston-beer-company
gap_category: functional|technical|performance|compliance|ux
severity: critical|high|medium|low  # Impact on go-live
status: open|under-review|resolved|workaround
feature: [[Feature Name]]  # The feature that has this gap
meeting: [[Meeting Date]]  # Where it was first discovered
created: YYYY-MM-DD
updated: YYYY-MM-DD
sources: [BostonBeerCompany/analysis/gap-analysis.md, BostonBeerCompany/meetings/2024-03-15-transcript.md]
tags: [custom-dev, budget-enforcement, high-priority]
decision: [[Decision on Gap Resolution]]  # Optional, if resolved
---
```

**Structure**:
```markdown
# {Gap Name}

## Definition
What is missing or different in SFCC compared to legacy?

## Current State (Legacy)
[How does the legacy system handle this?]
- Workflow
- User experience
- Limitations or pain points

## Target State (SFCC)
[What is the desired behavior in SFCC?]
- Expected workflow
- Expected user experience
- Why it matters

## Evidence
- Discovered in: [[2024-03-15-discovery]] (quote: "...")
- Confirmed in: [[2024-04-10-deep-dive]] (additional context)
- Stakeholder impact: [CFO, Supply Chain team, etc.]

## Assessment

**Severity**: [critical | high | medium | low]
**Likelihood**: [will definitely impact go-live | may impact | edge case]
**Estimated Effort**: [days | weeks | months of custom dev, config, or workaround]

## Resolution Options
1. **Use OOTB Salesforce Feature** — Conditions, limitations, gaps
2. **Implement Custom Solution** — Scope, technical approach, effort
3. **Use 3rd Party AppExchange** — Options, cost, limitations
4. **Process Workaround** — Manual steps, scalability concerns, long-term viability
5. **Accept Gap** — Business justification, risk management

## Recommended Resolution
**Approach**: [one of the above]
**Owner**: [Stakeholder or team]
**Timeline**: [by YYYY-MM-DD or milestone]
**Next Step**: See [[Decision on Gap Resolution]]

## Related
- **Feature**: [[Feature Name]]
- **Decision**: [[Decision on Gap Resolution]]
- **Meetings**: [[2024-03-15-discovery]], [[2024-04-10-deep-dive]]
- **Question**: [[Is SFCC sufficient for this use case?]]

## Notes
- [Any additional context, trade-offs, or strategic importance]
```

---

### 4.6 Integration

**Definition**: An external system, data flow, or API that connects to SFCC or the broader platform ecosystem.

**Examples**: Oracle ERP sync, TradeWearables API, Avalara tax service, Mindtree data warehouse

**Frontmatter**:
```yaml
---
type: integration
client: boston-beer-company
integration_type: erp|api|data-warehouse|payment|tax|external-system
status: active|planned|deprecated|tbd
direction: inbound|outbound|bidirectional
frequency: real-time|batch-daily|batch-weekly|on-demand
owner: [System/Team Name]
created: YYYY-MM-DD
updated: YYYY-MM-DD
sources: [BostonBeerCompany/meetings/2024-03-15-transcript.md, architecture-doc.pdf]
tags: [critical, batch-job, oracle-ecosystem]
related_entities: [[Oracle ERP]], [[Data Warehouse]]
related_features: [[Budget Management]], [[Purchase Order Routing]]
---
```

**Structure**:
```markdown
# {Integration Name}

## Overview
- External system: [name, version, owner]
- What data/signals are exchanged
- Why it matters to the engagement

## Current Architecture
[How does the legacy system integrate today?]
- Data flow diagram
- Frequency and volume
- Failure handling / SLAs
- Known issues or limitations

## Target Architecture (SFCC)
[How will this integrate with Salesforce B2B Commerce?]
- Proposed data flow
- Technical approach (API, ETL, middleware, etc.)
- Frequency and volume expectations
- Error handling and retry logic
- SLAs and monitoring

## Assessment
- **SFCC Readiness**: Is SFCC compatible with this integration?
- **Effort Estimate**: [days/weeks/months]
- **Risks**: [data quality, downtime, 3rd party reliability]
- **Dependencies**: [Other integrations, features, or decisions]

## Implementation Plan
- Data mapping requirements
- API authentication / credentials
- Testing strategy
- Cutover approach (parallel run, big bang, phased)
- Rollback plan

## Related
- **Entities**: [[Oracle ERP]], [[TradeWearables]]
- **Features**: [[Budget Management]], [[Purchase Order Routing]]
- **Gaps**: [[Real-time Sync Gap]]
- **Decision**: [[Real-time vs. Batch Sync]]

## Notes
- [Any additional context, performance tuning, or operational considerations]
```

---

### 4.7 Question

**Definition**: An open question that needs client/stakeholder input, clarification, or further analysis.

**Frontmatter**:
```yaml
---
type: question
client: boston-beer-company
priority: p0|p1|p2|p3  # P0 = blocks design/go-live; P3 = nice-to-have
status: open|answered|blocked|deferred|resolved
owner: Assignee Name
due_date: YYYY-MM-DD  # When answer needed
answered_by: Name (optional, if resolved)
answer_date: YYYY-MM-DD (optional, if resolved)
created: YYYY-MM-DD
updated: YYYY-MM-DD
sources: [meeting/transcript, email thread]
tags: [stakeholder-alignment, scoping, budget]
related_features: [[Feature Name]]
related_gaps: [[Gap Name]]
related_decisions: [[Decision Name]]
---
```

**Structure**:
```markdown
# {Question}

## Context
Why is this question important?
- Impact on engagement scope
- Impact on decision-making
- Stakeholder priority

## Question
[Specific, answerable question]

## Background
- First asked in: [[2024-03-15-discovery]]
- Previous attempts to answer: [context]
- Why it hasn't been answered yet: [blockers]

## Options / Considerations
- [Option A]
- [Option B]
- [Option C]

## Required Input
- Who needs to answer: [Stakeholder/Role]
- Information needed to answer: [specifics]
- By when: [YYYY-MM-DD]

## Related
- **Meeting**: [[2024-03-15-discovery]]
- **Feature**: [[Feature Name]]
- **Gap**: [[Gap Name]]
- **Decision**: [[Decision Name]]

## Answer (if resolved)
- **Answered by**: [Name] on [YYYY-MM-DD]
- **Answer**: [clear, specific response]
- **Implications**: [how this impacts scope, timeline, design]

## Notes
- [Assumptions made, follow-up questions, etc.]
```

---

## 5. Frontmatter Convention

Every page MUST start with YAML frontmatter. This is non-negotiable and required for LLM parsing, linting, and indexing.

### Minimal Required Frontmatter

```yaml
---
type: feature|entity|decision|meeting|gap|integration|question
client: {client-slug}|shared
status: active|deprecated|resolved|blocked|in-discovery|pending
created: YYYY-MM-DD
updated: YYYY-MM-DD
sources: [list/of/relative/paths/to/source/docs]
tags: [lowercase, hyphenated, category-specific]
---
```

### Status Values by Type

| Type | Valid Statuses |
|------|---|
| Entity | `active`, `deprecated`, `unknown` |
| Feature | `active`, `deprecated`, `in-discovery`, `blocked` |
| Decision | `pending`, `approved`, `implemented`, `rejected`, `under-review` |
| Meeting | `completed`, `scheduled`, `archived` |
| Gap | `open`, `under-review`, `resolved`, `workaround` |
| Integration | `active`, `planned`, `deprecated`, `tbd` |
| Question | `open`, `answered`, `blocked`, `deferred`, `resolved` |

### Tag Conventions

Tags are **lowercase, hyphenated**, and optionally prefixed by category:

- **Feature tags**: `#feature/budget-enforcement`, `#feature/custom-dev`
- **Gap tags**: `#gap/critical`, `#gap/high-priority`, `#gap/workaround`
- **Decision tags**: `#decision/pending`, `#decision/approved`, `#decision/architecture`
- **Integration tags**: `#integration/batch-job`, `#integration/real-time`
- **Domain tags**: `#commerce`, `#supply-chain`, `#compliance`
- **Status tags**: `#blocked`, `#urgent`, `#stakeholder-alignment`

Example frontmatter with comprehensive tags:

```yaml
---
type: gap
client: boston-beer-company
severity: critical
status: open
created: 2024-03-20
updated: 2024-04-10
sources:
  - BostonBeerCompany/analysis/sfcc-assessment.md
  - BostonBeerCompany/meetings/transcripts/2024-03-15.md
tags:
  - gap/critical
  - custom-dev
  - budget-enforcement
  - commerce
  - p0-blocker
---
```

---

## 6. Cross-Referencing Rules

Interconnection is the soul of a Karpathy-style wiki. Every page must explicitly link to related pages using Obsidian-style wiki-links.

### Syntax

```markdown
[[Page Name]]              # Basic link
[[Page Name|Custom Text]]  # Link with custom display text
[[../other-page]]          # Relative path (less common)
```

### Link Cardinality by Type

#### Features → Gaps
Every feature should link to its gaps. If there are no gaps (fully OOTB), say so explicitly.

```markdown
## Gaps
- [[Budget Management Gap]] — How SFCC handles custom budget rules
- **No gaps identified** — Budget Management is fully supported OOTB with configuration
```

#### Gaps → Decisions
Every gap must have at least one decision or proposed resolution linked.

```markdown
## Resolution Path
- See [[Decision: Budget Enforcement Approach]]
- See [[Integration: Oracle Budget Sync]]
```

#### Decisions → Questions
Every decision should link to the question(s) that motivated it.

```markdown
## Related
- **Question**: [[Does SFCC support co-op billing?]]
- **Question**: [[Should we use Vlocity or custom Apex?]]
```

#### Meetings → Entities, Features, Gaps, Questions
Every meeting summary must link to all artifacts discussed.

```markdown
## Features Discussed
- [[MerchTank Integration]] — Legacy system overview
- [[Budget Management]] — Key capability to port
- [[Purchase Order Routing]] — Workflow approval process

## Gaps Identified
- [[Dynamic Discount Gap]] — SFCC limitation discovered
- [[Real-time Inventory Gap]] — Performance requirement

## Questions Raised
- [[Can SFCC handle 10M+ SKUs?]]
- [[What's the ROI of custom vs. AppExchange?]]
```

### Link Density Expectations

- **Entity pages** should have 3-10 outgoing links (to features, integrations, decisions)
- **Feature pages** should have 2-5 links to gaps, decisions, meetings
- **Gap pages** should have 1-3 links to features, decisions, questions
- **Decision pages** should have 2-4 links to questions, features, meetings
- **Meeting pages** should have 5+ links (to entities, features, gaps, questions)
- **Question pages** should have 1-3 links (to features, gaps, decisions)

High link density enables LLM traversal and pattern discovery. Orphaned pages (no incoming/outgoing links) are a lint warning.

### Link Checking

The lint workflow (Section 9) will flag:
- Broken links (target page doesn't exist)
- Orphan pages (no incoming links)
- Missing expected links (e.g., gap with no decision)

---

## 7. Ingest Workflow

When new content arrives, a structured workflow updates and maintains the wiki.

### 7.1 New Meeting Transcript / Video

**Trigger**: A new meeting transcript lands in `BostonBeerCompany/meetings/transcripts/`

**Workflow**:
1. **Create meeting page**
   - File: `wiki/clients/{client}/meetings/{YYYY-MM-DD}-{type}.md`
   - Transcribe key takeaways, attendees, action items
   - Link to raw transcript in sources

2. **Extract features** (or update existing)
   - For each business capability mentioned:
     - If feature page exists: Add link in "Meeting History"
     - If feature page missing: Create new feature page
   - Link feature → meeting

3. **Identify gaps** (or update existing)
   - For each gap or limitation discovered:
     - If gap page exists: Add evidence link
     - If gap page missing: Create new gap page with status `open`
   - Link gap → feature, gap → meeting

4. **Note open questions** (or update existing)
   - For each question or ambiguity:
     - If question page exists: Update answer (if available) or status
     - If question page missing: Create new question page with priority, owner, due date
   - Link question → meeting, question → feature

5. **Update _index.md**
   - Add new pages to the content catalog
   - Update client overview (if major new entity/feature/gap)

6. **Log in _log.md**
   - Entry: `[2024-03-15 14:30] Meeting ingest: {client} — Discovered {N} features, {N} gaps, {N} questions`

**Example Entry**:
```markdown
## 2024-03-15 Meeting Ingest
**Source**: BostonBeerCompany/meetings/transcripts/2024-03-15-discovery.md
**Pages created**:
- [[2024-03-15-discovery]] (meeting)
- [[Budget Management]] (feature)
- [[Dynamic Discount Gap]] (gap)
- [[Can SFCC handle real-time discounts?]] (question)

**Pages updated**:
- [[MerchTank]] (entity) — New integration link added
- [[Purchase Order Routing]] (feature) — Workflow clarification from meeting

**Metrics**: 3 features discovered, 2 gaps, 1 question, 1 entity clarified
```

### 7.2 New Email / Document

**Trigger**: A client email or architecture document arrives (manually added to `BostonBeerCompany/emails/` or `BostonBeerCompany/docs/`)

**Workflow**:
1. Identify which entities, features, gaps, or decisions it affects
2. Update relevant pages with new information or evidence
3. Create new pages if a major new entity/feature/gap is introduced
4. Update _log.md with summary

### 7.3 Confluence Sync

**Trigger**: A new Confluence deliverable is published (SOW, design doc, gap analysis, etc.)

**Workflow**:
1. Compare Confluence state with wiki state
2. For each decision in Confluence:
   - If decision page exists in wiki: Update status, owner, approval dates
   - If decision page missing: Create it, linking to Confluence source
3. For each gap in Confluence:
   - If gap page exists: Update with Confluence assessment/resolution
   - If gap page missing: Create it
4. Reconcile any contradictions (e.g., different gap counts, conflicting decisions)
5. Update _log.md

---

## 8. Query Workflow

When an LLM or human asks a question about the client or platform:

### 8.1 Search & Synthesize

1. **Search wiki pages** for related content (features, gaps, decisions, questions)
2. **Synthesize answer** from existing pages
3. **Provide answer** with citations to wiki pages (and raw sources if needed)

### 8.2 Promote to Wiki

If the answer is valuable and reusable (not just a one-off explanation):
1. Create a new wiki page (e.g., a Decision or Feature summary)
2. Add to _index.md
3. Log query and promotion in _log.md

### 8.3 Log in _log.md

**Example Query Log Entry**:
```markdown
## 2024-04-01 Query
**Question**: "Does SFCC support co-op billing out of the box?"
**Answer**: No, SFCC has no OOTB co-op billing. See [[Co-op Billing Gap]] for detailed assessment and [[Decision: Co-op Billing Approach]] for proposed resolution (custom Apex).
**Promoted**: No (answered from existing pages)
**Confidence**: High (backed by 2 client meetings, SFCC assessment)
```

---

## 9. Lint Workflow

Periodic (weekly or before key milestones) health checks maintain wiki quality and surface problems.

### 9.1 Lint Checks

#### Contradictions
- **Detection**: Features assessed differently in different meetings (e.g., "OOTB" in Jan, "gap" in March)
- **Action**: Flag in _log.md, investigate root cause, reconcile pages
- **Example Output**:
  ```
  CONTRADICTION: [[Budget Management]] — Jan assessment says "OOTB config only",
  March meeting says "requires custom calc". Reconcile or document delta.
  ```

#### Orphans
- **Detection**: Pages with no incoming or outgoing links
- **Action**: Review page, add cross-references, or mark as deprecated
- **Example Output**:
  ```
  ORPHAN: [[Some Legacy System]] — No features or decisions link to this entity.
  Consider deprecating or finding connections.
  ```

#### Stale Pages
- **Detection**: Pages not updated since new related sources were ingested
- **Action**: Review page, update if needed, or mark as deprecated
- **Example Output**:
  ```
  STALE: [[Budget Management]] — Last updated 2024-03-15, but 3 new meetings
  since then mention budget logic. Refresh page.
  ```

#### Missing Cross-Refs
- **Detection**: Features mentioned without linked gap pages; gaps without decision pages
- **Action**: Create missing pages or add links
- **Example Output**:
  ```
  MISSING_GAP: [[Dynamic Pricing]] feature mentioned 3 times but has no gap page.
  Create or assess if truly OOTB.

  MISSING_DECISION: [[Real-time Sync Gap]] has no linked decision.
  Add decision or question link.
  ```

#### Open Questions
- **Detection**: P0 questions unresolved for > 2 weeks
- **Action**: Flag in _log.md, escalate to stakeholder
- **Example Output**:
  ```
  P0_OVERDUE: [[Can SFCC handle 10M SKUs?]] — Due 2024-03-20, no answer yet.
  Owner: [Name]. Status: Escalate.
  ```

#### Decision Drift
- **Detection**: Decisions that changed between meetings (e.g., "Use Vlocity" in Jan, "Custom Apex" in March) without explicit resolution
- **Action**: Create new decision page or update existing with version history
- **Example Output**:
  ```
  DECISION_DRIFT: [[Budget Solution]] — Jan: "Use Vlocity", March: "Custom Apex".
  Update decision page with rationale for change.
  ```

### 9.2 Lint Run Output

Create a dated lint log file (`wiki/_schema/LINT_LOG.md`):

```markdown
# Lint Run — 2024-04-05

**Total Pages**: 145
**Health Score**: 92% (excellent)

## Issues Found

### Contradictions (1)
- [[Budget Management]] — Assessment mismatch between meetings

### Orphans (2)
- [[Legacy Reporting System]]
- [[Unused Integration Placeholder]]

### Stale (3)
- [[Purchase Order Routing]] — 4 weeks, no update
- [[Inventory Sync]] — 3 weeks, no update
- [[Tax Compliance Gap]] — 2 weeks, no update

### Missing Cross-Refs (5)
- [[Dynamic Pricing]] (feature) — No gap page despite being mentioned as gap in 2 meetings
- [[Real-time Sync Gap]] — No decision page
- [[Payment Tokenization Question]] — No decision or integration link

### P0 Overdue (2)
- [[Can SFCC handle 10M SKUs?]] — Due 2024-03-20, 16 days overdue
- [[What's the total LOE for custom dev?]] — Due 2024-04-01, 4 days overdue

### Decision Drift (1)
- [[Budget Solution]] — Changed from Vlocity to custom Apex between Jan and March, no explicit resolution

## Recommendations
1. Update [[Budget Management]] to reflect current state (appears to require custom work)
2. Create [[Dynamic Pricing Gap]] page
3. Escalate P0 questions to [Stakeholder]
4. Deprecate [[Legacy Reporting System]] (no longer relevant)

## Next Lint Run
2024-04-12 (one week)
```

---

## 10. Naming Conventions

### File Names
- **Format**: `kebab-case`
- **Length**: Descriptive but concise (max 60 chars)
- **Examples**:
  - ✓ `budget-management.md`
  - ✓ `virtual-warehouse-inventory.md`
  - ✓ `can-sfcc-handle-10m-skus.md`
  - ✗ `Budget_Management_Feature_Page.md` (wrong case and underscores)
  - ✗ `q.md` (too vague)

### Client Slugs
- **Format**: `lowercase-hyphenated`
- **Examples**:
  - `boston-beer-company`
  - `acme-corp-reseller`
  - `heartland-foodservice`

### Platform Slugs
- **Format**: `lowercase-hyphenated`
- **Examples**:
  - `salesforce-b2b-commerce`
  - `salesforce-lightning`
  - `oracle-netsuite`

### Tag Format
- **Format**: `lowercase-hyphenated`, optionally prefixed by category
- **Examples**:
  - `#feature/budget-management`
  - `#gap/critical`
  - `#decision/pending`
  - `#integration/real-time`
  - `#domain/commerce`
  - `#domain/supply-chain`

### Meeting File Names
- **Format**: `{YYYY-MM-DD}-{meeting-type}.md`
- **Examples**:
  - `2024-03-15-discovery.md`
  - `2024-04-10-design-review.md`
  - `2024-05-01-stakeholder-alignment.md`

---

## 11. Decision Status & Color System

The color system provides a visual, at-a-glance assessment of each feature/gap's resolution approach in Salesforce B2B Commerce.

### Color Meanings

| Color | Category | Meaning | Effort | Timeline |
|-------|----------|---------|--------|----------|
| 🟢 | OOTB | Standard Salesforce B2B Commerce feature, no modifications needed | None | Immediate (configuration only) |
| 🔵 | Config | Salesforce native feature requiring configuration (no code) | 1-5 days | 1-2 weeks |
| 🟡 | Custom Dev | Requires custom Apex, Lightning, Flow, or JavaScript | 2-12 weeks | 2-8 weeks |
| 🔴 | Gap / New Build | No in-platform equivalent; net-new development required | 4-16 weeks | 4-12 weeks |
| ⚪ | TBD | Awaiting client input, requirements clarification, or further analysis | Unknown | Pending decision |
| 🟣 | 3rd Party | AppExchange app, managed package, or external vendor solution | 1-4 weeks | 2-4 weeks |

### Usage in Decisions

Every decision page should declare its color:

```yaml
---
type: decision
color: 🟡  # Custom Dev required
status: approved
---
```

### Summary Example

A decision summary might look like:

```markdown
## Decision: Budget Management Approach

**Color**: 🟡 Custom Dev
**Rationale**: SFCC has budget management UI, but the co-op deduction logic is non-standard. Requires custom Apex trigger and Flow.
**Effort**: 6 weeks of custom development + 1 week testing
**Timeline**: Week 8-14 of engagement
```

---

## 12. Relationship to Existing Pipeline

The wiki does **not replace** the analysis pipeline. Instead, it **consumes and elevates** its outputs.

### Pipeline → Wiki Flow

```
BostonBeerCompany/meetings/
├─ transcripts/2024-03-15.md (raw, immutable)
├─ frames/2024-03-15-analysis.json (raw, immutable)
└─ analysis/sfcc-assessment.md (raw, immutable)
        ↓
        [Ingest Workflow]
        ↓
wiki/clients/boston-beer-company/
├─ meetings/2024-03-15-discovery.md (synthesized)
├─ features/
├─ gaps/
├─ decisions/
└─ questions/
```

### What Pipeline Outputs Provide

- **Transcripts**: Raw words, searchable, timestamped
- **Frame Analysis**: Visual evidence, structured data extraction
- **Assessments & Gap Analyses**: Detailed technical findings

### What Wiki Adds

- **Cross-referencing**: Links features to gaps to decisions to questions
- **Decision Tracking**: Status, owners, approval dates, color codes
- **Question Management**: Open questions with priorities and owners
- **Trend Detection**: Contradictions, decision drift, stale information
- **Reusable Knowledge**: Patterns, templates, platform-level insights

### Example: A Gap's Journey

1. **Raw**: Video mentions "dynamic pricing not supported" → Frame analysis extracts this
2. **Pipeline**: SFCC assessment includes "Dynamic Pricing Gap" in structured analysis
3. **Wiki Ingest**:
   - Create [[Dynamic Pricing Gap]] page, citing pipeline analysis
   - Create [[Dynamic Pricing]] feature page
   - Create [[Can SFCC handle dynamic pricing?]] question
   - Link all three together
4. **Query**: When asked "What gaps are P1?", wiki returns [[Dynamic Pricing Gap]] with full context and decision status
5. **Decision**: Create [[Decision: Dynamic Pricing Approach]] (color 🟡 = custom dev), linked to question and gap
6. **Lint**: Next week, lint checks that gap, decision, and question are all linked

---

## 13. Examples

### Example 1: Complete Feature Page

**File**: `wiki/clients/boston-beer-company/features/budget-management.md`

```yaml
---
type: feature
client: boston-beer-company
status: active
current_platform: hybrid  # Legacy in MerchTank, will migrate to SFCC
priority: p0
created: 2024-03-15
updated: 2024-04-10
sources:
  - BostonBeerCompany/meetings/transcripts/2024-03-15-discovery.md
  - BostonBeerCompany/analysis/sfcc-assessment.md
tags:
  - feature/commerce
  - b2b-specific
  - strategic
discovered_by_meeting: [[2024-03-15-discovery]]
---

# Budget Management

## Definition

Budget Management is the capability for distributors to allocate spend budgets to customers, accounts, or regions, and enforce real-time budget limits during order placement. Customers can see remaining budget and are prevented from exceeding limits.

## Current Behavior (MerchTank Legacy)

- Budgets set per customer account
- Budget tracking is per fiscal year
- Co-op deductions reduce budget in real-time
- Budget alerts sent when 75% consumed
- Customers can request budget increases (manual approval workflow)
- Integration with Oracle ERP for budget master data

## Target Behavior (Salesforce B2B Commerce)

- Budgets defined per account, per year
- Real-time budget enforcement at checkout
- Co-op deductions applied automatically via [[Oracle ERP Sync]]
- Budget dashboards in community portal
- Escalation workflow for overages (subject to approval)

## Assessment

- **OOTB Status**: ⚠️ Partial — SFCC has budget tracking and alerts, but co-op deduction logic is custom
- **Estimated Effort**: 6-8 weeks (custom Apex + Flow + integration tuning)
- **Risks**:
  - Real-time Oracle sync latency could cause budget overages
  - Co-op deduction calculations are complex and error-prone
  - High customer visibility; any failures directly impact sales
- **Dependencies**: [[Oracle ERP Sync]], [[Co-op Billing Gap]], [[Real-time Sync Architecture Decision]]

## Meeting History

- [[2024-03-15-discovery]] — First mentioned as core capability; MerchTank implementation reviewed
- [[2024-04-10-deep-dive]] — Detailed co-op deduction workflow captured; Oracle sync complexity identified
- [[2024-05-01-design-review]] — Design spec drafted; approved with custom development path

## Gaps & Issues

- [[Co-op Billing Gap]] — SFCC has no OOTB co-op deduction logic
- [[Real-time Sync Gap]] — Oracle ERP budget updates need real-time reflection in SFCC

## Decision & Resolution

See [[Decision: Budget Management Approach]] (Color: 🟡 Custom Dev)

## Next Steps

- [ ] Finalize co-op deduction calculation rules with Finance team
- [ ] Complete Oracle integration data mapping
- [ ] Estimate custom Apex & Flow development
- [ ] Schedule design review with architects
```

### Example 2: Complete Gap Page

**File**: `wiki/clients/boston-beer-company/gaps/co-op-billing-gap.md`

```yaml
---
type: gap
client: boston-beer-company
gap_category: functional
severity: critical
status: under-review
feature: [[Budget Management]]
meeting: [[2024-03-15-discovery]]
created: 2024-03-20
updated: 2024-04-15
sources:
  - BostonBeerCompany/analysis/sfcc-assessment.md
  - BostonBeerCompany/meetings/transcripts/2024-03-15-discovery.md
  - BostonBeerCompany/meetings/transcripts/2024-04-10-deep-dive.md
tags:
  - gap/critical
  - custom-dev
  - commerce
  - p0-blocker
decision: [[Decision: Budget Management Approach]]
---

# Co-op Billing Gap

## Definition

Salesforce B2B Commerce does not have an out-of-the-box co-operative (co-op) billing deduction system. Co-op deductions are automatic reductions of customer budgets based on promotional spend commitments and sales performance. This is a critical gap for Boston Beer Company's B2B model.

## Current State (MerchTank)

- Co-op deductions calculated nightly based on:
  - Promotional spend (customer contribution vs. company contribution)
  - Sales rebate thresholds
  - Volume incentives
- Deductions applied automatically to customer budget
- Oracle ERP is master of co-op rules and spend tracking
- Customer-facing reports show co-op impact

## Target State (SFCC)

- Co-op deductions must be applied in real-time at order checkout (or as nightly batch)
- Budget is reduced by co-op amount before order is placed
- Integration with Oracle ERP for:
  - Co-op rate tables
  - Spend tracking per customer
  - Deduction calculations
- Audit trail of all deductions for compliance

## Evidence

**Meeting 2024-03-15 (Discovery)**:
> "Co-op deductions are how we manage distributor spend. Every order reduces their available budget by a percentage based on their promotional contribution. This needs to work in Salesforce B2B Commerce."

**Meeting 2024-04-10 (Deep Dive)**:
> "The calculation is complex. Co-op rates vary by product line, customer tier, and promotional campaign. We need Oracle to provide real-time co-op rates."

**SFCC Assessment**:
> "Salesforce B2B Commerce has budget enforcement but no co-op deduction module. Custom development required."

## Assessment

- **Severity**: CRITICAL — Without this, budget enforcement is incomplete. Customers could exceed actual spend commitments.
- **Likelihood**: Definitely impacts go-live if not resolved. Core to financial controls.
- **Estimated Effort**:
  - Co-op deduction calculation engine: 4 weeks (Apex)
  - Oracle sync for co-op rates: 2 weeks (Integration)
  - Testing & validation: 2 weeks
  - **Total**: 6-8 weeks

## Resolution Options

1. **Custom Apex Engine** (Recommended)
   - Build custom calculation logic in Apex
   - Sync co-op rates nightly from Oracle
   - Apply deductions real-time at checkout
   - Effort: 6-8 weeks
   - Risk: High complexity, must be accurate
   - Benefit: Full control, meets all requirements

2. **Nightly Batch Process**
   - Calculate deductions overnight, apply to budget pool
   - Less real-time but simpler
   - Effort: 4-5 weeks
   - Risk: Customers may see stale budgets during day
   - Benefit: Simpler, easier to test

3. **3rd Party AppExchange**
   - Evaluate available budget/billing solutions
   - Effort: 2-3 weeks (evaluation + integration)
   - Risk: May not align perfectly with Oracle rates
   - Benefit: Reduced custom development

4. **Oracle Integration Only**
   - Let Oracle calculate deductions, pull deduction amount into SFCC
   - Effort: 3-4 weeks
   - Risk: Dependency on Oracle availability
   - Benefit: Single source of truth for calculations

## Recommended Resolution

**Approach**: Custom Apex Engine (Option 1)
**Owner**: Verndale Engineering + Client Finance Team (co-owned)
**Timeline**: Week 8-16 of engagement (8-week effort window)
**Justification**:
- Gives full control over logic and audit trail
- Integrates cleanly with SFCC budget management
- Meets real-time requirement
- Can be tested thoroughly with historical data

## Implementation Plan

1. **Week 1-2**: Detailed requirements gathering
   - Co-op rate structure documentation
   - Sample data and calculation examples
   - Oracle API/export specifications

2. **Week 3-4**: Apex development
   - Co-op calculation service
   - Unit tests

3. **Week 5-6**: Integration
   - Oracle sync process
   - Real-time budget reduction logic

4. **Week 7-8**: Testing, docs, UAT

## Related

- **Feature**: [[Budget Management]]
- **Decision**: [[Decision: Budget Management Approach]]
- **Question**: [[How should co-op rates be synchronized from Oracle?]]
- **Integration**: [[Oracle ERP Sync]]
- **Meetings**: [[2024-03-15-discovery]], [[2024-04-10-deep-dive]]

## Notes

- Co-op is non-negotiable for the client; any solution must be 100% accurate
- Oracle is the source of truth for co-op rates; SFCC cannot override
- Audit trail is critical for compliance; all deductions must be logged
- Performance is important; deduction calculation must not slow checkout
```

### Example 3: Complete Decision Page

**File**: `wiki/clients/boston-beer-company/decisions/budget-management-approach.md`

```yaml
---
type: decision
client: boston-beer-company
status: approved
decision_category: architecture
color: 🟡
owner: Verndale Lead Architect
due_date: 2024-04-20
approved_by: [Client CTO, Client CFO]
approval_date: 2024-04-25
created: 2024-03-20
updated: 2024-04-25
sources:
  - BostonBeerCompany/meetings/transcripts/2024-04-10-deep-dive.md
  - email-thread-budget-approach.md
tags:
  - decision/approved
  - architecture
  - custom-dev
  - commerce
related_features: [[Budget Management]]
related_gaps: [[Co-op Billing Gap]]
related_questions: [[How should co-op rates be synchronized from Oracle?]]
---

# Decision: Budget Management Approach

## Question

How should Salesforce B2B Commerce enforce budget limits and apply co-op deductions for Boston Beer Company's B2B customers?

See [[Can SFCC handle co-op billing?]]

## Options Considered

### Option 1: Custom Apex Engine (Recommended)
- Build custom calculation logic in Apex that replicates MerchTank co-op rules
- Sync co-op rates nightly from Oracle ERP
- Apply deductions real-time at order checkout
- **Pros**: Full control, meets all requirements, single source of truth
- **Cons**: 6-8 weeks of custom development, higher risk if logic is incorrect
- **Effort**: 6-8 weeks
- **Cost**: ~$80-100K

### Option 2: Nightly Batch Process
- Calculate deductions overnight, apply to budget pool before business hours
- Simpler to implement and test
- **Pros**: Simpler, lower risk, lower cost
- **Cons**: Budgets may be stale during the day; customers see previous day's deductions
- **Effort**: 4-5 weeks
- **Cost**: ~$50-70K

### Option 3: 3rd Party AppExchange Solution
- Evaluate available Salesforce budget/billing apps
- Integrate with Oracle for co-op rates
- **Pros**: Reduced custom development, potentially faster
- **Cons**: May not align perfectly with client's co-op rules; vendor lock-in
- **Effort**: 2-3 weeks (evaluation + integration)
- **Cost**: ~$20-30K (app) + integration

### Option 4: Oracle as Source of Truth
- Let Oracle calculate deductions, pull deduction amount into SFCC budget pool
- SFCC acts as display/enforcement layer only
- **Pros**: Single source of truth, reduced custom code
- **Cons**: Dependent on Oracle availability; less flexible if rules change
- **Effort**: 3-4 weeks
- **Cost**: ~$40-60K

## Decision

**Status**: APPROVED
**Color**: 🟡 (Custom Dev)
**Approved By**: [Client CTO], [Client CFO]
**Date Approved**: 2024-04-25

### Selected Option: Custom Apex Engine (Option 1)

We are building a custom Apex-based co-op deduction engine in Salesforce B2B Commerce. This engine will:

1. **Replicate MerchTank Logic** — All existing co-op deduction rules implemented in Apex
2. **Integrate with Oracle** — Nightly sync of co-op rate tables from Oracle ERP
3. **Real-Time Enforcement** — Deductions applied at checkout before order submission
4. **Full Audit Trail** — Every deduction logged with calculation details

## Rationale

### Business Driver
Co-op deductions are core to Boston Beer Company's financial controls and customer relationship management. Any solution must be 100% accurate and meet real-time requirements.

### Technical Rationale
- Apex allows full replication of complex co-op rules
- Real-time enforcement meets customer expectations
- Nightly Oracle sync provides reliable, auditable source of truth
- Custom engine gives flexibility if rules evolve

### Risk Mitigation
- Extensive testing using historical data (3 months of production transactions)
- Parallel run for first 2 weeks post-go-live
- Rollback plan: Revert to manual co-op adjustments if engine fails
- Weekly validation against MerchTank during transition

### Stakeholder Alignment
- Finance team confident in accuracy and audit trail
- Operations team supportive of real-time enforcement
- CTO approved architecture and data integration approach

## Implementation Plan

**Timeline**: Week 8-16 of engagement (8-week effort window)

**Phase 1: Requirements & Data Mapping (Week 1-2)**
- Document all co-op rate structures
- Map Oracle schema to Apex objects
- Create test data sets

**Phase 2: Apex Development (Week 3-4)**
- Implement deduction calculation service
- Implement budget reduction trigger
- Unit tests (90%+ coverage)

**Phase 3: Oracle Integration (Week 5-6)**
- Scheduled flow to sync co-op rates nightly
- Error handling and retry logic
- Integration testing

**Phase 4: Testing & UAT (Week 7-8)**
- Functional testing with sample data
- Performance testing at scale
- User acceptance testing with Finance team
- Documentation and training

**Success Criteria**:
- Deduction calculation accuracy: 100% (validated against MerchTank)
- Sync reliability: 99.9% (< 1 sync failure per month)
- Checkout performance: < 500ms deduction calculation impact
- Audit trail: 100% of deductions logged

## Dependencies

- Oracle ERP availability and data quality (high priority)
- Client Finance team availability for requirements and UAT
- Access to 3 months historical MerchTank data for testing
- Salesforce Order Management license (if using SOM) — See [[Decision: Salesforce Order Management Licensing]]

## Review History

- **2024-03-20**: Draft decision proposed after initial discovery
- **2024-04-10**: Deep-dive with technical and Finance teams; options evaluated
- **2024-04-20**: Design spec created; stakeholder review
- **2024-04-25**: Approved by CTO and CFO

## Related

- **Gaps**: [[Co-op Billing Gap]]
- **Feature**: [[Budget Management]]
- **Question**: [[Can SFCC handle co-op billing?]], [[How should co-op rates be synchronized from Oracle?]]
- **Integration**: [[Oracle ERP Sync]]
- **Meeting**: [[2024-03-15-discovery]], [[2024-04-10-deep-dive]], [[2024-04-20-design-review]]
```

---

## 14. Templates & Checklists

### Ingest Checklist

When a new meeting transcript is added:

- [ ] Create meeting summary page
- [ ] Extract and create/update feature pages
- [ ] Extract and create/update gap pages
- [ ] Identify and create/update question pages
- [ ] Identify and create/update entity pages
- [ ] Add links from features → gaps → decisions → questions
- [ ] Update _index.md with new pages
- [ ] Log ingest in _log.md
- [ ] Run lint to check for contradictions or orphans

### Decision Page Checklist

Before publishing a decision page:

- [ ] Question is clearly stated (see [[Question Name]])
- [ ] All options are documented (3+ options if complex)
- [ ] Rationale explains why this option was chosen
- [ ] Color code is assigned (🟢🔵🟡🔴⚪🟣)
- [ ] Owner and timeline are clear
- [ ] Success criteria are defined
- [ ] Related pages are linked (features, gaps, questions, meetings)
- [ ] Approval status and date(s) are documented
- [ ] Implementation plan is outlined

### Gap Page Checklist

Before publishing a gap page:

- [ ] Gap is clearly defined (current vs. target)
- [ ] Evidence links back to meetings or assessments
- [ ] Resolution options are documented (3+ options if complex)
- [ ] Severity and effort estimate are assessed
- [ ] Recommended resolution is stated
- [ ] Linked to feature page
- [ ] Linked to related decision or question
- [ ] Status is set (open, under-review, resolved, workaround)

---

## 15. Maintenance & Governance

### Weekly Tasks

- **New meeting ingest**: Process any new transcripts, create/update pages
- **Query log review**: Promote valuable queries to wiki pages
- **Question status review**: Check P0 questions for overdue answers

### Bi-Weekly Tasks

- **Lint run**: Execute health checks, review issues
- **Index update**: Ensure _index.md reflects all new pages
- **Cross-ref audit**: Check for orphans, missing links

### Monthly Tasks

- **Stakeholder sync**: Share wiki updates, decision status, open questions
- **Platform knowledge update**: Add new SFCC patterns or learnings to shared platform pages
- **Retrospective**: Lessons learned from engagement, document patterns

### Governance

- **Owner**: Verndale Lead Architect (per engagement)
- **Reviewers**: Verndale Project Manager, Client Product Lead
- **Approval Gate**: All Decision pages (color 🔴🟡🟣) require CTO or CFO sign-off before implementation
- **Audit**: All gap assessments must cite evidence (meetings, assessments, demos)

---

## 16. Final Notes

This wiki is a **living document**. It evolves with each client engagement. Over time, it becomes an invaluable repository of institutional knowledge, decision rationale, and reusable patterns.

**For LLMs reading this**: Use the frontmatter, wiki-links, and cross-referencing structure to understand relationships and context. When asked a question, search for related pages (features, gaps, decisions, questions) and synthesize an answer. If the answer is novel and reusable, promote it to a wiki page.

**For humans maintaining this**: Embrace the structure. Every page created, every link added, every lint run executed makes the wiki more valuable. Contradictions and stale information are problems to solve, not annoyances. The wiki's value compounds over time.

**Next Steps**:
1. Create client-specific README pages (auto-maintained summaries of entities, features, gaps, decisions)
2. Create `TEMPLATES.md` with copy-paste templates for each page type
3. Create `LINT_RULES.md` with detailed lint check logic
4. Implement automated indexing and lint runs (optional: GitHub Actions, CI/CD)
5. Establish a cadence for query logging, promotion, and wiki growth

---

**Version**: 1.0
**Last Updated**: 2024-04-06
**Maintainer**: Verndale LLM Wiki System
