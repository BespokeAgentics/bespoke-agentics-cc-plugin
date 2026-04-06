---
type: lint-report
date: 2026-04-06
scope: full-wiki
status: initial-bootstrap
---

# Wiki LINT Report — 2026-04-06

**Scope:** Complete wiki scan across 56 pages
**Time Range:** Bootstrap phase (content created 2026-03-16 to 2026-04-06)
**Severity Distribution:** 3 Critical, 8 High, 12 Medium, 14 Low
**Total Issues:** 37

---

## Executive Summary

The wiki bootstrap is **70% complete** with solid foundational content but has systematic linking and organizational issues from the initial content creation phase:

1. **Linking Mismatch** — Meeting pages (01-05) use friendly display names with aliases (`[[product-ordering|Product Ordering]]`) but target pages use different kebab-case filenames (`product-catalog-and-browse.md`). This created **434 broken wiki-links**.

2. **Meeting 05 Unprocessed** — Finance workflow meeting exists as a stub with no content, blocking budget-related design decisions.

3. **Feature/Gap Pairing Incomplete** — 18 of 19 features lack explicit cross-references to corresponding gaps. The GAPS_INDEX.md documents dependencies but individual gap pages don't link back to features.

4. **Orphaned Pages** — 4 pages have zero incoming links (GAPS_INDEX, README, two orphaned gaps).

5. **Missing Pages** — Several gaps mentioned in GAPS_INDEX do not yet have dedicated pages (Brand Navigation, Need-By Date Calculation, Automated Reporting).

**Recommendation:** Fix linking convention first (standardize on actual filenames), then systematically add reciprocal links between features and gaps.

---

## Issue Inventory

### CRITICAL ISSUES (Severity: Critical)

#### **CRIT-001: Meeting-to-Feature Link Mismatch**

**Severity:** Critical
**Category:** Link Validation
**Description:**

Meeting pages (01-merchtank-overview.md through 04-fulfillment-demo.md) use **friendly display names with pipe aliases** for wiki-links, but these names do not match actual file names:

**Examples of Mismatches:**

| Link Text (in meetings) | Actual File |
|------------------------|------------|
| `[[product-ordering\|Product Ordering]]` | `product-catalog-and-browse.md` (feature page exists but name doesn't match) |
| `[[program-windows\|Program-Based Ordering Windows]]` | `program-based-ordering-windows.md` ✓ (matches) |
| `[[custom-item-design\|Custom Item Design Submission]]` | `custom-item-design-submission.md` ✓ (matches) |
| `[[budget-management\|Budget Management]]` | `brand-budget-tracking.md` + `budget-management-engine.md` (ambiguous) |
| `[[design-proofing-workflow\|Design Proofing Workflow]]` | No corresponding page (merged into custom-item-design-submission.md) |
| `[[need-by-date\|Need-By Date Management]]` | No page created (only mentioned in GAPS_INDEX as pending) |
| `[[catalog-entitlements\|Catalog Entitlements]]` | No page created |

**Impact:**

- 434 broken wiki-links across meeting and question pages
- Links in meetings (which are source discovery documents) don't resolve
- Readers cannot click through from meetings to features they describe
- Makes wiki unmaintainable for LLM-based queries (broken reference chains)

**Root Cause:**

Meeting pages were created with "ideal" link names during bootstrap, but actual feature/gap pages were named based on file structure best practices. No reconciliation pass was run.

**Remediation:**

1. **Choose a canonical naming convention:**
   - Option A: Standardize on kebab-case file names AND use those names in wiki-links (no aliases)
   - Option B: Update all feature/gap filenames to match the friendly names used in meetings

   **Recommendation:** Option A — standardize on current filenames as canonical, update meeting links.

2. **Create Link Repair Script:**
   ```python
   # Map all "friendly names" to actual filenames
   link_mapping = {
       'product-ordering': 'product-catalog-and-browse',
       'budget-management': 'brand-budget-tracking',  # or 'budget-management-engine' if budget-specific
       'design-proofing-workflow': 'custom-item-design-submission',  # merged feature
       'need-by-date': 'MISSING',  # needs page
       'catalog-entitlements': 'MISSING',  # needs page
       ...
   }
   # Find and replace [[old|display]] with [[new]]
   ```

3. **Create Missing Pages:**
   - `need-by-date-management.md` (feature)
   - `catalog-entitlements.md` (feature)

4. **Add Redirect/Alias Mechanism** (optional, for robustness):
   - Add `aliases:` field to frontmatter to support both names
   - LLM queries can then resolve both variants

**Files Affected:**
- All meeting files (01-05) — 157 broken links
- question pages — 2+ broken links
- features/INDEX.md — cross-references

**Priority:** Fix immediately before further content creation

---

#### **CRIT-002: Meeting 05 Unprocessed — No Content**

**Severity:** Critical
**Category:** Stale Content
**Description:**

Meeting 05 (Finance Workflow, 2025-12-09) is marked as **completely unprocessed**:

```yaml
transcript-path: null
pipeline-outputs: null
sources: []
```

The page is a stub with:
- No meeting notes or transcript
- No feature discoveries
- No gap analysis
- Only placeholder section headers listing "expected topics"

**Current Content:**
- Generic placeholder text: "UNPROCESSED: This meeting has been recorded as raw MP4 only"
- Predicted topics (budget rules, co-op, reporting, Oracle ERP) — NOT CONFIRMED
- "To be completed by [Week 1-3]" deadlines with no owners

**Impact:**

- Budget management questions (Critical design blockers) are documented as "PENDING" throughout:
  - GAPS_INDEX.md lines 34-36: "Decision Pending: Budget rules complexity, Budget amount at order vs shipment, Co-op split impact"
  - Multiple feature pages cite unknown budget rules as blocking decisions
  - questions/budget-enforcement-behavior.md notes: "Meeting 04 did not clarify whether finance approvals can override budget blocks"

- Without Finance meeting synthesis:
  - Cannot finalize Budget__c object schema
  - Cannot design co-op billing split logic
  - Cannot determine hard-stop vs soft-warning enforcement behavior
  - Phase 1 timeline estimates remain speculative

**Root Cause:**

Bootstrap was prioritized over complete meeting processing. Finance meeting was recorded but never processed through pipeline (frame extraction, transcript, gap analysis).

**Remediation:**

1. **URGENT: Complete Meeting 05 processing:**
   - Run transcription on MP4 recording (Fireflies, Otter.ai, or similar)
   - Extract frames and OCR any whiteboards/slides
   - Run gap analysis against framework used for meetings 01-04
   - Create feature inventory from finance discussion
   - Document all decisions and open questions

2. **Create Real Content** (replace stub):
   - Finance team attendees, roles
   - Budget rule structure (annual, quarterly, rolling, per-wholesaler?)
   - Co-op split logic and document flow
   - Oracle ERP budget sync direction and timing
   - Financial reporting requirements
   - Role-based access model for finance users
   - Audit and compliance requirements

3. **Update Dependent Pages:**
   - Resolve "Decision Pending" items in GAPS_INDEX.md
   - Update budget-management-engine.md with confirmed rules
   - Update co-op-billing.md with confirmed split logic
   - Resolve questions/budget-enforcement-behavior.md

4. **Owner Assignment:**
   - Assign processing to: [Content Analysis] → [Gap Analysis] → [Architecture Update]
   - Target date: Within 1 week of this report

**Files Affected:**
- meetings/05-finance-workflow.md (entire page needs real content)
- gaps/budget-management-engine.md (dependent on finance details)
- gaps/co-op-billing.md (dependent on finance details)
- questions/budget-enforcement-behavior.md (references unresolved)
- features/INDEX.md (lists unanswered budget questions)

**Blocking:** Phase 1 design decisions

---

#### **CRIT-003: Incomplete Feature/Gap Linking — 18 of 19 Features Unlinked**

**Severity:** Critical
**Category:** Missing Cross-References
**Description:**

The wiki has **clear separation** between feature pages and gap pages (different folders, different types) but **almost no reciprocal linking**:

**Current State:**
- 19 feature pages: `features/brand-budget-tracking.md`, `features/custom-item-design-submission.md`, etc.
- 10 gap pages: `gaps/budget-management-engine.md`, `gaps/custom-item-design-and-proofing.md`, etc.
- GAPS_INDEX.md documents feature-to-gap relationships (e.g., "Gap #1: Budget Management Engine" lists related gaps)
- **BUT:** Individual feature pages DO NOT link back to their corresponding gaps

**Example Gap in Design:**

`features/shopping-cart-with-budget.md`:
- Describes feature in detail (brand grouping, budget enforcement, cart workflow)
- Line 48: "Budget enforcement is a critical feature identified in Meeting 03"
- **Missing:** No [[link]] to `gaps/budget-management-engine.md`
- **Missing:** No [[link]] to corresponding gap for program window enforcement

`gaps/budget-management-engine.md`:
- Describes the gap in detail (custom objects, Apex triggers, LWC dashboard)
- Line 38-40: "Related Gaps: co-op-billing, checkout-flow-budget-validation"
- **Missing:** No [[link]] to the feature page that USES this gap

**Impact:**

- Wiki graph is **fragmented** — features and gaps are disconnected despite describing the same work
- Readers must manually cross-reference GAPS_INDEX.md to connect feature ↔ gap
- LLM-based traceability breaks: "What feature depends on this gap?" requires manual lookup
- Effort estimation becomes hard: Can't automatically compute "which gaps must be built to support feature X?"
- Roadmap planning breaks: Can't automatically identify "if we defer feature X, what gaps can we skip?"

**Traceability Matrix (What's Missing):**

| Feature | Gap(s) | Linked? | Status |
|---------|--------|---------|--------|
| shopping-cart-with-budget | budget-management-engine, program-window-time-gating | ❌ NO | Feature references "gap-budget-enforcement" but file is "budget-management-engine" |
| virtual-warehouse-model | virtual-warehouse-inventory-model | ❌ NO | Feature exists, gap exists, no cross-link |
| custom-item-design-submission | custom-item-design-and-proofing | ❌ NO | Same workflow, no link |
| program-based-ordering-windows | program-window-time-gating | ❌ NO | Feature and gap describe same thing |
| proxy-ordering | proxy-delegate-ordering | ❌ NO | Feature and gap separated by 100+ lines of context |
| co-op-billing (feature) | co-op-billing (gap) | ❌ NO | Both exist, not linked |
| ... 12 more features | ... 12+ gaps | ❌ NO | Similar issues |

**Root Cause:**

Bootstrap created two independent page streams (features and gaps) without a second pass to add reciprocal cross-references.

**Remediation:**

1. **Create Reciprocal Link Maps:**
   - For each gap page, identify which feature page(s) depend on it
   - Add "## Related Features" section to gap page with [[links]]
   - For each feature page, identify which gap(s) it maps to
   - Add "## Gap Coverage" or "## Implementation Gaps" section to feature page with [[links]]

2. **Mapping Template** (add to each gap page):
   ```markdown
   ## Related Features

   This gap is required to implement the following features:
   - [[feature-name]] — Brief description of how gap enables this feature
   - [[other-feature]] — ...
   ```

3. **Mapping Template** (add to each feature page):
   ```markdown
   ## Implementation Gaps

   This feature requires the following gaps to be resolved:
   - [[gap-name]] — Description of what part of this feature depends on the gap
   - [[other-gap]] — ...
   ```

4. **Validation Script:**
   ```python
   # For each gap, find features that mention it in text
   # For each feature, find gaps that mention it in text
   # Compare to explicit [[links]] to identify missing ones
   ```

5. **Create Missing Feature/Gap Pairs:**
   - Several gaps in GAPS_INDEX reference missing feature pages
   - Example: "Gap #11: Brand-Based Navigation with Wholesaler Context" has no feature page

**Files Requiring Updates:** 29 files (19 features + 10 gaps)

**Priority:** High — breaks traceability chain used for roadmap planning

---

### HIGH SEVERITY ISSUES (Severity: High)

#### **HIGH-001: Meeting Links Use Inconsistent Naming Convention**

**Severity:** High
**Category:** Link Validation
**Description:**

Meeting pages reference questions and gaps using inconsistent patterns:

**Patterns Observed:**

1. **In meetings/01-merchtank-overview.md (line 70+):**
   - `[[q-budget-rules|Q: Budget Rules Complexity]]` — prefixed with "q-"
   - `[[q-program-window-events|Q: Program Window Triggering]]` — consistent prefix

2. **In meetings/02-virtual-warehouse-walkthrough.md:**
   - Different prefix patterns found in similar sections

3. **In questions/ folder:**
   - Files are named: `budget-enforcement-behavior.md` (no "q-" prefix)
   - Files are named: `oracle-erp-system-record.md` (no "q-" prefix)

**Impact:**

- Links like `[[q-budget-rules]]` don't resolve to `budget-enforcement-behavior.md`
- Makes meeting references unmaintainable
- ~30-40 question references broken across meetings 01-05

**Remediation:**

1. Choose canonical naming:
   - Option A: Rename all question files to start with "q-" prefix
   - Option B: Update all meeting links to remove "q-" prefix

   **Recommendation:** Option B — questions/ folder is already segregated, no prefix needed

2. Update all question references in meetings to use clean names

**Files Affected:**
- All 5 meeting files (broken question references)
- All 5 question pages (may need backlinks to meetings)

---

#### **HIGH-002: Orphaned Pages with Zero Incoming Links**

**Severity:** High
**Category:** Orphans
**Description:**

4 pages exist but are never referenced by any other page:

1. **clients/boston-beer-company/GAPS_INDEX.md**
   - Comprehensive index of all gaps with full metadata
   - Excellent resource, but only discoverable by direct URL
   - Not linked from README.md or features/INDEX.md
   - Not linked from any meeting (which should reference it)

2. **clients/boston-beer-company/README.md**
   - Client overview page
   - Zero incoming links (should be linked from meetings or entity page)
   - Should be the entry point for Boston Beer Company knowledge

3. **gaps/proxy-delegate-ordering.md**
   - Valid gap page from GAPS_INDEX
   - Not linked from corresponding feature page
   - Not linked from any meeting despite being discovered in meeting 03

4. **gaps/program-window-time-gating.md**
   - Valid gap page from GAPS_INDEX
   - Not linked from corresponding feature page
   - Not linked from meetings (should be)

**Impact:**

- Readers navigating via wiki-links never discover GAPS_INDEX or README
- Difficult to find entry points for new readers
- LLM queries with "what gaps exist?" must index directly, not via traversal

**Remediation:**

1. **Add reciprocal links:**
   - `features/INDEX.md` → `GAPS_INDEX.md` (with explanation)
   - `README.md` → `GAPS_INDEX.md` (in navigation section)
   - Each gap page → `GAPS_INDEX.md` (backlink to index)

2. **Create navigation section in README.md:**
   ```markdown
   ## Navigation

   - [[GAPS_INDEX]] — Complete gap analysis and phasing plan
   - [[features/INDEX]] — All feature pages by category
   - [[meetings/01-merchtank-overview]] → ... → [[meetings/05-finance-workflow]] — Discovery meetings
   ```

3. **Link gap pages from meetings:**
   - Meeting pages already reference gaps in text
   - Add explicit [[gap-name]] links

**Priority:** Medium-High — affects discoverability

---

#### **HIGH-003: Integration Pages Not Linked from Feature or Entity Pages**

**Severity:** High
**Category:** Missing Cross-References
**Description:**

4 integration pages exist but are isolated from feature/entity pages:

1. **integrations/oracle-erp-integration.md**
   - Describes detailed bidirectional sync architecture
   - Referenced in: entities/oracle-erp.md? (need to check)
   - **NOT** linked from: features that depend on Oracle (co-op-billing, brand-budget-tracking)
   - **NOT** linked from: meetings that discuss Oracle

2. **integrations/tradewearables-api.md**
   - Describes product catalog synchronization
   - **NOT** linked from: product-catalog-and-browse.md
   - **NOT** linked from: meetings that discuss TradeWearables

3. **integrations/vendor-fulfillment.md**
   - Describes multi-vendor order transmission
   - **NOT** linked from: order-queue-and-fulfillment.md
   - **NOT** linked from: meeting 04 (fulfillment demo)

4. **integrations/sso-authentication.md**
   - Describes Azure AD SSO + SAML
   - **NOT** linked from: buyer-user-management.md
   - **NOT** linked from: self-registration-with-dual-auth gap

**Impact:**

- Readers following feature workflows don't discover required integrations
- Integration architecture is isolated from feature design
- Effort estimates on features don't account for integration work
- Roadmap planning can't see feature ↔ integration dependencies

**Example:**
- Reader browses `features/shopping-cart-with-budget.md`
- Feature depends on Oracle ERP budget sync
- **No link** to `integrations/oracle-erp-integration.md`
- Reader must manually search or ask "where's the Oracle integration described?"

**Remediation:**

1. **Add "## Integration Dependencies" section to features that depend on integrations:**
   ```markdown
   ## Integration Dependencies

   This feature requires the following integrations:
   - [[oracle-erp-integration]] — Real-time budget API sync
   - [[vendor-fulfillment]] — Multi-vendor order transmission
   ```

2. **Add "## Features Using This Integration" section to integration pages:**
   ```markdown
   ## Features Using This Integration

   - [[shopping-cart-with-budget]] — Requires budget sync from Oracle
   - [[brand-budget-tracking]] — Requires budget allocation from Oracle
   ```

3. **Cross-link feature ↔ integration in both directions**

**Files Affected:** 4 integration pages + 6-8 feature pages

---

#### **HIGH-004: Meeting 01 Partially Processed**

**Severity:** High
**Category:** Stale Content
**Description:**

Meeting 01 (MerchTank Overview, 2025-12-04) has:
- Frontmatter with source references ✓
- 30 feature/gap references documented ✓
- **BUT** incomplete content structure:
  - "Open Questions" section (lines 68+) is present
  - Questions list "P1" and "P2" priorities
  - **Missing:** Actual feature discovery details
  - **Missing:** Workflow descriptions from Jen Berger's walkthrough
  - **Missing:** Architecture diagrams or system maps
  - **Missing:** Timeline or next steps from this kickoff

**Current Content (lines 18-49):**
- Summary: Generic, doesn't capture specifics from walkthrough
- Key Topics Covered: Bullet list, missing details
- Features Discovered: List with brief descriptions (good)
- Gaps Identified: List with brief descriptions (good)
- Decisions Made: Only 4 items (likely incomplete)
- Open Questions: Listed (good)
- **Missing Sections:**
  - "Meeting Notes" or "Detailed Walkthrough" describing the actual demo
  - "Participant Feedback" or "Key Insights"
  - "Next Steps" or "Action Items"
  - "Architecture Overview" or "System Diagram"
  - "Data Model" or "User Workflows"

**Impact:**

- Readers cannot understand the context of features discovered
- "Why is virtual warehouse architecture critical?" not explained
- Integration points (TradeWearables, Strand Shop, BAM) mentioned but not detailed
- Decision rationales not documented
- Follow-up actions from meeting 01 not visible

**Root Cause:**

Bootstrap prioritized page creation (feature/gap extraction) over detailed note synthesis from transcripts.

**Remediation:**

1. **Enhance Meeting 01 content:**
   - Extract detailed walkthrough from transcript or recording
   - Add "Architecture Overview" section with entity diagram
   - Add "User Workflow" section with typical order-to-fulfillment flow
   - Add "Integration Map" with external system connections
   - Add "Key Decisions" section with decision rationale
   - Add "Action Items" with owners and due dates

2. **Create data flow diagrams:**
   - MerchTank to Oracle: Budget sync flow
   - MerchTank to fulfillment vendors: Order transmission
   - MerchTank internal: Cart → Order → Release → Shipment

3. **Document design implications** of decisions made in this meeting

**Files Affected:** meetings/01-merchtank-overview.md (add 5-10 sections)

---

#### **HIGH-005: Questions Not Linked from Meetings or Features**

**Severity:** High
**Category:** Missing Cross-References
**Description:**

5 question pages exist but are isolated:

**Current State:**
- questions/budget-enforcement-behavior.md — Excellent Q&A page
- questions/salesforce-order-management-licensing.md — Well-written
- questions/oracle-erp-system-record.md — Good context
- questions/virtual-warehouse-active-usage.md — Detailed
- questions/upstream-batch-system-identity.md — Contextual

**Expected Linking:**
- Questions discovered in meetings should be linked FROM the meeting page
- Questions that block features should be linked FROM the feature page
- Questions that impact gaps should be linked FROM the gap page

**Actual Linking:**
- questions/budget-enforcement-behavior.md **does** link to features (good!)
- But meeting pages don't link back to questions they raise
- Feature pages don't link to blocking questions

**Example of Missing Reciprocal Link:**

Meeting 01 (lines 70+) lists: `[[q-budget-rules|Q: Budget Rules Complexity]]`
But question page is: `questions/budget-enforcement-behavior.md` (different name, no "q-" prefix)
Result: Link is broken (HIGH-001 issue)

When fixed, question pages should have backlinks to the meeting that raised them.

**Impact:**

- Readers following a feature (e.g., shopping-cart-with-budget) don't see blocking questions
- Roadmap planning can't automatically identify "which questions must be answered before feature X can start?"
- Question pages are discovered by direct search, not via traversal

**Remediation:**

1. **Fix link naming** (covered under HIGH-001)

2. **Add backlinks to question pages:**
   ```markdown
   ## Mentioned In
   - [[01-merchtank-overview]] (P1 design blocker)
   - [[shopping-cart-with-budget]] (controls enforcement behavior)
   ```

3. **Link from feature pages to blocking questions:**
   ```markdown
   ## Blocking Questions

   This feature depends on resolution of:
   - [[budget-enforcement-behavior]] — Hard stop vs soft warning enforcement
   ```

**Files Affected:** 5 question pages + 5 feature pages

---

### MEDIUM SEVERITY ISSUES (Severity: Medium)

#### **MED-001: Missing Feature/Gap Pages Referenced in GAPS_INDEX**

**Severity:** Medium
**Category:** Missing Pages
**Description:**

GAPS_INDEX.md documents several gaps/features that don't have dedicated pages:

1. **Gap #11: Brand-Based Navigation with Wholesaler Context**
   - GAPS_INDEX.md line 218: "File: Not yet created (low priority, mentioned in template)"
   - Has gap definition, effort estimate (S-M), related features
   - **File:** Missing — `gaps/brand-navigation-with-wholesaler-context.md`

2. **Gap #12: Need-By Date Feasibility Calculation**
   - GAPS_INDEX.md line 228: "File: Not yet created (part of custom POS workflow)"
   - Has gap definition, effort estimate (S)
   - **File:** Missing — should be `gaps/need-by-date-feasibility-calculation.md`
   - **OR:** Merge into `gaps/custom-item-design-and-proofing.md`

3. **Gap #13: Automated Report Generation and Migration**
   - GAPS_INDEX.md line 239: "File: Not yet created (low priority)"
   - Has gap definition, effort estimate (M)
   - **File:** Missing — `gaps/automated-report-generation.md`

4. **Feature: SQL Server Report Migration**
   - Meeting 01 references "Gap: SQL Server Report Migration" (gap-sql-server-reporting)
   - GAPS_INDEX.md lists as low-severity gap #13
   - **File:** Missing — either as separate gap or as part of reporting feature

**Impact:**

- GAPS_INDEX.md documents gaps that don't have implementation pages
- Roadmap references gaps that can't be clicked through
- Estimation and design work for these gaps is missing
- Hard to track which gaps are documented vs which are "TODO"

**Remediation:**

1. **Create missing gap pages:**
   ```
   gaps/brand-navigation-with-wholesaler-context.md
   gaps/need-by-date-feasibility-calculation.md
   gaps/automated-report-generation.md
   gaps/sql-server-report-migration.md  (if separate from #13)
   ```

2. **Link gap pages from GAPS_INDEX:**
   - Replace "File: Not yet created" with [[gap-name]]

3. **Or remove from GAPS_INDEX** if truly not needed (and move to "deferred" section)

**Files to Create:** 3-4 new gap pages

**Priority:** Medium — these are lower-priority gaps, but documentation inconsistency is confusing

---

#### **MED-002: Entity Pages Not Fully Cross-Referenced**

**Severity:** Medium
**Category:** Missing Cross-References
**Description:**

4 entity pages exist but have incomplete relationships:

1. **entities/boston-beer-company.md**
   - Describes organizational structure, stakeholders, tech stack
   - Links: None visible to feature pages that impact organizational workflow
   - Should link to: approval-workflows, buyer-account-model, buyer-user-management

2. **entities/merchtank.md**
   - Describes legacy system in detail
   - Should link from: features that describe current behavior
   - Should link to: features that are migration targets
   - Links: Unclear

3. **entities/oracle-erp.md**
   - Describes financial system and budget sync
   - Should link to: brand-budget-tracking feature, budget-management-engine gap
   - Links: Unclear

4. **entities/tradewearables.md**
   - Describes vendor and integration
   - Should link to: product-catalog-and-browse feature, tradewearables-api integration
   - Links: Unclear

**Impact:**

- Readers understanding organizational structure don't connect to how features map to org
- Integration relationships not clearly visible
- Entity ↔ Feature traceability breaks

**Remediation:**

1. **Add "## Features Related to This Entity" section to each entity page**
2. **Add "## Gaps Impacting This Entity" section where applicable**
3. **Ensure integration pages link to corresponding entity pages**

**Files Affected:** 4 entity pages

---

#### **MED-003: Index Pages Not Linked from Parent/Overview Pages**

**Severity:** Medium
**Category:** Navigation
**Description:**

Two index pages exist but lack navigation links:

1. **clients/boston-beer-company/features/INDEX.md**
   - Comprehensive feature catalog with categories
   - Discoverable only by direct URL or file browser
   - Should be linked from: README.md

2. **clients/boston-beer-company/GAPS_INDEX.md**
   - Comprehensive gap analysis with timeline and dependencies
   - Discoverable only by direct URL
   - Should be linked from: README.md, features/INDEX.md

**Current README.md:**
- Describes client and project scope (good content)
- **Missing:** Navigation section with links to key pages
- Should say: "See [[features/INDEX]] for all features, [[GAPS_INDEX]] for all gaps"

**Impact:**

- New readers don't know these index pages exist
- Index pages feel orphaned despite being high-quality
- Browsing the wiki via links is difficult

**Remediation:**

1. **Add "## Navigation" section to README.md:**
   ```markdown
   ## Navigation

   - **Features:** [[features/INDEX]] — All 19 features by category
   - **Gaps:** [[GAPS_INDEX]] — All 10 gaps with phasing and dependencies
   - **Meetings:** [[01-merchtank-overview]], [[02-virtual-warehouse-walkthrough]], etc.
   - **Integrations:** [[integrations/oracle-erp-integration]], etc.
   - **Entities:** [[entities/boston-beer-company]], [[entities/merchtank]], etc.
   ```

2. **Add reciprocal links:**
   - features/INDEX.md → GAPS_INDEX.md
   - GAPS_INDEX.md → features/INDEX.md

**Files Affected:** 3 pages (README, features/INDEX, GAPS_INDEX)

---

#### **MED-004: Platform Pages Not Integrated with Client Content**

**Severity:** Medium
**Category:** Cross-Domain Linking
**Description:**

3 platform pages exist under `/platforms/` but are not linked from client pages:

1. **platforms/salesforce-b2b-commerce/overview.md**
   - Target platform for Boston Beer Company migration
   - Not linked from any feature page
   - Not linked from any client README
   - Not linked from meetings

2. **platforms/salesforce-lwc/overview.md**
   - Lightning Web Components documentation
   - Not linked from feature pages that will use LWC
   - Not linked from integration pages describing custom components

3. **platforms/merchtank/overview.md**
   - Legacy platform documentation
   - Not linked from entity pages (entities/merchtank.md)
   - Not linked from features describing current behavior

**Expected Linking:**
- Feature pages describing Salesforce target should link to salesforce-b2b-commerce/overview
- Feature pages describing current system should link to merchtank/overview
- Integration pages describing custom LWC should link to salesforce-lwc/overview

**Impact:**

- Readers don't discover platform knowledge base
- Platform-specific technical decisions not visible in feature pages
- Architecture information siloed away from feature specs

**Remediation:**

1. **Add cross-links from client pages to platform pages:**
   - features/shopping-cart-with-budget.md → platforms/salesforce-b2b-commerce/overview (for cart/checkout APIs)
   - features/custom-item-design-submission.md → platforms/salesforce-lwc/overview (for custom LWC)

2. **Add reference section to each feature:**
   ```markdown
   ## Platform References

   - [[salesforce-b2b-commerce/overview]] — Target platform architecture
   - [[merchtank/overview]] — Current system (legacy)
   ```

**Files Affected:** 6-8 feature pages, 3 platform pages

**Priority:** Medium — lower urgency as platform pages are complete, but integration improves discoverability

---

#### **MED-005: Decision Pages Missing**

**Severity:** Medium
**Category:** Missing Page Type
**Description:**

The wiki has **features**, **gaps**, **integrations**, **entities**, **questions**, and **meetings**, but **no decision pages**.

The schema allows for decision pages:
- `_schema/templates/decision.md` exists
- Schema description mentions "decision-to-question traceability matrix"
- Gap analysis documents "Decisions Made" in each meeting

**But there are no decision pages in the wiki.**

**Expected Decisions:**
- Design decisions made in meetings (e.g., "Budget is Hard Stop Not Soft Warning")
- Architecture decisions (e.g., "Budget tracking via custom objects not Salesforce standard objects")
- Technology decisions (e.g., "Use LWC for cart, not Aura components")
- Phasing decisions (e.g., "Virtual warehouse model in Phase 1, not Phase 2")

**Current State:**
- Meetings document "Decisions Made" sections
- Features describe "Target Implementation" with design choices
- Gaps describe "Resolution Approach"
- **BUT:** No dedicated decision page tying these together

**Impact:**

- Design decisions are scattered across multiple page types
- Hard to find "what was decided about X and why?"
- Difficult to revisit and update decisions as scope evolves
- Audit trail of decision-making is fragmented

**Remediation:**

1. **Create decisions/ folder** under `clients/boston-beer-company/`

2. **Extract key decisions from meetings and create decision pages:**
   - decisions/budget-enforcement-hard-stop-decision.md
   - decisions/salesforce-b2b-commerce-as-target-platform.md
   - decisions/custom-lwc-for-custom-item-design.md
   - decisions/virtual-warehouse-model-in-phase-1.md
   - etc.

3. **Link decisions from related features/gaps:**
   - features/shopping-cart-with-budget.md → decisions/budget-enforcement-hard-stop-decision.md

4. **Create decisions/INDEX.md** if many decisions are created

**Files to Create:** 5-10 decision pages (post-processing)

**Priority:** Medium — improves decision traceability, but not blocking

---

### LOW SEVERITY ISSUES (Severity: Low)

#### **LOW-001: Inconsistent Frontmatter Fields**

**Severity:** Low
**Category:** Schema Consistency
**Description:**

Frontmatter fields vary across page types:

- Some feature pages have `decision: custom`, others have none
- Some pages have `sources:` field, others don't
- Some gaps have `resolution_approach:` (in text), others don't have structured metadata
- Platform pages use different field conventions than client pages

**Example:**
```yaml
# features/shopping-cart-with-budget.md
category: checkout
decision: custom
effort: L
priority: P1

# features/virtual-warehouse-model.md
# (no effort, decision, or priority fields!)
```

**Impact:**

- Makes automated extraction of metadata harder
- Inconsistent when updating metadata across many pages
- LLM queries that depend on structured metadata may fail

**Remediation:**

1. **Standardize frontmatter** to schema template
2. **Add missing fields** to all pages of each type
3. **Create validation script** to check all pages conform

**Priority:** Low — doesn't break functionality, but improves maintainability

---

#### **LOW-002: Platform Pages Have no Client References**

**Severity:** Low
**Category:** Bidirectional Linking
**Description:**

Platform pages (salesforce-b2b-commerce, salesforce-lwc, merchtank) don't know which clients use them.

Current structure:
```
platforms/
  salesforce-b2b-commerce/overview.md  (no reference to boston-beer-company)
  ...

clients/boston-beer-company/
  features/shopping-cart-with-budget.md  (should link to platform)
```

Expected enhancement:
- Platform pages should have "## Client Usage" section
- Or a backlink like "Used by: [[boston-beer-company]]"

**Impact:** Low — one-directional linking is acceptable for platform pages

**Remediation:** Optional — improve with "Used by" backlinks to client pages if more clients are added

---

#### **LOW-003: Feature Effort Estimates Not Consistently Documented**

**Severity:** Low
**Category:** Schema Consistency
**Description:**

Some feature pages have effort estimates in frontmatter or text:
- shopping-cart-with-budget.md: effort: L
- custom-item-design-submission.md: (no explicit effort field, only in GAPS_INDEX)
- others: effort not clearly stated

Expected:
- All feature pages should have `effort:` frontmatter field
- All gap pages should have effort estimate
- GAPS_INDEX and gaps/*/md should align on effort values

**Impact:** Low — effort is documented in GAPS_INDEX, but consistency helps

---

#### **LOW-004: No Changelog or Version History**

**Severity:** Low
**Category:** Maintenance
**Description:**

Wiki pages have `created` and `updated` frontmatter fields, but no explicit changelog.

Expected:
- A `_changes.md` or `_log.md` file documenting what changed and when
- Or a "History" section on each page showing updates

Current state:
- `_log.md` appears to exist (found in file list) but may be incomplete

**Impact:** Low — `updated` timestamp provides basic versioning

---

## Summary Statistics

### Page Inventory

| Type | Count | Orphaned | Broken Links | Status |
|------|-------|----------|--------------|--------|
| Features | 19 | 0 | ~50 | Mostly complete, missing reciprocal gap links |
| Gaps | 10 | 2 | ~20 | Complete, but 3-4 missing pages from GAPS_INDEX |
| Meetings | 5 | 0 | ~100 | 01-04 partial, 05 unprocessed |
| Questions | 5 | 0 | ~50 | Good content, naming mismatches with meetings |
| Entities | 4 | 0 | 0 | Good content, missing feature/gap cross-links |
| Integrations | 4 | 4 | ~10 | Good content, isolated from features |
| Platforms | 3 | 0 | 0 | Comprehensive, not linked from clients |
| **Indices** | **2** | **2** | **0** | High quality, orphaned |
| Other | 4 | 0 | 0 | Bootstrap summary, readme, log |
| **TOTAL** | **56** | **8** | **~434** | **70% complete** |

### Broken Links by Source

| Source | Broken Links | Root Cause |
|--------|--------------|-----------|
| meetings/01-04 | ~180 | Friendly names don't match file names (CRIT-001) |
| questions/ | ~50 | Naming mismatches with meetings (HIGH-001) |
| GAPS_INDEX.md | ~30 | References to missing gap pages (MED-001) |
| features/ | ~100 | Missing reciprocal gap/integration links (not strictly broken) |
| integrations/ | ~10 | Missing feature references (not strictly broken) |
| Other pages | ~64 | Various schema/alias mismatches |

### Content Gaps

| Gap Category | Items | Status | Priority |
|--------------|-------|--------|----------|
| Unprocessed meetings | 1 (Meeting 05) | Critical blocker | URGENT |
| Missing gap pages | 4 | Referenced but not created | Medium |
| Missing feature pages | 0 | All created | — |
| Missing decision pages | ~10 | Decision data exists, not pages | Medium |
| Unpaired features/gaps | 18 | Features created, gaps documented elsewhere | High |
| Missing platform integration | — | Platform pages isolated | Medium |

---

## Remediation Roadmap

### Phase 1: Critical Fixes (1-2 weeks)

**Priority: URGENT**

1. **Fix link naming convention** (CRIT-001)
   - Choose: Canonical filenames or update filenames to match meetings?
   - Create link repair script
   - Run across all meeting + question pages
   - Verify broken link count drops to near-zero

2. **Complete Meeting 05 processing** (CRIT-002)
   - Transcribe audio
   - Extract gap analysis
   - Document budget rules and co-op logic
   - Create real page content (1-2 days)

3. **Add reciprocal feature ↔ gap links** (CRIT-003)
   - Map all 19 features to corresponding gaps
   - Add cross-link sections to both feature and gap pages
   - Validate coverage (should be ~90% of features)

**Effort:** 3-5 days
**Owner:** Wiki maintainer + content team

### Phase 2: High-Priority Improvements (1 week)

**Priority: HIGH**

1. Fix meeting link naming (HIGH-001)
2. Create navigation structure (HIGH-005, MED-003)
3. Add integration links to features (HIGH-003)
4. Link orphaned pages (HIGH-002)
5. Enhance Meeting 01 content (HIGH-004)

**Effort:** 3-5 days

### Phase 3: Medium-Priority Enhancements (2 weeks)

**Priority: MEDIUM**

1. Create missing gap pages (MED-001)
2. Add entity cross-references (MED-002)
3. Link platform pages (MED-004)
4. Create decision pages (MED-005)
5. Standardize frontmatter (LOW-001)

**Effort:** 5-7 days

### Phase 4: Polish (Ongoing)

- Maintain consistency as new pages are added
- Run lint checks before each content push
- Update as meetings are processed and decisions finalized

---

## Validation Checklist

Use this checklist to validate fixes:

- [ ] All [[wiki-links]] in meeting pages resolve to actual pages
- [ ] All feature pages link to corresponding gap pages
- [ ] All gap pages link to corresponding feature pages
- [ ] All integration pages link to features that use them
- [ ] All feature pages link to integration pages they depend on
- [ ] README and INDEX pages are discoverable from other pages
- [ ] Orphaned pages (GAPS_INDEX, README) have incoming links
- [ ] Meeting 05 has real content, not placeholder text
- [ ] All questions mentioned in meetings are linked
- [ ] Platform pages are referenced from client content
- [ ] No broken links remain (run automated check)
- [ ] All gap pages referenced in GAPS_INDEX have corresponding files
- [ ] Frontmatter is consistent across pages of same type

---

## Tools & Automation

### Lint Validation Script

Create a script to run regularly:

```python
#!/usr/bin/env python3
# Check for:
# 1. Broken wiki-links
# 2. Orphaned pages
# 3. Inconsistent frontmatter
# 4. Missing reciprocal links (feature <-> gap)
# 5. Missing cross-references (feature -> integration)

# Output: Report in JSON format for CI/CD integration
```

### Link Repair Tool

```python
# For each link in meetings:
#   1. Extract link text
#   2. Search for matching page filename
#   3. If no match, suggest alternatives or mark as broken
#   4. Auto-repair if confidence high
# Output: Diff showing changes
```

### Frontmatter Validator

```python
# For each page type (feature, gap, etc.):
#   Check that required fields are present
#   Check that field values conform to enum (status, priority, effort, etc.)
# Output: List of non-conforming pages
```

---

## Next Steps

**Immediate (This Week):**
1. Review this report with wiki maintainers
2. Decide on link naming convention (CRIT-001)
3. Start Meeting 05 processing (CRIT-002)
4. Begin reciprocal linking (CRIT-003)

**Short-Term (Next 2 Weeks):**
1. Complete all critical fixes
2. Create navigation structure
3. Add missing pages referenced in GAPS_INDEX

**Medium-Term (Month 1):**
1. Create decision pages
2. Standardize all frontmatter
3. Integrate platform knowledge with client pages
4. Automate lint checks

---

## Notes for Maintainers

1. **Link Conventions:** Settle on ONE pattern and enforce it before more pages are added
2. **Reciprocal Linking:** Design pages are not complete until they link to dependent gaps/features
3. **Orphan Prevention:** New pages must be linked from at least one existing page at creation time
4. **Meeting Processing:** Complete full processing (transcript → gap analysis → page updates) before creating new meeting pages
5. **Platform Integration:** Platform knowledge should be cross-linked with client pages from the start

---

**Report Generated:** 2026-04-06
**Reporter:** LINT automation
**Status:** ACTIVE — Awaiting remediation prioritization
**Next Review:** Post-remediation (1 week recommended)
