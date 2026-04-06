# Boston Beer Company Salesforce B2B Commerce Migration Wiki

Welcome to the Karpathy-style LLM Wiki for Boston Beer Company's migration from MerchTank to Salesforce B2B Commerce. This wiki consolidates all meeting notes, gap analysis findings, open questions, and design decisions into a searchable, interconnected knowledge base.

## Overview

Boston Beer Company (BBC) is migrating its custom-built MerchTank merchandise ordering platform to Salesforce B2B Commerce. MerchTank serves ~200-500 internal users across Procurement, Sales, Creative Operations, Brand Teams, Finance, and IT, managing 12+ beer brands with complex workflows including:

- **Merchandise ordering** with brand-level budget enforcement and wholesaler-based inventory allocation
- **Custom item design** with creative operations approval workflows
- **Fulfillment operations** with UPS shipping integration and tracking
- **Virtual Warehouse** per-person inventory allocation model
- **Co-op billing** for shared wholesaler cost arrangements

**Target State:** Salesforce B2B Commerce on Experience Cloud with custom Lightning Web Components, custom objects, and Apex business logic.

**Current Status:** Post-analysis phase. Five client meetings completed; comprehensive gap analysis produced; critical architectural decisions pending client input.

---

## Navigation

### Meetings (5 Sessions)

All client meetings have been recorded and analyzed. Each meeting page includes:
- Executive summary of key topics
- Features discovered and clarified
- Gaps identified with severity ratings
- Open questions needing client input
- Action items and next steps
- Links to raw artifacts (recordings, transcripts, gap analyses)

1. **[Meeting 01: MerchTank Overview](meetings/01-merchtank-overview.md)** (Dec 4, 2025)
   - Initial platform walkthrough with Jen Berger
   - Core commerce workflows and custom features overview
   - 18 features assessed; 7 critical gaps identified
   - Early-stage analysis with screen catalog and architecture mapping

2. **[Meeting 02: Virtual Warehouse Walkthrough](meetings/02-virtual-warehouse-walkthrough.md)** (Feb 2, 2026)
   - Deep dive into VW inventory model, catalog browsing, cart with budget validation, checkout
   - Complete gap analysis with 22 features and effort estimates
   - Critical decisions on VW retention vs simplification
   - 6-9 month estimated timeline for 3-person dev team

3. **[Meeting 03: Custom Requests Walk-through](meetings/03-custom-requests.md)** (Mar 1, 2026)
   - Custom merchandise request lifecycle from submission through design/proofing
   - Budget management and proxy ordering workflows
   - Virtual Warehouse context and fulfillment overview
   - 20 features with 38 unique open questions consolidated

4. **[Meeting 04: Fulfillment Demo](meetings/04-fulfillment-demo.md)** (Mar 15, 2026)
   - Order fulfillment operations at Milton Brewery with Benjamin Loverin (operator)
   - Daily 5 PM batch order intake, two-touch fulfillment, UPS WorldShip integration
   - 7 P0 design blockers and 22 critical assumptions identified
   - Lightweight custom-object approach recommended pending location count validation

5. **[Meeting 05: Finance Workflow](meetings/05-finance-workflow.md)** (Dec 9, 2025)
   - ⚠️ **UNPROCESSED** — Raw MP4 only
   - Placeholder indicating finance requirements walkthrough exists
   - Pending: frame extraction, transcript analysis, gap analysis

---

### Open Questions (5 Featured, 38+ Total)

The most critical questions blocking design decisions are documented in `/questions/`. Each question includes:
- Problem statement and context
- Impact if unanswered
- Proposed answer (if any) with confidence level
- Related features and gaps
- Resolution path and owner

**P0 Design Blockers (Must Answer Before Any Design):**

1. **[Upstream Batch System Identity](questions/upstream-batch-system-identity.md)** - What is the upstream system sending orders to MerchTank daily?
   - **Blocks:** Order intake integration architecture (40-60 hours effort)
   - **Owner:** IT / ERP Team

2. **[Budget Enforcement Behavior](questions/budget-enforcement-behavior.md)** - Hard stop vs soft warning when users exceed budget?
   - **Blocks:** Budget custom object model and cart validation design
   - **Owner:** Finance Team
   - **Impact:** 1-2 weeks effort variance

3. **[Oracle ERP as System of Record](questions/oracle-erp-system-record.md)** - Is Oracle the system of record for budgets?
   - **Blocks:** Budget data architecture and integration strategy
   - **Owner:** Finance / IT
   - **Impact:** Determines if Oracle sync is needed (6+ weeks integration effort)

4. **[Virtual Warehouse Active Usage](questions/virtual-warehouse-active-usage.md)** - Are the 95 VWs actively used or legacy?
   - **Blocks:** VW custom development (2-6 weeks effort variance)
   - **Owner:** Procurement / Operations
   - **Note:** All observed VWs had zero inventory; usage unclear

5. **[Salesforce Order Management Licensing](questions/salesforce-order-management-licensing.md)** - License OMS or build custom fulfillment?
   - **Blocks:** Fulfillment architecture decision
   - **Owner:** IT Procurement / Sponsor
   - **Impact:** $12K-24K/year licensing vs 2-4 weeks dev time tradeoff

**Other Critical Questions:**
- Fulfillment location count and workflow variability
- Existing Salesforce org (greenfield vs brownfield)
- Operator UI platform (Experience Cloud vs Lightning Console)
- B2B Commerce platform confirmation
- ERP system identity (SAP, Oracle, NetSuite, custom?)
- MuleSoft licensing availability

(See `/questions/` directory for full question register with P1/P2/P3 tiers and stakeholder mapping)

---

### Features

All discovered features are documented in `/features/` with:
- Current state implementation in MerchTank
- Target state on Salesforce B2B Commerce
- Related gaps and assumptions
- Links to relevant meetings

**Key Features:**
- [[virtual-warehouse-model]]
- [[brand-budget-tracking]]
- [[shopping-cart-with-budget]]
- [[proxy-ordering]]
- [[program-based-ordering-windows]]
- [[custom-item-design-submission]]
- [[co-op-billing]]
- [[order-queue-and-fulfillment]]
- [[shipment-recording]]

---

### Gaps

All identified gaps are documented in `/gaps/` with:
- Severity rating (Critical, High, Medium, Low)
- Detailed description of what's missing
- Resolution options with effort estimates
- Recommendations
- Related assumptions and risks

**Critical Gaps:**
- [[virtual-warehouse-inventory-model]] - No B2B Commerce equivalent for per-person VW allocation
- [[budget-management-engine]] - Zero OOTB budget tracking; complete custom build required
- [[custom-item-design-and-proofing]] - Multi-field form with file uploads and approval workflow
- [[co-op-billing]] - Cost-sharing arrangement with wholesalers
- [[proxy-delegate-ordering]] - "Order on behalf of" with context switching
- [[program-window-time-gating]] - Time-bound catalog availability

---

### Entities

Pre-existing entity pages document BBC's organizational structure and systems:
- [[boston-beer-company]] - Client profile and organization
- [[merchtank]] - Current platform documentation
- [[oracle-erp]] - ERP system overview

---

## Key Metrics & Status

### Meeting Coverage

| Meeting | Date | Status | Attendees | Key Artifacts |
|---------|------|--------|-----------|---------------|
| 01 - MerchTank Overview | Dec 4, 2025 | ✅ Analyzed | Jen Berger | Gap analysis (sample/early) |
| 02 - VW Walkthrough | Feb 2, 2026 | ✅ Complete | Ops Team | Full gap analysis, effort estimates |
| 03 - Custom Requests | Mar 1, 2026 | ✅ Complete | Creative Ops, Procurement | Gap analysis, client elicitation (38 Q's) |
| 04 - Fulfillment Demo | Mar 15, 2026 | ✅ Complete | Benjamin Loverin (operator) | Gap analysis, client elicitation (P0 blockers) |
| 05 - Finance Workflow | Dec 9, 2025 | ⏳ Unprocessed | Finance Leadership | Raw MP4 only |

### Gap Analysis Summary

| Category | Count | Status |
|----------|-------|--------|
| Total Features Assessed | 40+ | Across all meetings |
| Direct Match (config only) | 8 | 20% |
| Standard + Minor Custom | 10 | 25% |
| Requires Custom Development | 16 | 40% |
| Requires Architectural Redesign | 4 | 10% |
| Unknown/Pending | 2 | 5% |

### Critical Decisions Pending

| Decision | Owner | Deadline | Impact |
|----------|-------|----------|--------|
| Budget enforcement behavior (hard stop vs warning) | Finance | Week 1 | Architecture |
| Virtual Warehouse retention vs simplification | Procurement / Sponsor | Week 1 | 2-6 weeks dev effort |
| Upstream batch system identity | IT / ERP Team | Week 1 | Integration architecture |
| Fulfillment location count & workflow consistency | Operations | Week 2 | Lightweight vs OMS licensing |
| Salesforce OMS licensing decision | IT Procurement / Sponsor | Week 2 | $12K-24K/year + dev time |
| Oracle as budget system of record | Finance / IT | Week 2 | Integration scope (6+ weeks) |

---

## Implementation Phases (Recommended)

**Phase 1 — Foundation (Weeks 1-10)**
- Salesforce B2B Commerce environment setup
- Azure AD SSO configuration
- Product catalog data model and migration
- Experience Cloud storefront with brand/program navigation
- User provisioning and buyer group setup
- Milestone: Users can log in, browse catalog, see products by brand/program

**Phase 2 — Virtual Warehouse + Budget Engine (Weeks 6-18)**
- Virtual Warehouse custom objects + admin UI (if approved for Phase 1)
- Brand budget custom object + cart validation
- Proxy ordering context switching
- Data migration: VWs, inventory, budgets
- Milestone: Budget allocations loaded and queryable; VW management operational

**Phase 3 — Cart + Checkout + Fulfillment (Weeks 12-22)**
- Custom budget-grouped cart LWC
- Pack-based ordering display and calculations
- Custom checkout components (contacts, carrier, delivery instructions)
- Order intake batch integration (MuleSoft or file-based)
- Fulfillment provider integration
- Oracle ERP budget sync (if applicable)
- Approval workflows
- Milestone: End-to-end ordering from catalog to fulfillment submission

**Phase 4 — Reporting, Migration, Polish (Weeks 18-26)**
- Salesforce Reports and Dashboards
- Historical order data migration (if required)
- Custom design/proofing workflow (if Phase 1)
- Email notification templates
- UAT and bug fixes
- Training and change management
- Milestone: Production go-live

**Overall Timeline:** 6-9 months for 3-person dev team (assuming no scope expansion from unobserved modules)

---

## How to Use This Wiki

### For Architects & Project Leads

1. **Start with** the [Meeting pages](meetings/) to understand current state and observed workflows
2. **Review** critical [Open Questions](questions/) — these block design decisions
3. **Reference** the [Gap Analysis summaries](gaps/) to size custom development effort
4. **Use** the [Features directory](features/) to understand requirements detail

### For Developers

1. **Read** relevant [Meeting pages](meetings/) for workflow context
2. **Study** the [Gap Analysis documents](gaps/) — these are the design specifications
3. **Check** related [Features](features/) for edge cases and business rules
4. **Reference** SFCC assessment files in `/analysis/` for Salesforce capability mapping

### For Product Managers & Business Stakeholders

1. **Review** [Meeting pages](meetings/) to understand what was discussed
2. **Check** [Open Questions](questions/) to see what needs clarification
3. **Use** impact statements in gaps and questions to understand business implications
4. **Reference** [Phase descriptions](#implementation-phases-recommended) to plan timeline and resource allocation

---

## Key Hyperlink Conventions

This wiki uses internal wiki-link syntax for cross-referencing:

- `[[feature-name]]` — Links to feature documentation in `/features/`
- `[[gap-name]]` — Links to gap analysis in `/gaps/`
- `[[q-question-name]]` or `[[question-name]]` — Links to open questions in `/questions/`
- `[[meeting-NN-title]]` — Links to meeting pages in `/meetings/`
- `[[entity-name]]` — Links to entity pages in `/entities/`

Example: "The [[gap-budget-management-engine|budget management gap]] requires custom `Brand_Budget__c` objects to implement [[budget-tracking|per-brand budget enforcement]]."

---

## Source Materials

All analysis is grounded in raw artifacts from the client meetings:

### Recording & Transcript Locations

```
BostonBeerCompany/meetings/
├── 01-merchtank-overview/source/         # Frame extracts, transcript, audio
├── 02-virtual-warehouse-walkthrough/source/
├── 03-custom-requests/source/
├── 04-fulfillment-demo/source/
└── 05-finance-workflow/source/           # Raw MP4 only (unprocessed)
```

### Analysis Artifacts

```
BostonBeerCompany/meetings/NN-*/analysis/
├── gap-analysis-*.md                     # Primary deliverable
├── feature-inventory-*.md
├── sfcc-assessment-*.md
├── integration-assessment-*.md
├── data-schema-mapping-*.md
├── screen-catalog.md
├── component-library.md
├── system-architecture-map.md
├── client-elicitation-*.md               # Consolidated questions/assumptions
└── confluence/                           # HTML/Confluence Wiki exports
```

---

## Document Update Cycle

This wiki is updated as:

1. **Meetings are conducted** → Meeting page created/updated in `/meetings/`
2. **Gap analysis is completed** → Gaps extracted to `/gaps/` with severity/effort
3. **Client questions arise** → Questions added to `/questions/` with priority tier
4. **Decisions are made** → Recorded in relevant meeting/question/gap pages with links
5. **Phase details finalize** → Features/gaps marked with phase assignments

---

## Contact & Ownership

| Role | Owner | Contact |
|------|-------|---------|
| Wiki Maintainer | [AI Analysis Agent] | See BostonBeerCompany/INDEX.md |
| Project Sponsor | [BBC Business Sponsor] | TBD |
| Technical Lead | [Salesforce Architect] | TBD |
| Client Contact | [BBC IT/Procurement] | TBD |

---

## Version History

| Date | Change | Author |
|------|--------|--------|
| 2026-03-16 | Created 5 meeting pages, 5 question pages, README | Vendale Agentics (AI) |
| TBD | Finance workflow processing | TBD |
| TBD | Critical decision milestone | TBD |
| TBD | Phase 1 design completion | TBD |

---

**Last Updated:** 2026-03-25
**Next Recommended Action:** Answer P0 design blockers (Week 1 of project)
