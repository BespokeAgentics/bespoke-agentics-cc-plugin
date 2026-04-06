---
type: entity
client: shared
status: active
category: process
created: 2026-04-06
updated: 2026-04-06
sources:
  - ../../../wiki/_schema/SCHEMA.md
tags:
  - process
  - wiki
  - maintenance
---

# Wiki Maintenance Playbook

## Overview

The Verndale wiki is a living, continuously maintained knowledge base that serves as the single source of truth for client-specific intelligence, technical decisions, and business capabilities across all Salesforce B2B Commerce migration engagements. Unlike the immutable analysis pipeline (which produces outputs stored in client folders), the wiki synthesizes, cross-references, and evolves knowledge over time.

This playbook documents the operational workflows that keep the wiki healthy, interconnected, and valuable.

---

## Ingest Workflow

When new content arrives—whether from a migration pipeline run, client email, meeting recording, or Confluence document—a structured workflow updates and maintains the wiki.

### Trigger: New Meeting Transcript / Video

**Source**: A new meeting transcript or analysis output lands in `{ClientFolder}/meetings/transcripts/` or `{ClientFolder}/analysis/`

**Workflow Steps**:

1. **Create or update meeting page**
   - File: `wiki/clients/{client-slug}/meetings/{YYYY-MM-DD}-{meeting-type}.md`
   - Complete frontmatter: type, client, meeting_date, meeting_type, attendees, duration_minutes, sources
   - Structure: Context → Key Takeaways → Features Discussed → Gaps Identified → Decisions Made → Open Questions → Action Items → Raw Evidence → Next Steps
   - Link to raw transcript in sources field
   - Example: `wiki/clients/boston-beer-company/meetings/2024-03-15-discovery.md`

2. **Extract and organize features**
   - For each business capability discovered in meeting or pipeline output:
     - If feature page exists: Add link in "Meeting History" section; update `updated` date
     - If feature page missing: Create new feature page at `wiki/clients/{client-slug}/features/{feature-slug}.md`
   - Frontmatter: type: feature, client, status: active|in-discovery|deprecated, current_platform, priority, created, updated, sources, tags, discovered_by_meeting
   - Structure: Definition → Current Behavior (Legacy) → Target Behavior (SFCC) → Assessment → Meeting History → Next Steps
   - Link feature → meeting and feature → gaps

3. **Extract and organize gaps**
   - For each gap or limitation mentioned:
     - If gap page exists: Update with new evidence links, meeting references
     - If gap page missing: Create new gap page at `wiki/clients/{client-slug}/gaps/{gap-slug}.md` with status: `open`
   - Frontmatter: type: gap, client, gap_category, severity, status: open|under-review|resolved|workaround, feature, meeting, created, updated, sources, tags
   - Structure: Definition → Current State → Target State → Evidence → Assessment → Resolution Options → Recommended Resolution → Related → Notes
   - Link gap → feature, gap → meeting, gap → decision (if one exists)

4. **Extract and organize questions**
   - For each open question, ambiguity, or item needing stakeholder input:
     - If question page exists: Update answer (if available) or status; update `updated` date
     - If question page missing: Create new question page at `wiki/clients/{client-slug}/questions/{question-slug}.md`
   - Frontmatter: type: question, client, priority: p0|p1|p2|p3, status: open|answered|blocked|deferred|resolved, owner, due_date, created, updated, sources, tags
   - Structure: Context → Question → Background → Options/Considerations → Required Input → Related → Answer (if resolved) → Notes
   - Link question → feature, question → gap, question → decision

5. **Update wiki indexes**
   - Update `wiki/_index.md`: Add new pages to content catalog; maintain entry count and summary
   - Update `wiki/clients/{client-slug}/README.md`: Refresh client overview with metrics (features: N, gaps: N, decisions: N, questions: N)
   - Example index entry: `[[Budget Management]] (feature, active) — p1 priority, discovered 2024-03-15, 2 gaps, 1 decision`

6. **Log ingest activity**
   - Update `wiki/_log.md` with entry at top (reverse chronological)
   - Format: `## {YYYY-MM-DD HH:MM} Meeting Ingest — {client-slug}`
   - Include: source file, pages created, pages updated, metrics (features, gaps, questions), highlights
   - Example:
     ```markdown
     ## 2024-03-15 14:30 Meeting Ingest — boston-beer-company
     **Source**: BostonBeerCompany/meetings/transcripts/2024-03-15-discovery.md
     **Pages created**: 4
     - [[2024-03-15-discovery]] (meeting)
     - [[Budget Management]] (feature)
     - [[Dynamic Discount Gap]] (gap)
     - [[Can SFCC handle real-time discounts?]] (question)

     **Pages updated**: 2
     - [[MerchTank]] (entity) — Added integration link
     - [[Purchase Order Routing]] (feature) — Updated workflow from meeting

     **Metrics**: 3 features discovered, 2 gaps, 1 question, 0 decisions made
     **Tags**: discovery, stakeholder-alignment, critical
     ```

### Trigger: New Email / Document

**Source**: Client email, architecture document, or design decision lands in client folder

**Workflow Steps**:

1. Identify which entities, features, gaps, or decisions it affects
2. Update relevant existing pages with new information or evidence
3. Create new pages if major new entity/feature/gap is introduced
4. Update `wiki/_log.md` with summary (same format as meeting ingest)

### Trigger: Confluence Sync

**Source**: New Confluence deliverable published (gap analysis export, design doc, meeting notes, etc.)

**Workflow Steps**:

1. Compare Confluence state with current wiki state
2. For each decision in Confluence:
   - If decision page exists: Update status, owner, approval dates, linked meetings
   - If decision page missing: Create it at `wiki/clients/{client-slug}/decisions/{decision-slug}.md`, linking to Confluence source
3. For each gap in Confluence:
   - If gap page exists: Update with Confluence assessment, resolution approach, effort estimate
   - If gap page missing: Create new gap page
4. **Reconcile contradictions**: If Confluence says "X gaps identified" but wiki shows Y, investigate and document delta
5. Update `wiki/_log.md` with sync summary

---

## Query Workflow

When an LLM or human asks a question about a client or platform:

### Search & Synthesize

1. **Search wiki pages** for related content
   - Look across features, gaps, decisions, questions, meetings
   - Use client slug and tag filters to scope correctly
   - Example queries: "What gaps are p1?", "Who decided on the budget solution?", "What meetings mentioned inventory?"

2. **Synthesize answer** from existing pages
   - Link to relevant wiki pages as evidence
   - Trace back to source meetings and pipeline outputs if helpful
   - Provide confidence assessment based on source recency and link density

3. **Provide answer** with citations
   - Cite specific pages (with wiki-links)
   - Reference raw sources (pipeline documents, transcripts) for additional evidence
   - Highlight any contradictions or stale information

### Promote to Wiki (Optional)

If the answer is valuable and reusable (not a one-off explanation):

1. Create a new wiki page (e.g., Decision, Feature summary, or Platform pattern)
2. Add to `wiki/_index.md`
3. Log query and promotion in `wiki/_log.md`

**Example Promotion Log Entry**:
```markdown
## 2024-04-01 Query → Promotion
**Question**: "Does SFCC support co-op billing out of the box?"
**Answer**: No. See [[Co-op Billing Gap]] for detailed assessment.
**Promoted**: Yes, created [[Decision: Co-op Billing Approach]] (custom Apex, 6 weeks, p1)
**Sources**: [[2024-03-15-discovery]], [[2024-04-10-deep-dive]], SFCC B2B Expert assessment
**Confidence**: High (backed by 2 client meetings, SFCC validation)
```

### Log Queries in _log.md

```markdown
## 2024-04-01 Query
**Question**: "Does SFCC support co-op billing out of the box?"
**Answer**: No, SFCC has no OOTB co-op billing. See [[Co-op Billing Gap]] for assessment and [[Decision: Co-op Billing Approach]] for proposed resolution.
**Promoted**: No (answered from existing pages)
**Confidence**: High (2 client meetings + SFCC validation)
```

---

## Lint Workflow

Periodic (weekly or before key milestones) health checks maintain wiki quality and surface problems.

### Lint Checks

#### Contradictions
- **Detection**: Features or gaps assessed differently in different meetings (e.g., "OOTB" in Jan, "gap" in March)
- **Action**: Flag in `wiki/_schema/LINT_LOG.md`, investigate root cause, reconcile pages
- **Example Output**:
  ```
  CONTRADICTION: [[Budget Management]] — Jan assessment: "OOTB config only"
  March meeting: "requires custom calc". Decision changed but not documented.
  ACTION: Update [[Decision: Budget Enforcement Approach]] with explicit rationale for change.
  ```

#### Orphans
- **Detection**: Pages with no incoming or outgoing links (isolated islands)
- **Action**: Review page, add cross-references, or mark as deprecated
- **Example Output**:
  ```
  ORPHAN: [[Some Legacy System]] — No features or decisions link to this entity.
  If still relevant, connect to features or deprecate.
  ```

#### Stale Pages
- **Detection**: Pages not updated since new related sources were ingested
- **Action**: Review page, update if needed, or mark as deprecated
- **Example Output**:
  ```
  STALE: [[Budget Management]] — Last updated 2024-03-15, but 3 new meetings
  (2024-03-20, 2024-04-05, 2024-04-10) mention budget logic. Refresh page.
  ```

#### Missing Cross-Refs
- **Detection**: Features mentioned without linked gap pages; gaps without decision pages; questions without linked decisions
- **Action**: Create missing pages or add links
- **Example Output**:
  ```
  MISSING_GAP: [[Dynamic Pricing]] feature mentioned in 3 meetings but has no gap page.
  ACTION: Create [[Dynamic Pricing Gap]] or assess if truly OOTB.

  MISSING_DECISION: [[Real-time Sync Gap]] identified but no linked decision.
  ACTION: Create [[Decision: Real-time vs. Batch Sync]] or question page.
  ```

#### Open Questions
- **Detection**: P0 questions unanswered for > 2 weeks; P1 for > 4 weeks
- **Action**: Flag in LINT_LOG, escalate to owner/stakeholder
- **Example Output**:
  ```
  P0_OVERDUE: [[Can SFCC handle 10M SKUs?]] — Due 2024-03-20, no answer 16 days overdue.
  Owner: [Name]. STATUS: Escalate immediately.
  ```

#### Decision Drift
- **Detection**: Decisions that changed between meetings without explicit resolution documented
- **Action**: Create new decision page or update existing with version history
- **Example Output**:
  ```
  DECISION_DRIFT: [[Budget Solution]] — Jan meeting: "Use Vlocity", March meeting: "Custom Apex".
  ACTION: Update [[Decision: Budget Enforcement Approach]] with rationale for change.
  Ensure [[Can we use Vlocity for budget logic?]] is answered.
  ```

#### Link Density Issues
- **Detection**: Pages with too many or too few links (out of expected range)
- **Action**: Add cross-references or investigate why page is so isolated
- **Example Output**:
  ```
  LOW_DENSITY: [[Feature: Co-op Billing]] — Only 1 outgoing link. Expected 2-5.
  ACTION: Link to [[Co-op Billing Gap]], [[Decision: Co-op Billing Approach]], related meetings.
  ```

### Lint Run Output

Create a dated lint log file (`wiki/_schema/LINT_LOG.md`). Add new run results to the top; keep historical results below.

**Sample Lint Report**:
```markdown
# Lint Run — 2024-04-05

**Date**: 2024-04-05
**Scope**: All wiki/clients/ pages
**Total Pages**: 145
**Health Score**: 92% (excellent; target: >90%)

## Issues Found (8 total)

### Contradictions (1)
- [[Budget Management]] — Assessment mismatch between 2024-03-15 and 2024-04-10 meetings
  - **Action**: Update feature page with reconciliation

### Orphans (2)
- [[Legacy Reporting System]] (entity) — No features/decisions link to it
- [[Unused Integration Placeholder]] (integration) — Created but never populated
  - **Action**: Review and deprecate if obsolete

### Stale (3)
- [[Purchase Order Routing]] (feature) — Updated 2024-03-15, 3 new meetings since
- [[Inventory Sync]] (integration) — Updated 2024-03-20, 2 new meetings
- [[Tax Compliance Gap]] (gap) — Updated 2024-03-25, 1 new meeting
  - **Action**: Refresh these pages within 2 days

### Missing Cross-Refs (5)
- [[Dynamic Pricing]] (feature) — No linked gap page despite being mentioned as limitation in 2 meetings
- [[Real-time Sync Gap]] — No linked decision page
- [[Payment Tokenization Question]] — No decision or integration link
- [[CFO Stakeholder]] (entity) — No linked decisions despite being decision owner
- [[Oracle ERP Integration]] (integration) — No linked feature dependencies
  - **Action**: Create missing pages or add links

### P0 Overdue (2)
- [[Can SFCC handle 10M SKUs?]] — Due 2024-03-20, 16 days overdue. Owner: [Name]
- [[What's total LOE for custom dev?]] — Due 2024-04-01, 4 days overdue. Owner: [Name]
  - **Action**: Escalate immediately

### Decision Drift (1)
- [[Budget Solution]] — Jan meeting: "Use Vlocity", March: "Custom Apex". No documented rationale for change.
  - **Action**: Update decision page with transition narrative

## Recommendations (Priority Order)

1. **P0 Escalation** (URGENT): Reach out to question owners for [[Can SFCC handle 10M SKUs?]] and [[Total LOE?]]
2. **Refresh 3 Stale Pages**: [[Purchase Order Routing]], [[Inventory Sync]], [[Tax Compliance Gap]]
3. **Create Missing Pages**: [[Dynamic Pricing Gap]], [[Budget Solution]] (updated), [[Payment Tokenization]] decision
4. **Reconcile Contradiction**: [[Budget Management]] — meet with team
5. **Deprecate Orphans**: Confirm [[Legacy Reporting System]] no longer relevant

## Health Metrics

| Metric | Value | Status |
|--------|-------|--------|
| Total Pages | 145 | ✓ Growing |
| Avg Links/Page | 3.2 | ✓ Good (target: 2-5) |
| Orphan Pages | 2 | ✓ Low (target: <5) |
| Cross-Ref Coverage | 98% | ✓ Excellent (target: >95%) |
| Stale Pages (>1 week) | 3 | ⚠ Moderate (target: <2) |
| P0 Overdue Questions | 2 | ⚠ High (target: 0) |
| Contradictions | 1 | ✓ Low (target: 0) |

**Health Score Calculation**: (145 pages - 8 issues) / 145 = 92%

## Next Steps

- **Next Lint Run**: 2024-04-12 (1 week, before design review meeting)
- **Before Next Run**: Refresh stale pages, escalate overdue questions, create missing cross-refs
- **Quarterly Review**: Schedule deeper audit for April 25 (end of Q2)
```

---

## Page Lifecycle

### Creation

**Trigger**: New page needed during ingest workflow or query promotion

**Steps**:
1. Determine page type (feature, gap, decision, meeting, question, entity, integration)
2. Choose file location and name (kebab-case, descriptive)
3. Create frontmatter with required fields:
   - `type`, `client`, `status`, `created`, `updated`, `sources`, `tags`
4. Add structure sections appropriate to type
5. Add at least 1 outgoing link to related page (to avoid immediate orphan status)
6. Update `wiki/_index.md` to register new page
7. Log creation in `wiki/_log.md`

### Updates

**Trigger**: New meeting, decision, or evidence

**Steps**:
1. Open existing page
2. Update `updated` date to today
3. Add new evidence, links, or context to relevant sections
4. Update frontmatter `sources` if new source added
5. Add links to any newly created related pages
6. Optionally add entry to page's "Review History" or "Meeting History" section
7. Log update in `wiki/_log.md` (aggregate multiple updates into one log entry per day)

### Deprecation

**Trigger**: Feature/integration no longer relevant; replaced by newer page; or business decision to retire

**Steps**:
1. Update `status` field to `deprecated`
2. Add note at top of page explaining why (e.g., "Superseded by [[New Feature]]") and when
3. Keep all content intact (for historical reference)
4. Update any pages linking to deprecated page (point links to successor)
5. Log deprecation in `wiki/_log.md`

### Archival

**Trigger**: End of engagement; client no longer active; or decision to archive old client knowledge

**Steps**:
1. Move client folder to `wiki/archived/` (e.g., `wiki/archived/boston-beer-company/`)
2. Mark all pages in archived folder with `status: archived` in frontmatter
3. Update `wiki/_index.md` to show archived status
4. Remove references from platform pages (`wiki/platforms/`) but keep decision/pattern pages
5. Log archival event in `wiki/_log.md`

---

## Cross-Referencing Rules

Interconnection is the soul of the Verndale wiki. Every page must explicitly link to related pages using Obsidian-style wiki-links.

### Link Syntax

```markdown
[[Page Name]]              # Basic link to another page
[[Page Name|Custom Text]]  # Link with custom display text
[[../other-page]]          # Relative path (less common)
```

### Expected Link Patterns by Type

**Features ↔ Gaps**:
- Every feature should link to its gaps. If fully OOTB, state "No gaps identified."
- Every gap should link back to the feature it affects

**Gaps ↔ Decisions**:
- Every gap should link to its resolution approach (decision, question, or workaround)
- Every decision should link back to the gaps/questions that motivated it

**Decisions ↔ Questions**:
- Every decision should link to the question(s) it answers
- Every question should link to the decision(s) that resolved it (if answered)

**Meetings ↔ All Artifacts**:
- Every meeting page should link to entities, features, gaps, questions, decisions discussed
- Artifacts should link back to meetings where they were discovered or discussed

**Entities ↔ Features/Integrations**:
- Every entity (legacy system, vendor, person) should link to features it relates to
- Features and integrations should link to the entities they depend on

### Link Density Expectations

- **Entity pages**: 3-10 outgoing links (to features, integrations, decisions)
- **Feature pages**: 2-5 links (to gaps, decisions, meetings)
- **Gap pages**: 1-3 links (to features, decisions, questions)
- **Decision pages**: 2-4 links (to questions, features, meetings)
- **Meeting pages**: 5+ links (to entities, features, gaps, questions)
- **Question pages**: 1-3 links (to features, gaps, decisions)

High link density enables LLM traversal and pattern discovery. Orphaned pages (no incoming/outgoing links) are lint warnings.

### Link Checking

The lint workflow flags:
- **Broken links**: Target page doesn't exist
- **Orphan pages**: No incoming or outgoing links
- **Missing expected links**: Gap with no decision; feature with no gap (when gaps exist)

---

## Naming Conventions Quick Reference

### File Names (kebab-case)
- Format: `lowercase-hyphenated`, max 60 characters
- Examples:
  - ✓ `budget-management.md`
  - ✓ `virtual-warehouse-inventory.md`
  - ✓ `can-sfcc-handle-10m-skus.md`
  - ✗ `Budget_Management_Feature_Page.md` (wrong case, underscores)
  - ✗ `q.md` (too vague)

### Client Slugs (lowercase-hyphenated)
- Examples: `boston-beer-company`, `acme-corp-reseller`, `heartland-foodservice`

### Platform Slugs (lowercase-hyphenated)
- Examples: `salesforce-b2b-commerce`, `salesforce-lightning`, `oracle-netsuite`

### Meeting File Names ({YYYY-MM-DD}-{type}.md)
- Examples:
  - `2024-03-15-discovery.md`
  - `2024-04-10-design-review.md`
  - `2024-05-01-stakeholder-alignment.md`

### Tags (lowercase-hyphenated, optionally category-prefixed)
- Feature tags: `#feature/budget-enforcement`, `#feature/custom-dev`
- Gap tags: `#gap/critical`, `#gap/high-priority`, `#gap/workaround`
- Decision tags: `#decision/pending`, `#decision/approved`, `#decision/architecture`
- Integration tags: `#integration/batch-job`, `#integration/real-time`
- Domain tags: `#commerce`, `#supply-chain`, `#compliance`
- Status tags: `#blocked`, `#urgent`, `#stakeholder-alignment`

---

## Maintenance Cadence

### Daily

- **Ingest new content** as it arrives (meeting transcripts, emails, Confluence sync)
  - Create/update meeting pages
  - Extract features, gaps, questions
  - Log ingest activity
  - Estimated time: 30-60 minutes per meeting

### Weekly (Friday or Weekly Review)

- **Run lint checks** across all active client pages
  - Check for contradictions, orphans, stale pages, missing cross-refs
  - Flag overdue questions
  - Generate LINT_LOG entry
  - Estimated time: 30-45 minutes

- **Review queries and promote where valuable**
  - Identify answered questions that could become wiki pages
  - Create promoted pages with sources and links
  - Log promotions in activity log
  - Estimated time: 15-30 minutes

### Bi-Weekly (Every 2 Weeks, e.g., Before Decision Gate Meetings)

- **Reconciliation pass**: Ensure all meeting outputs are fully ingested
  - Check for any missed features, gaps, or questions
  - Verify contradictions are flagged and documented
  - Update decision pages with latest approvals and status changes
  - Estimated time: 45-90 minutes per client

### Monthly (Or Before Key Milestones)

- **Deep audit**: Health assessment and planning for next month
  - Review overall health score (target: >90%)
  - Identify patterns in overdue questions, decision drift, stale pages
  - Plan deprecations or archival of obsolete pages
  - Update `wiki/_index.md` with comprehensive metrics
  - Generate monthly summary in `wiki/_log.md`
  - Estimated time: 2-3 hours

### Quarterly (End of Each Quarter)

- **Strategic review**: Archive completed clients; consolidate platform patterns
  - Archive client folders if engagement complete
  - Identify reusable platform-level knowledge from completed engagements
  - Create or update `wiki/platforms/salesforce-b2b-commerce/` patterns and templates
  - Publish quarterly metrics and health summary
  - Estimated time: 4-6 hours

### As-Needed

- **Urgent reconciliation**: When contradictions discovered or major decisions change
  - Investigate root cause
  - Update all affected pages
  - Create decision page documenting change
  - Escalate if stakeholder alignment needed

---

## Workflows at a Glance

| Event | Frequency | Estimated Time | Responsible |
|-------|-----------|-----------------|------------|
| Meeting ingest | As meetings occur | 30-60 min | LLM or analyst |
| Email/document update | As received | 15-30 min | LLM or analyst |
| Query + synthesis | On-demand | 10-30 min | LLM or human |
| Query + promotion | On-demand | 30-60 min | LLM or analyst |
| Lint check (weekly) | Every Friday | 30-45 min | LLM or analyst |
| Lint check (before milestone) | Before key meetings | 30-45 min | Project manager |
| Bi-weekly reconciliation | Every 2 weeks | 45-90 min | Lead analyst |
| Monthly audit | Monthly | 2-3 hours | Project lead |
| Quarterly review | Quarterly | 4-6 hours | Director |

---

## Quality Criteria

### Page Quality Checklist

Every page should have:

- [ ] Complete frontmatter (type, client, status, created, updated, sources, tags)
- [ ] Clear, descriptive title (matches file name)
- [ ] 2-5 outgoing links (to related pages)
- [ ] At least 1 incoming link (from another page)
- [ ] Evidence-based statements (traceable to sources)
- [ ] No orphaned sections (all sections mentioned in body)
- [ ] Last updated within relevant time window (daily for decisions, weekly for features, monthly for platforms)

### Wiki Health Targets

| Metric | Target |
|--------|--------|
| Overall health score | >90% |
| Pages with proper frontmatter | 100% |
| Avg outgoing links/page | 2-5 (by type) |
| Orphan pages | <5% |
| Cross-ref coverage | >95% |
| Stale pages (>2 weeks old) | <10% |
| P0 overdue questions | 0 |
| Contradictions (unreconciled) | 0 |
| Broken links | 0 |

### Escalation Thresholds

- **Health score drops below 85%**: Schedule urgent audit
- **>3 P0 overdue questions**: Escalate to stakeholders immediately
- **>5 unreconciled contradictions**: Block further ingest until reconciled
- **>10% stale pages**: Schedule comprehensive refresh
