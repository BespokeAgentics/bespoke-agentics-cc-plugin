---
type: entity
client: boston-beer-company
status: active
category: organization
created: 2026-04-06
updated: 2026-04-06
sources:
  - "BostonBeerCompany/CLAUDE.md"
  - "BostonBeerCompany/meetings/01-merchtank-overview/analysis/bbc-system-architecture-map.md"
  - "BostonBeerCompany/meetings/02-virtual-warehouse-walkthrough/analysis/integration-assessment-vw-walkthrough.md"
  - "BostonBeerCompany/meetings/03-custom-requests/analysis/integration-assessment-custom-requests-meeting.md"
  - "BostonBeerCompany/meetings/04-fulfillment-demo/analysis/integration-assessment-fulfillment-demo.md"
tags:
  - client
  - beer-industry
  - b2b-commerce
  - enterprise
---

# Boston Beer Company

## Overview

**Boston Beer Company (BBC)** is a major American brewery and beverage company operating multiple brand portfolios (Samuel Adams, Twisted Tea, Angry Orchard, Dogfish Head, and others) with national distribution through wholesalers and retailers. The company has internal operations spanning procurement, brand management, creative operations, finance, IT, and field sales.

BBC is currently operating **[[merchtank|MerchTank]]**, a custom-built internal merchandise ordering and fulfillment platform. The company is undertaking a strategic migration to **[[salesforce-b2b-commerce|Salesforce B2B Commerce]]** to modernize procurement, improve data visibility, automate fulfillment workflows, and align with enterprise cloud infrastructure.

## Key Characteristics

**Organization Structure:**
- **Procurement Department** — Order release authority, vendor management, fulfillment coordination (20+ third-party vendors)
- **Brand Teams** — Product management, budget owners (per-brand annual allocations)
- **Creative Operations** — Custom merchandise design, approval workflows, asset delivery
- **Finance** — Budget tracking, invoicing, co-op billing administration
- **IT** — System operations, identity management, integrations
- **Sales Organization** — Field representatives placing orders to merchandisers and wholesalers

**Scale & Operations:**
- **Locations:** 95+ virtual warehouses (field locations, district warehouses, wholesale partner accounts)
- **Products:** 10,000+ SKUs across multiple product categories (Drinkware, Apparel, Promotional Items, Packaging)
- **Order Volume:** Thousands of merchandise orders daily (seasonal peaks during summer/promotional campaigns)
- **Users:** Hundreds of employees across procurement, brand, creative, finance, and sales
- **Financial Scope:** Multi-million dollar annual merchandise budget (broken down per brand; managed through [[oracle-erp|Oracle ERP]])

**Current Technology Stack:**
- **Merchandise Platform:** [[merchtank|MerchTank]] (ASP.NET custom application)
- **Identity Provider:** Microsoft Azure Active Directory (Entra ID, SAML 2.0)
- **Financial System:** [[oracle-erp|Oracle ERP]] (budget allocations, invoicing, co-op billing)
- **Office Productivity:** Microsoft 365 (Teams, Outlook, OneDrive, Excel)
- **Intranet:** Brew Hub (SharePoint-based, serves as portal to MerchTank)
- **Supply Chain:** Supply Chain Management system (vendor unknown; likely SAP or similar)
- **Brand Asset Management:** BAM system (asset library and approval workflows)

## Key Stakeholders & Roles

**Executive Sponsor:**
- Title and name not disclosed in meeting recordings
- Drives business case for Salesforce migration (cost, modernization, integration)

**Procurement Leadership:**
- Manages vendor relationships, order release authority
- Budget forecasting and spend tracking
- Fulfillment coordination across 20+ vendors
- Pain points: Manual order release, no vendor status visibility, Excel tracking

**Finance Leadership:**
- Budget allocation per brand and time period
- Co-op billing administration (cost-split between BBC and wholesalers)
- Invoice reconciliation with [[oracle-erp|Oracle ERP]]
- Pain points: Delayed budget visibility, manual reconciliation with MerchTank

**Brand Management:**
- Budget owners (annual allocation per brand)
- Product selection and pricing strategy
- Marketing support via merchandise orders
- Pain points: Budget visibility lag, order status tracking, manual approval workflow

**Creative Operations:**
- Design request intake (custom merchandise design)
- Creative approval workflow (requestor → designer → approver)
- File delivery to requestors (via email + OneDrive link)
- Pain points: Manual email composition, no tracking of file delivery, no approval SLA enforcement

**IT / Systems Administration:**
- Identity management (Azure AD groups and role mapping)
- System operations, uptime, backups
- Integration architecture and middleware
- Pain points: Legacy system maintenance, manual integrations, scaling limitations

**Field Sales & Merchandisers:**
- End-users placing orders for promotional merchandise
- Virtual warehouse assignment (delivery to specific location)
- Order tracking and fulfillment status

## Current State Assessment

### Merchandise Ordering Workflow (Current)

1. **Browse & Add to Cart** — User logs in via Azure AD SSO to MerchTank → navigates product catalog by category → adds items to cart with quantity and delivery location (virtual warehouse)
2. **Pricing & Budget Visibility** — Cart displays pricing (volume-based), co-op split rules, and budget impact per brand
3. **Approval & Checkout** — User submits order; workflow routes to approvers based on amount/brand; once approved, order enters "Submitted" state
4. **Batch Order Intake** — Upstream batching system feeds orders to MerchTank daily (after 5 PM); orders become visible in MerchTank
5. **Procurement Release** — Procurement team reviews orders, manually releases to assigned vendor (via email or vendor portal)
6. **Vendor Fulfillment** — Vendor ships merchandise; UPS tracking number is manually copied from UPS app and pasted into MerchTank (3 separate entry points)
7. **Order Completion** — Status marked "Shipped"; invoice matches with [[oracle-erp|Oracle ERP]] for financial reconciliation
8. **Historical Tracking** — Orders manually re-entered into Excel shadow system for reporting and audit trail

### Creative Requests Workflow (Current)

1. **Request Submission** — User submits custom merchandise design request via MerchTank custom creative form (brand, product, artwork notes)
2. **Design Assignment** — Requestor assigned to designer; designer creates proofs based on guidelines and BAM assets
3. **Approval Loop** — Designer uploads proofs to custom creative dashboard; requestor reviews and provides feedback (Approve/Decline/View); designer iterates
4. **File Delivery** — Once approved, designer manually uploads final files to OneDrive "Digital Files" folder, generates sharing link, composes email to requestor with link, and sends
5. **No Delivery Confirmation** — No tracking of whether requestor downloaded file or printed design

### Key Pain Points Identified

**Operational:**
- Session timeouts force mid-workflow re-authentication (poor UX)
- Manual order release to vendors (slow, error-prone, not trackable)
- UPS tracking requires 3x manual copy-paste operations per order (copy from UPS, paste to MerchTank, paste to Excel)
- Excel shadow system (2x data entry per order; inconsistency and audit trail risk)
- Creative file delivery is entirely manual (no automation, no delivery confirmation)

**Integration & Data:**
- No real-time budget visibility (daily batch lag from [[oracle-erp|Oracle ERP]])
- No vendor fulfillment status feedback (operators must track across 20+ vendor systems)
- No UPS API integration (tracking, delivery proof)
- No automated file delivery or versioning (OneDrive is external file store)
- Oracle ERP integration is batch-based; no enforcement of budget limits at order time

**Scale & Governance:**
- 95 virtual warehouses create complexity in address assignment and inventory distribution
- Manual procurement workflows don't scale with volume growth
- No audit trail for order release decisions or budget overruns
- Email-based approvals lack strong audit trail
- No SLA enforcement on approval or creative turnaround time

## Salesforce B2B Commerce Migration Goals

**Phase 1 — Foundation (Months 1-3):**
- Stand up [[salesforce-b2b-commerce|Salesforce B2B Commerce]] storefront
- Implement [[sso-authentication|Azure AD SSO integration]]
- Migrate product catalog from MerchTank to Salesforce
- Launch core ordering workflow (browse → cart → checkout)
- Achieve feature parity with current MerchTank ordering (no creative requests yet)

**Phase 2 — Integration & Automation (Months 4-6):**
- Implement [[oracle-erp-integration|Oracle ERP data sync]] (real-time budget visibility)
- Build [[vendor-fulfillment|vendor fulfillment integration]] (automated order transmission)
- Integrate [[tradewearables-api|TradeWearables product catalog API]]
- Eliminate Excel shadow system (Salesforce reporting + audit trail)
- Migrate creative request workflow to Salesforce approval framework

**Phase 3 — Optimization & Automation (Months 7-9):**
- Automate UPS tracking integration (AppExchange connector or custom middleware)
- Build designer portal for file upload and tracking
- Implement real-time budget enforcement (prevent overspeending)
- Deprecate MerchTank; archive historical data to Salesforce
- Measure ROI: order cycle time, fulfillment accuracy, user adoption

**Expected Benefits:**
- **Time Savings:** Eliminate 3x manual copy-paste operations per order; 10-15 hours/week procurement time freed
- **Data Quality:** Eliminate Excel shadow system; single source of truth in Salesforce
- **Visibility:** Real-time order tracking, budget visibility, fulfillment status (vs. 24-hour batch lag)
- **Compliance:** Audit trail for all approvals, budget controls, and procurement decisions
- **User Experience:** Responsive UI, single sign-on (no separate login), mobile-friendly

## Relationships & Cross-References

**Related Platforms:**
- [[merchtank|MerchTank]] — Current merchandise ordering platform (being replaced)
- [[salesforce-b2b-commerce|Salesforce B2B Commerce]] — Target platform for migration
- [[oracle-erp|Oracle ERP]] — Financial system (budget allocations, invoicing)

**Integrations:**
- [[oracle-erp-integration|Oracle ERP Data Sync]] — Budget allocations, invoice reconciliation
- [[vendor-fulfillment|Vendor Fulfillment Integration]] — 20+ third-party fulfillment providers
- [[tradewearables-api|TradeWearables API Integration]] — Product catalog vendor
- [[sso-authentication|Azure AD SSO & Dual Authentication]] — Identity provider federation

**Related Entities:**
- [[oracle-erp|Oracle ERP]] — Financial system
- [[tradewearables|TradeWearables]] — Product vendor
- [[dogfish-head-brewery|Dogfish Head Brewery]] — BBC brand operations (fulfillment demo site)

## Meeting Artifacts & Documentation

**Walkthrough Recordings:**
- 01-merchtank-overview — End-to-end MerchTank platform tour (procurement, creative, financial workflows)
- 02-virtual-warehouse-walkthrough — Virtual warehouse inventory system, carrier selection, budget tracking
- 03-custom-requests — Creative request design approval workflow
- 04-fulfillment-demo — Brewery-level order fulfillment workflow (manual order release, UPS integration gap)

**Analysis Documents:**
- System architecture maps (per meeting)
- Gap analyses (Salesforce capabilities vs. current state)
- Integration assessments (external system dependencies)
- SFCC assessment (feature-by-feature Salesforce capability mapping)

## Notes

- BBC is a **well-resourced enterprise customer** with clear business case for Salesforce migration (multiple integration pain points, scale, modernization needs)
- The **Excel shadow system is a critical risk** — indicates loss of confidence in MerchTank as system of record; Salesforce migration must restore confidence via audit trail and reporting
- **Session timeout issue is unexplained** — suggests authentication token misconfiguration (needs investigation early in project)
- The **20+ fulfillment vendors** create complexity for vendor management; Salesforce must provide centralized orchestration (vs. current manual coordination)
- **Oracle ERP co-op billing** adds complexity to Salesforce integration design (cost-split logic must be enforced at order time)
- The **creative request workflow** is separate from core merchandise ordering; may need to be handled as Phase 2 effort (vs. Phase 1 core ordering)
