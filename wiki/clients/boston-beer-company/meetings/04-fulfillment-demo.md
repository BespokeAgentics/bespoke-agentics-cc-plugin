---
type: meeting
client: Boston Beer Company
meeting-date: 2026-03-15
attendees: Benjamin Loverin (Fulfillment Operator, Milton DE), Synovia (Program Manager), Operations Leadership
recording-path: meetings/04-fulfillment-demo/source/
transcript-path: meetings/04-fulfillment-demo/analysis/
pipeline-outputs: gap-analysis-boston-beer-company-fulfillment-demo.md, client-elicitation-boston-beer-company.md
created: 2026-03-25
updated: 2026-03-25
sources:
  - meetings/04-fulfillment-demo/analysis/gap-analysis-boston-beer-company-fulfillment-demo.md
  - meetings/04-fulfillment-demo/analysis/client-elicitation-boston-beer-company.md
  - meetings/04-fulfillment-demo/confluence/
tags:
  - fulfillment
  - brewery
  - shipping
  - ups
  - order-intake
  - warehouse-operations
---

# Meeting: Brewery Fulfillment Demo

## Summary

Deep-dive demonstration of BBC's order fulfillment operations at the Milton Brewery location with focus on the daily 5:00 PM batch order intake from upstream systems, manual two-touch fulfillment workflow, UPS shipping integration (WorldShip), and tracking number management. Meeting revealed critical architectural decisions needed around upstream batch system identity, fulfillment operator UI platform selection, and order intake technology (MuleSoft vs direct API vs file-based). Fulfillment operator Benjamin Loverin provided extensive tribal knowledge about package weights, box sizes, carrier selection ("FRN" codes), and exception handling through Program Manager Synovia. Assessment identified 7 critical P0 blockers requiring immediate stakeholder clarification plus 22 explicit assumptions and 9 low-confidence features. Lightweight custom-object approach recommended pending fulfillment location count validation.

## Key Topics Covered

### Fulfillment Workflow

- **Order Intake:** Daily batch at 5:00 PM delivers orders from upstream system; 16-hour delay before operator receives work queue (typical for Brew Hub/intranet check at 9 AM next day)
- **Two-Touch Fulfillment:** (1) Order review, address validation, shipment initiation in MerchTank → (2) Label generation in UPS WorldShip with carrier selection, weight entry, cost validation
- **Operator Queue Management:** Excel spreadsheet tracking orders (Order ID, Requestor Email, Need-By Date extracted from Special Instructions free-text) with manual status progression
- **UPS Integration:** UPS WorldShip (desktop app) for label generation, carrier selection (UPS, FRN, others), weight/dimension entry; Tracking numbers captured back in MerchTank
- **Carrier Selection Logic:** "Lowest Cost/Best Partner" visible in MerchTank UI but actual selection mechanism unclear (fulfillment-provider-managed vs platform-calculated)
- **Need-By Date Extraction:** Operators manually parse Special Instructions field for "Need By:" text; inconsistent adoption by requestors ("we've been working on trying to train these folks")
- **Special Instructions:** Free-text field for custom delivery instructions, room/suite numbers, contact preferences
- **Exception Handling:** Synovia (Program Manager) handles exceptions; Cherry Bomb formula quality hold cited as "the very first time we did it"
- **Backup & Continuity:** No backup operator documented; single operator per location (bus factor = 1)
- **Product Quality Holds:** Ad hoc process when products fail quality checks

### Upstream Systems & Integration

- **Batch System:** Unknown identity, vendor, technology, APIs — described as "upstream order batching system" that sends daily batch to MerchTank
- **Fulfillment Providers:** Unknown names, integration protocols, workflows; orders passed with delivery instructions
- **Brew Hub Integration:** SharePoint intranet portal used by operator for general information access; Brew Hub link visible in MerchTank but unclear integration
- **ERP Integration:** Oracle observed in IT team browser tabs but data flows undocumented
- **Reporting:** SQL Server SSRS with VPN access (unreliable), standard MerchTank reports, Excel-based operator tracking

## Features Discovered / Updated

- [[order-intake|Order Intake Batch]]: Daily 5:00 PM batch from upstream system with 16-hour delay
- [[two-touch-fulfillment|Two-Touch Fulfillment Workflow]]: MerchTank review → UPS WorldShip label generation
- [[fulfillment-queue|Operator Queue Management]]: Excel spreadsheet with manual Order ID, requestor email, Need-By date tracking
- [[ups-worldship|UPS WorldShip Integration]]: Desktop application for label generation with carrier selection and weight entry
- [[carrier-selection|Carrier Selection]]: UPS, FRN (FedEx Regional?), and other carrier codes; "Lowest Cost/Best Partner" optimization
- [[tracking-number|Tracking Number Management]]: Generated in WorldShip, captured back in MerchTank, stored as Shipment ID (possibly redundant)
- [[need-by-date-parsing|Need-By Date Extraction]]: Manual parsing from Special Instructions text; inconsistent requestor adoption
- [[special-instructions|Special Instructions Field]]: Free-text for custom delivery info (room numbers, contact prefs, timing)
- [[exception-handling|Exception Handling]]: Program Manager (Synovia) handles exceptions and escalations
- [[product-quality-hold|Product Quality Hold]]: Ad hoc process for formula failures (Cherry Bomb example)
- [[shipment-status|Shipment Status Tracking]]: Order statuses (Entered, Open, Shipped); Shipment linking unclear
- [[brew-hub-access|Brew Hub Portal Integration]]: SharePoint intranet link accessible from MerchTank
- [[email-notification|Email Notification]]: Automated emails from MerchTank with order details (format, logic, CC recipients unconfirmed)

## Gaps Identified

### P0 Design Blockers (Must Answer Before Architecture)

- [[gap-upstream-identity|Gap Q-01: Upstream Order Batching System]]: Identity, vendor, technology, APIs, ownership unknown. **Blocks entire order intake integration design** (40-60 hours). Fallback: CSV file-based import via SFTP
- [[gap-location-count|Gap Q-02: Fulfillment Location Count & Variability]]: Milton Brewery demonstrated; other locations unknown. **Blocks lightweight vs OMS licensing decision**. Effort variance: 2-5x if multiple locations with different workflows
- [[gap-existing-org|Gap Q-03: Salesforce Org Status]]: Greenfield or existing org? **Blocks architecture decisions** (object namespace, existing automation, deployment)
- [[gap-operator-ui|Gap Q-04: Operator UI Platform]]: Experience Cloud (community) vs Lightning Console (internal)? **Blocks all 6 custom LWC designs** (component availability, licensing, security model)
- [[gap-b2b-confirmed|Gap Q-05: B2B Commerce Confirmed]]: Platform confirmation (not B2C, Platform-only). **Invalidates entire analysis if different**
- [[gap-erp-identity|Gap Q-06: ERP System Identity]]: SAP, Oracle, NetSuite, custom? **Blocks MuleSoft connector selection** and cost estimate
- [[gap-mulesoft-license|Gap Q-07: MuleSoft Licensing Status]]: Existing license? In agreement? Alternative iPaaS? **Could vary integration cost by $50K-$200K+**

### Feature-Level Gaps

- [[gap-fulfillment-dashboard|Gap: Fulfillment Dashboard]]: Severity Medium - Custom LWC with queue view, status filtering, approval workflow
- [[gap-carrier-optimization|Gap: Carrier Optimization]]: Severity Medium - "Lowest Cost/Best Partner" implementation unclear (platform vs vendor)
- [[gap-ups-integration|Gap: UPS WorldShip Integration]]: Severity High - Current desktop app to cloud integration (3-4 weeks); requires UPS API access, rate calculation, label generation
- [[gap-batch-import|Gap: Batch Import Mechanism]]: Severity High - Unknown source format; fallback to CSV/SFTP if upstream system not identified (4+ weeks for direct API)
- [[gap-fulfillment-routing|Gap: Fulfillment Vendor Routing]]: Severity High - Unknown vendor protocols; multiple vendor integration patterns may be required (4-6+ weeks)
- [[gap-special-instructions|Gap: Structured Special Instructions]]: Severity Medium - Need-By date extraction from free-text (1 week to auto-parse and restructure)
- [[gap-tracking-number|Gap: Tracking Number Field]]: Severity Low - Shipment ID field purpose unclear; may be redundant with tracking number or serve downstream ERP sync

### Critical Assumptions Requiring Validation

| ID | Assumption | Impact If Wrong | Validation Method |
|----|-----------|-----------------|-------------------|
| **A-01** | Salesforce B2B Commerce confirmed as target | Entire analysis must be redone | Confirm with sponsor |
| **A-02** | Operators will use Lightning Console (internal) not Experience Cloud | Component availability, licensing, security differs significantly | Confirm with IT + Sponsor |
| **A-04** | Upstream batch system can be modified to increase frequency | Daily 16-hour delay persists; file-based fallback needed | Confirm with IT/ERP team |
| **A-10** | Same fulfillment workflow applies to all brewery locations | Scope multiplies if different location workflows | Confirm with Operations |
| **A-03** | Corporate IdP is Azure AD | SSO configuration redesigned for different provider | Confirm with IT |
| **A-05** | Boston Beer can obtain UPS Developer API account | Phase 3 carrier integration blocked without it | Confirm with IT/Procurement |
| **A-06** | MuleSoft included in or addable to Salesforce agreement | Alternative iPaaS adds $50K-$200K+ and timeline | Confirm with Procurement |
| **A-09** | UPS primary carrier; FRN, USPS secondary | Multi-carrier scope expansion if all actively used | Confirm with Operator |
| **A-13** | 5 PM batch timing set by upstream system not MerchTank | Migration alone doesn't fix latency if MerchTank-imposed | Confirm with IT |

### Low-Confidence Features (Medium/Low Confidence Assessment)

| ID | Feature | Confidence | Why Low | Evidence Needed |
|----|---------|-----------|---------|-----------------|
| **LC-01** | Program Manager role (Synovia) handles all exceptions/escalations | Low | Mentioned once; authority/scope unclear | Interview Synovia's manager on exception workflow |
| **LC-02** | Requestors trained to enter Need-By in Special Instructions | Medium | Operator: "been working on trying to train these folks" -- incomplete adoption | % of orders with structured Need-By dates in Special Instructions |
| **LC-03** | Product quality holds (Cherry Bomb) are extremely rare | Medium | "Very first time we did it" but process was well-understood | Hold frequency, formal process documentation |
| **LC-04** | "FRN" carrier codes map to FedEx | Medium | Not standard abbreviation; could be private carrier/regional | Confirm carrier identity for FRN |
| **LC-05** | Upstream batch system is separate from ERP | Medium | Never identified; could be ERP module, custom app, middleware | Identify system |
| **LC-06** | MerchTank uses standard SMTP for email | Medium | Protocol assumed not observed | Confirm email infrastructure |
| **LC-07** | Order lifecycle has exactly 3 statuses (Entered, Open, Shipped) | Medium | Only ones observed; others (Canceled, On Hold, Partial) may exist | Export full status picklist from MerchTank |
| **LC-08** | MerchTank is ASP.NET WebForms | Medium | Inferred from UI; not confirmed | Confirm technology stack |
| **LC-09** | Excel spreadsheet contains no data not also in MerchTank | Medium | Derivative tracking tool; could have untracked notes/annotations | Review actual Excel spreadsheet |

## Decisions Made

- **Architecture Approach:** Lightweight custom-object approach recommended over full Salesforce Order Management, pending fulfillment location count validation
- **Operator Platform:** Recommend Lightning Console for internal users (lower cost, more component availability) pending confirmation
- **Batch Integration Strategy:** MuleSoft Anypoint recommended for order intake middleware; fallback to CSV file-based import via SFTP if upstream system not identified
- **UPS Integration:** Multi-carrier AppExchange solution (Zenkraft recommended) vs direct UPS API depends on actual carrier usage
- **Proof of Concept:** Early POCs recommended for UPS API integration, batch file import, and fulfillment queue management
- **Phasing:** 4-phase approach with fulfillment operations in Phase 3 (Weeks 12-22), contingent on integration architecture decisions

## Open Questions Extracted

Comprehensive client elicitation produced 38 unique questions consolidated into 4 priority tiers with stakeholder mapping:

### **P0 Design Blockers** (7 Questions - Must Answer Before Any Design)

1. **Upstream Order Batching System** [IT/ERP Team] - Identity, vendor, technology, APIs, team ownership
2. **Fulfillment Location Count & Workflow Variability** [Operations] - Milton only or multiple? Different workflows?
3. **Existing Salesforce Org** [IT] - Greenfield or existing (object namespace, automation, deployment impact)?
4. **Operator UI Platform** [IT + Sponsor] - Experience Cloud vs Lightning Console (component/licensing/security)
5. **B2B Commerce Target Confirmation** [Sponsor] - Validated platform selection
6. **ERP System Identity** [IT/Finance] - SAP, Oracle, NetSuite, custom?
7. **MuleSoft Licensing** [IT Procurement] - Existing? In agreement? Alternative iPaaS?

### **P1 Must Answer Before Estimates** (10 Questions)

- UPS Shipping Application (WorldShip, web, CampusShip?)
- Order Volume (per day/week/month? Seasonal spikes?)
- Other MerchTank User Roles (credits, returns, reporting?)
- Shipment ID Field Purpose (downstream use or redundant?)
- Backup Operator / Continuity Plan (single operator risk?)
- Split Shipment Support (multiple shipments per order?)
- Batch File Format & Schema (CSV, XML, JSON?)
- Product Catalog Size (total SKUs? Master database?)
- UPS API Access (Developer account available?)
- Corporate Identity Provider (Azure AD confirmed?)

### **P2 Should Know Before Build** (10 Questions)

- Carrier Diversity (beyond UPS - FedEx/USPS usage?)
- Packaging Reference Data (weights/dimensions documented?)
- Email Notification Logic (CC, conditionals, attachments?)
- Special Instructions Decomposition (structured fields?)
- SLA Requirements (24-hour ship target? Formal SLAs?)
- Management Reporting (key metrics, current sources?)
- Catalog Field Meaning (Invoice/Merch/Brewery/Preview/Everyday routing?)
- Product Quality Hold Process (formal or ad hoc?)
- Batch Timing Flexibility (5 PM set by upstream or MerchTank?)
- Requestor Email Population (user entry or profile-based?)

### **P3 Nice to Know** (11 Questions)

- Historical Data Preference (import Excel or clean cutover?)
- Mobile Fulfillment Interest (scanning from phone?)
- Brew Hub Consolidation Plans (migrate to Salesforce?)
- Designer Filter Meaning
- DNR/DAM/OHM Module Scope
- Data Retention Policy
- Synovia's Full Role & Title
- Distributor Ordering Role

## Action Items

- **[Business Sponsor]:** Identify upstream order batching system - Due [Week 1] **BLOCKS DESIGN**
- **[Operations]:** Confirm fulfillment location count and workflow consistency - Due [Week 2] **BLOCKS LICENSING**
- **[IT]:** Determine greenfield vs existing Salesforce org status - Due [Week 1] **BLOCKS DESIGN**
- **[IT + Sponsor]:** Confirm operator UI platform (Experience Cloud vs Lightning Console) - Due [Week 1] **BLOCKS LWC DESIGN**
- **[Business Sponsor]:** Reconfirm Salesforce B2B Commerce as target - Due [Day 1] **VALIDATES ANALYSIS**
- **[IT/Finance]:** Identify ERP system and confirm Oracle integration scope - Due [Week 2] **BLOCKS DESIGN**
- **[IT Procurement]:** Confirm MuleSoft licensing availability - Due [Week 1] **IMPACTS BUDGET**
- **[Operator/Fulfillment]:** Clarify FRN carrier codes and multi-carrier usage - Due [Week 2]
- **[IT]:** Provide batch file schema and upstream system API documentation - Due [Week 3]
- **[Operations]:** Document SLA requirements and management reporting metrics - Due [Week 3]
- **[Architecture Team]:** Build POC for UPS API integration (rate calculation + label generation) - Due [Week 4]
- **[Architecture Team]:** Prototype batch import mechanism (CSV fallback vs MuleSoft) - Due [Week 4]

## Raw Artifacts

- **Gap Analysis:** meetings/04-fulfillment-demo/analysis/gap-analysis-boston-beer-company-fulfillment-demo.md
- **Client Elicitation:** meetings/04-fulfillment-demo/analysis/client-elicitation-boston-beer-company.md
- **Feature Inventory:** meetings/04-fulfillment-demo/analysis/feature-inventory-*.md
- **Integration Assessment:** meetings/04-fulfillment-demo/analysis/integration-assessment-*.md
- **Data Schema Mapping:** meetings/04-fulfillment-demo/analysis/data-schema-mapping-*.md
- **Confluence Export:** meetings/04-fulfillment-demo/confluence/gap-analysis-confluence-boston-beer-company.{html,confluence}
- **Recording:** meetings/04-fulfillment-demo/source/
