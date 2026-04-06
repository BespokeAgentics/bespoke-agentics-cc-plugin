---
type: meeting
client: Boston Beer Company
meeting-date: 2026-03-01
attendees: BBC Creative Operations, Brand Teams, Procurement
recording-path: meetings/03-custom-requests/source/
transcript-path: meetings/03-custom-requests/analysis/
pipeline-outputs: gap-analysis-bbc-custom-requests-meeting.md, client-elicitation-bbc.md
created: 2026-03-16
updated: 2026-03-16
sources:
  - meetings/03-custom-requests/analysis/gap-analysis-bbc-custom-requests-meeting.md
  - meetings/03-custom-requests/analysis/client-elicitation-bbc.md
  - meetings/03-custom-requests/confluence/
tags:
  - custom-requests
  - creative-operations
  - design-workflow
  - approvals
  - budget-management
  - merchandise
---

# Meeting: Custom Requests Walk-through (Parts 1 & 2)

## Summary

Two-part walkthrough of BBC's custom merchandise request ("Items From Scratch") lifecycle from submission through design, proofing, approval, and delivery. Meeting covered the 20+ field creative request form, designer assignment with delivery method coupling, proof upload and approval workflow with override capability, automated email notifications with inline approval buttons, and Creative Operations dashboard with status tracking and volume visualization. Also covered merchandise ordering workflows, budget management implementation, Virtual Warehouse usage, and fulfillment operations. Complete gap analysis identified 20 features with substantial custom development required for design workflow (4 XL/L components, 12+ custom objects) plus extensive questions on budget enforcement behavior, Oracle integration scope, returns/credits scope, and feature feasibility.

## Key Topics Covered

- **Custom Creative Request Submission:** 20+ field form capturing physical item specs (height, width, material, shape), branding references, designer assignment, delivery method, category, price (observed $1,000-$7,000)
- **Designer Assignment & Delivery Method:** "Digital Then -- Jason Krok" style coupling combining designer identity with delivery method; manual routing to creative ops team
- **Design Workflow:** Designers work in Adobe Illustrator with linked brand templates, export at 300 ppi CMYK with naming convention RequestNumber_BrandCode_Description
- **Proof Upload & Approval:** Drag-and-drop proof upload modal (PDF, PNG, images), gated approval workflow (Upload → Review → Approve/Decline → Post) with override capability and explicit unapproval confirmation
- **Email Notifications:** Automated HTML emails from no_return@bostonbeer.com with inline Approve/Decline/View buttons; reviewers can approve directly from email
- **Creative Operations Dashboard:** Bar chart visualization, status filters (Pending, Approved, Bid Request, Sent To Print, etc.), sub-tabs (ADMIN ALL, TO PRINT, SHIPPING)
- **Merchandise Ordering:** Brand-grouped budget tracking, pack-based quantities, co-op billing splits, proxy ordering for procurement staff
- **Virtual Warehouse Context:** 95 VWs serving as inventory allocation containers with per-brand budget enforcement

## Features Discovered / Updated

- [[custom-request-submission|Custom Request Submission]]: 20+ field form with physical item specs, branding, designer assignment, delivery method, category, pricing
- [[designer-assignment|Designer Assignment & Delivery Coupling]]: Manual routing with combined designer+delivery method field
- [[design-workflow|Design Workflow]]: Adobe Illustrator integration with brand templates, 300 ppi CMYK export, file naming convention
- [[proof-upload|Proof Upload]]: Drag-and-drop modal supporting PDF, PNG, image formats with file previews
- [[proof-approval|Proof Approval Workflow]]: Gated workflow (Upload → Review → Approve/Decline → Post) with email-based approval response
- [[proof-override|Proof Approval Override]]: Post unapproved proofs with explicit confirmation and audit trail
- [[approval-email|Email Approval Notifications]]: Automated HTML emails with inline Approve/Decline/View buttons
- [[creative-dashboard|Creative Operations Dashboard]]: Bar chart visualization, status filtering, pagination, sub-tabs for workflow stages
- [[request-number-format|Custom Request Number Format]]: NNNNN-YYYYMMDDNN format (e.g., 83106-26400571) used across communications and file naming
- [[rush-surcharge|Rush Surcharge Calculation]]: Automatic surcharge based on request delivery timing
- [[budget-enforcement|Brand-Level Budget Enforcement]]: Per-brand spending limits with enforcement behavior (hard stop vs soft warning) unconfirmed
- [[pack-based-ordering|Pack-Based Ordering]]: All merchandise in packout units (1-50 items) affecting pricing, cart display, fulfillment
- [[co-op-billing|Co-op Billing]]: Wholesaler cost-sharing with split logic unconfirmed
- [[proxy-ordering|Proxy Ordering]]: Procurement ordering on behalf of sales reps with VW context switching

## Gaps Identified

### Custom Request Workflow

- [[gap-request-number|Gap W1-G1: Custom Request Number Format]]: Severity Medium - NNNNN-YYYYMMDDNN format requires custom Apex generation; Standard auto-number insufficient. Options: (1) Apex trigger with sequence counter (2 days), (2) External ID with Apex values (1 day)
- [[gap-designer-coupling|Gap W1-G2: Designer/Delivery Coupling]]: Severity Low - Should separate into distinct fields for better data integrity and reporting
- [[gap-proof-override|Gap W1-G3: Proof Approval Override]]: Severity Medium - Salesforce Approval Processes don't natively support unapproved posting. Options: (1) Custom LWC with bypass modal + audit (2 days), (2) Independent "Post" action with required reason (1 day)
- [[gap-dashboard-chart|Gap W1-G4: Bar Chart Visualization]]: Severity Low - Embedded charts require Chart.js LWC (2 days) or CRM Analytics (3 days, license required)

### Budget & Ordering Workflows

- [[gap-budget-hardstop|Gap W2-G1: Budget Enforcement Behavior Unconfirmed]]: Severity Critical - Hard stop vs soft warning fundamentally affects implementation (3-4 weeks vs 2-3 weeks). Business rule documentation required.
- [[gap-pack-ordering|Gap W2-G2: Pack-Based Ordering Model]]: Severity High - Threading packout units through catalog, cart, checkout, fulfillment (2 weeks custom development)
- [[gap-proxy-authorization|Gap W2-G3: Proxy Ordering Authorization]]: Severity High - Role-based proxy context switching (2 weeks). Authorization model unconfirmed.
- [[gap-program-windows|Gap W2-G4: Program Window Time-Gating]]: Severity Medium - Custom Program_Window__c object with scheduled Flow automation (1.5 weeks automated, 2 days manual)

### Virtual Warehouse & Inventory

- [[gap-vw-concept|Gap W3-G1: Virtual Warehouse Concept]]: Severity Medium - No B2B Commerce equivalent; observation of zero inventory in all demo VWs suggests possible underutilization. Validation recommended before building. Options: (1) Full custom build (2.5 weeks), (2) Simplified account-based model (1 week), (3) Defer if underutilized
- [[gap-transfer-packout|Gap W3-G2: Inventory Transfer Packout Model]]: Severity Medium - Packout-based transfer logic with atomic operations (1 week)

### Fulfillment & Returns (Unobserved)

- [[gap-unobserved-fulfillment|Gap: Fulfillment Module Unobserved]]: Severity Unknown - FULFILLMENT tab never demonstrated; scope unclear
- [[gap-returns-credits|Gap: Returns & Credits Unobserved]]: Severity Unknown - Returns/Credits tabs visible but never demonstrated; scope and necessity unconfirmed

## Critical Unknowns Requiring Validation

| Question | Impact | Stakeholder | Priority |
|----------|--------|-------------|----------|
| **Budget Enforcement Behavior** | Hard stop vs soft warning changes implementation complexity and architecture | Finance / Business Stakeholders | **P0 BLOCKER** |
| **Oracle ERP Integration Scope** | Unknown data flows, budget sync direction, co-op billing integration | IT / Finance | **P0 BLOCKER** |
| **Salesforce Order Management Licensing** | Determines custom vs standard build for fulfillment, returns, credits | IT Procurement / Sponsor | **P0 BLOCKER** |
| **Virtual Warehouse Active Usage** | All observed VWs had zero inventory; feature may be underutilized | Procurement / Operations | **P1** |
| **Returns/Credits In Scope** | Never demonstrated; unclear if needed or out of scope | Business Sponsor | **P1** |
| **Six Unobserved Navigation Modules** | HISTORY, BUDGETS, APPROVALS, REPORTING, CONTACTS, LINKS scope unknown | Business Sponsor | **P1** |
| **Upstream Batch System Identity** | Order intake batching mechanism, vendor, APIs, team ownership | IT / ERP Team | **P0 BLOCKER** |
| **Fulfillment Vendor Protocols** | Which vendors, integration capabilities (API, EDI, email) | Procurement | **P0 BLOCKER** |

## Decisions Made

- **Request Number Migration:** Recommend External ID approach (Option 2) using Apex-generated values with standard auto-number for internal Salesforce references
- **Design Approval Architecture:** Decouple posting from approval with required reason for audit trail
- **Dashboard Chart Implementation:** Chart.js LWC (Option 1) for lower cost; CRM Analytics deferred to Phase 2
- **Feature Prioritization:** Custom request workflow and budget enforcement confirmed as Phase 2 priorities
- **Validation Gates:** Establish design blockers requiring client input before proceeding with detail design

## Open Questions Extracted

This meeting generated 38 unique questions across 4 priority tiers and 4 stakeholder groups. Key P0 design blockers:

### P0 - Must Answer Before Design

- [[q-upstream-batching|Q-01: Upstream Order Batching System]] - Identity, vendor, technology, APIs, ownership - Blocks entire order intake integration architecture
- [[q-fulfillment-locations|Q-02: Fulfillment Location Count]] - Beyond Milton Brewery? Operator count? Workflow variability? - Determines lightweight vs OMS licensing decision
- [[q-salesforce-org|Q-03: Existing Salesforce Org]] - Greenfield or existing? - Architecture impact
- [[q-operator-ui|Q-04: Operator UI Platform]] - Experience Cloud (community) vs Lightning Console (internal)? - Component/licensing impact
- [[q-b2b-commerce-confirmed|Q-05: B2B Commerce Confirmed]] - Target platform confirmation - Validates entire analysis
- [[q-erp-identity|Q-06: ERP System Identity]] - SAP, Oracle, NetSuite, custom? - MuleSoft connector selection
- [[q-mulesoft-license|Q-07: MuleSoft Licensing]] - Existing? In Salesforce agreement? Alternative iPaaS? - $50K-$200K+ cost variance

### P1 - Must Answer Before Estimates

- [[q-ups-application|Q-01: UPS Shipping Application]] - WorldShip, web, CampusShip? - UPS API tier and integration path
- [[q-order-volume|Q-02: Order Volume]] - Per day/week/month? Seasonal spikes? - Validates lightweight approach adequacy
- [[q-other-roles|Q-03: Other MerchTank Users]] - Credits, returns, reporting? In scope? - Returns/credits objects needed?
- [[q-shipment-id-purpose|Q-04: Shipment ID Purpose]] - Downstream use or redundant with tracking? - Field retention decision
- [[q-backup-operator|Q-05: Backup Operator/Continuity]] - How handled when operator absent? - Bus factor mitigation
- [[q-split-shipments|Q-06: Split Shipment Support]] - Multiple shipments per order or 1:1? - Shipment cardinality decision
- [[q-batch-schema|Q-07: Batch File Schema]] - Format, fields, data transformation complexity - MuleSoft design complexity
- [[q-catalog-size|Q-08: Product Catalog Size]] - Total SKUs? Master database? - Import strategy impact
- [[q-ups-api-access|Q-09: UPS API Access]] - Developer account available? - Phase 3 integration feasibility
- [[q-idp-confirmation|Q-10: Corporate IdP]] - Azure AD assumed? - SSO configuration path

### P2 - Should Know Before Build

- [[q-carrier-diversity|Q-01: Multi-Carrier Usage]] - FedEx, USPS beyond UPS? - Integration scope expansion
- [[q-packaging-reference|Q-02: Package Weights & Dimensions]] - Documented or tribal knowledge? - UPS API rate/label generation
- [[q-email-notification-logic|Q-03: Email Notification Details]] - CC recipients, conditionals, attachments? - Flow template design
- [[q-special-instructions|Q-04: Decompose Special Instructions]] - Structured fields beyond Need-By Date? - Field design
- [[q-sla-requirements|Q-05: SLA Requirements]] - Ship within 24 hours? Formal SLAs? - Escalation and reporting
- [[q-management-reporting|Q-06: Management Reporting]] - Key metrics? Currently pulled? - Reports/Dashboards scope
- [[q-catalog-field|Q-07: Catalog Field Meaning]] - Invoice, Merch, Brewery, Preview, Everyday? Routing impact? - Fulfillment logic
- [[q-quality-hold|Q-08: Quality Hold Process]] - Formal or ad hoc? - Workflow implementation
- [[q-batch-timing|Q-09: Batch Timing Flexibility]] - 5 PM set by upstream or MerchTank? - Real-time ordering feasibility
- [[q-requestor-email|Q-10: Requestor Email Population]] - User entry or profile-based? - Notification reliability

## Action Items

- **[Business Stakeholders]:** Confirm budget enforcement behavior (hard stop vs soft warning) - Due [Week 1] **BLOCKS DESIGN**
- **[Finance Team]:** Clarify Oracle ERP integration scope and data flows - Due [Week 2] **BLOCKS DESIGN**
- **[IT Procurement]:** Confirm Salesforce Order Management licensing decision - Due [Week 1] **BLOCKS DESIGN**
- **[Procurement Team]:** Validate Virtual Warehouse active usage with inventory counts - Due [Week 2]
- **[Business Sponsor]:** Scope Returns/Credits and unobserved navigation modules for Phase 1 - Due [Week 1] **BLOCKS SCOPE**
- **[IT]:** Identify upstream order batching system details - Due [Week 2] **BLOCKS DESIGN**
- **[Procurement]:** Identify fulfillment vendors and their integration protocols - Due [Week 2] **BLOCKS DESIGN**
- **[Architecture Team]:** Design custom request workflow with proof approval override - Due [Week 4]
- **[Architecture Team]:** Prototype budget-enforced cart with hard-stop validation - Due [Week 4]

## Raw Artifacts

- **Gap Analysis:** meetings/03-custom-requests/analysis/gap-analysis-bbc-custom-requests-meeting.md
- **Client Elicitation:** meetings/03-custom-requests/analysis/client-elicitation-bbc.md
- **Feature Inventory:** meetings/03-custom-requests/analysis/feature-inventory-*.md
- **SFCC Assessment:** meetings/03-custom-requests/analysis/sfcc-assessment-*.md
- **Confluence Export:** meetings/03-custom-requests/confluence/gap-analysis-confluence-bbc.{html,confluence}
- **Recording:** meetings/03-custom-requests/source/
