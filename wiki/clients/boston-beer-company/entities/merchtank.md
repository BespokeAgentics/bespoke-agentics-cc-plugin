---
type: entity
client: boston-beer-company
status: legacy
category: system
created: 2026-04-06
updated: 2026-04-06
sources:
  - "BostonBeerCompany/CLAUDE.md"
  - "BostonBeerCompany/meetings/01-merchtank-overview/analysis/bbc-system-architecture-map.md"
  - "BostonBeerCompany/meetings/02-virtual-warehouse-walkthrough/analysis/integration-assessment-vw-walkthrough.md"
  - "BostonBeerCompany/meetings/03-custom-requests/analysis/integration-assessment-custom-requests-meeting.md"
  - "BostonBeerCompany/meetings/04-fulfillment-demo/analysis/integration-assessment-fulfillment-demo.md"
  - client-email-merchtank-feeder-systems-2026-04-06
tags:
  - legacy-system
  - merchandise
  - fulfillment
  - internal-platform
  - migration-target
  - email
---

# MerchTank — Entity Record

## Overview

**MerchTank** (merchtank.bostonbeer.com) is Boston Beer Company's custom-built merchandise ordering, budgeting, and fulfillment platform. It serves as the central hub for internal procurement, enabling employees to order branded merchandise (drinkware, apparel, promotional items, packaging) for distribution to field locations, wholesale partners, and promotional campaigns.

The platform is a **legacy system under active replacement** by [[salesforce-b2b-commerce|Salesforce B2B Commerce]]. While functionally complete, MerchTank exhibits multiple pain points: manual order release workflows, lack of vendor integration, Excel shadow system (data duplication), and manual file delivery for creative requests.

## Key Characteristics

**System Properties:**
- **Type:** Custom-built internal merchandise ordering platform
- **Technology:** ASP.NET (likely .NET Framework or .NET Core)
- **Database:** SQL Server (implied)
- **Deployment:** Hosted or on-premises (integrated with Brew Hub intranet)
- **Authentication:** Azure AD SSO (SAML 2.0)
- **Users:** Hundreds (procurement, brand teams, creative ops, finance, field sales, merchandisers)
- **Scale:** 95+ virtual warehouses, 10k+ products, thousands of daily orders
- **Criticality:** Business-critical (daily merchandise operations depend on it)
- **Status:** Active but in deprecation phase (migration to Salesforce underway)

**Core Workflows:**
1. **Merchandise Ordering** — Browse catalogs, add to cart, approve, release to vendor, track shipment
2. **Virtual Warehouse Management** — Assign orders to 95+ field/district/partner locations
3. **Budget Tracking** — Per-brand annual budget allocations, usage tracking, co-op billing splits
4. **Creative Requests** — Custom merchandise design request intake, approval workflow, file delivery
5. **Financial Integration** — Order-to-invoice correlation with [[oracle-erp|Oracle ERP]]

**Data Volume:**
- Thousands of orders daily
- 10,000+ product SKUs
- 95 virtual warehouse locations
- 20+ fulfillment vendors
- Millions of historical orders (since inception)
- Multi-petabyte transaction history (implied)

## Relationships

### Dependency: [[boston-beer-company|Boston Beer Company]]

- **Relationship:** Operator, user, and sponsor of platform
- **Type:** Primary customer; internal system
- **Ownership:** BBC IT department
- **Users:** Procurement, brand management, creative operations, finance, field sales
- **Status:** Planning migration to [[salesforce-b2b-commerce|Salesforce B2B Commerce]]

### Integration: [[azure-ad|Azure Active Directory (Entra ID)]]

- **Relationship:** [[sso-authentication|Identity provider for SAML 2.0 federation]]
- **Type:** External system (corporate identity)
- **Data Exchanged:** User identity, email, group memberships, session tokens
- **Frequency:** Per session; re-auth on timeout
- **Status:** Active; configured for @bostonbeer.com domain

### Integration: [[oracle-erp|Oracle ERP]]

- **Relationship:** [[oracle-erp-integration|Financial system for budget allocations and invoicing]]
- **Type:** External system (ERP backbone)
- **Data Exchanged:** Budget allocations, financial transactions, invoice correlation
- **Frequency:** Batch (daily or weekly); per-invoice for billing
- **Status:** Active; bidirectional sync required (not fully detailed in analysis)
- **Gap:** No real-time budget enforcement at order time; batch lag of 24+ hours

### Integration: [[sam-central|Sam Central (Legacy Coworker Database)]]

- **Relationship:** User access control and approval thresholds
- **Type:** External system (legacy coworker database)
- **Data Exchanged:** Organizational hierarchy, sales geography hierarchy, coworker approval thresholds, coworker-to-distributor mappings
- **Frequency:** Cost center hierarchy updated daily; approval thresholds looked up in real-time at order submit/approve time
- **Status:** Active; critical dependency for access control and approvals
- **Source:** Client email 2026-04-06 (IT department)

### Integration: [[anaplan|Anaplan (Financial Reporting / Budget Management)]]

- **Relationship:** Budget allocations source → MerchTank; Budget usage reporting → Anaplan
- **Type:** External enterprise financial reporting system
- **Data Exchanged:** Brand budgets (inbound to MT via template), budget usage reporting (outbound from MT during LE cycles ~5x/year)
- **Frequency:** Budget loading via template (frequency TBD); usage reporting ~5x/year
- **Status:** Active; **Anaplan is the source of truth for OPEX budgets** — NOT SAP, NOT Oracle
- **Source:** Client email 2026-04-06 (Finance department)

### Integration: [[workfront|WorkFront (Project Management)]]

- **Relationship:** Asset intake, POS workflow management, item setup data collection
- **Type:** External project management system
- **Data Exchanged:** Asset data, item setup info, proofs/thumbnails, part number generation via MDM
- **Frequency:** Per-asset/per-item setup
- **Status:** Active
- **Automation:** If "Upload to Merchtank" selected → data to MDM → notifies Procurement/Creative Ops → part number in MDM → pushes to SAP & back to WorkFront
- **Source:** Client email 2026-04-06 (Brand/Creative and Procurement departments)

### Integration: [[mdm|MDM (Master Data Management)]]

- **Relationship:** Part number generation and product master data
- **Type:** Internal master data system
- **Data Exchanged:** Asset classification, part numbers
- **Flow:** WorkFront → MDM (if Upload to Merchtank selected) → MDM generates part number → pushes to SAP & back to WorkFront
- **Status:** Active
- **Source:** Client email 2026-04-06 (Procurement department)

### Integration: [[sap|SAP / SAP Ariba]]

- **Relationship:** Part number repository; hard goods procurement bidding
- **Type:** External ERP/procurement system
- **Data Exchanged:** Part numbers (from MDM), hard goods procurement bids and pricing
- **Note:** BBC does NOT maintain OPEX budgets in SAP (budgets are in Anaplan)
- **Status:** Active
- **Source:** Client email 2026-04-06 (Finance and Procurement departments)

### Integration: Upstream Batching System

- **Relationship:** Daily order feed into MerchTank
- **Type:** Inbound order generation
- **Data Exchanged:** Order records, line items, customer details, delivery addresses
- **Frequency:** Daily batch (after 5 PM)
- **Status:** Active; 24-hour latency on order visibility
- **Gap:** Unknown upstream system (could be SAP, custom portal, or aggregator)

### Integration: [[vendor-fulfillment|Third-Party Fulfillment Vendors (20+)]]

- **Relationship:** [[vendor-fulfillment|Order fulfillment partners]]
- **Type:** External vendor ecosystem
- **Data Exchanged:** Order details, SKU, quantity, shipping address, delivery instructions
- **Frequency:** Per-order release (manual by procurement)
- **Status:** Active; **completely manual workflow** (no API or automated transmission)
- **Gap:** No vendor status feedback; no automated order transmission; no fulfillment tracking

### Integration: UPS Shipping

- **Relationship:** [[vendor-fulfillment|Carrier for merchandise delivery]]
- **Type:** External shipping system
- **Data Exchanged:** Tracking numbers, shipping method, delivery estimates
- **Frequency:** Per-order shipment
- **Status:** Active; **completely manual copy-paste** (no API integration)
- **Gap:** Operator manually copies tracking from UPS app to MerchTank (3 separate entry points); no return of delivery proof or exception data

### Integration: [[excel-shadow-system|Excel Shadow System]]

- **Relationship:** Parallel order tracking (data duplication)
- **Type:** Manual spreadsheet
- **Data Exchanged:** Full order lifecycle data (order number, items, shipment status, tracking)
- **Frequency:** Per-order (2x data entry: order submission + shipment confirmation)
- **Status:** Active; **critical data quality issue**
- **Gap:** No reconciliation; Excel considered more authoritative than MerchTank for historical reporting

### Integration: Microsoft Outlook / Exchange

- **Relationship:** [[sso-authentication|Email notifications and manual file delivery]]
- **Type:** External email system
- **Data Exchanged:** Order notifications, approval requests, design file sharing links
- **Frequency:** Event-driven (order status change, approval needed)
- **Status:** Active; email-based approvals, manual file composition

### Integration: Microsoft OneDrive / SharePoint

- **Relationship:** [[excel-shadow-system|Design file storage and sharing]]
- **Type:** External cloud file storage
- **Data Exchanged:** Design assets (JPEG, PDF, PNG, PSD, ZIP, TIF)
- **Frequency:** Per-creative-request completion
- **Status:** Active; **manual upload and link sharing** (no OneDrive API automation)
- **Gap:** Disconnected from MerchTank order records; no automated file delivery or confirmation

### Integration: BAM (Brand Asset Management)

- **Relationship:** Brand asset library for creative requests
- **Type:** External asset management system
- **Data Exchanged:** Brand logos, templates, color palettes, approved designs
- **Frequency:** On-demand reference
- **Status:** Active; manual navigation by designers

### Integration: Supply Chain Management System

- **Relationship:** Inventory visibility and allocation
- **Type:** External supply chain system (vendor unknown, likely SAP)
- **Data Exchanged:** Inventory levels per virtual warehouse, product availability
- **Frequency:** Batch or near-real-time
- **Status:** Active; source of inventory data for MerchTank display

## History & Timeline

- **Early 2000s** — MerchTank custom development begins (estimated, not documented)
- **2010s** — Platform scales with BBC growth; 95+ virtual warehouses added
- **2020** — Excel shadow system introduced (informal; indicates loss of confidence in MerchTank data)
- **2024-2025** — Strategic decision made to migrate to [[salesforce-b2b-commerce|Salesforce B2B Commerce]]
- **2026** — Migration underway; Phase 1 (core ordering) expected to launch Q3 2026

## Known Issues & Pain Points

### High-Impact Issues

**Manual Order Release Workflow**
- Procurement team manually releases orders to 20+ vendors
- No API or automated transmission; likely email or manual portal upload
- No vendor acknowledgment or fulfillment status feedback
- Vendor contact management is manual directory (CONTACTS tab)
- **Impact:** 5-10 hours/week procurement labor; delays order processing

**Manual UPS Tracking Entry**
- Operator must manually copy tracking number from UPS app
- Paste into MerchTank (3 separate locations: order record, shipment ID, Excel)
- No UPS API integration; no return of delivery proof or exceptions
- **Impact:** 3 hours/week manual data entry; high error rate

**Excel Shadow System**
- Every order manually re-entered into Excel after shipment confirmation
- Excel acts as system of record for historical analysis (indicates loss of trust in MerchTank)
- No reconciliation between MerchTank and Excel; data inconsistency
- No audit trail for Excel edits (deletions, corrections unlogged)
- **Impact:** 5-8 hours/week manual data entry; audit trail risk; data quality risk

**Manual File Delivery for Creative Requests**
- Designer manually uploads file to OneDrive
- Copies sharing link
- Composes email to requestor
- No confirmation that requestor received/downloaded
- **Impact:** 2-3 hours/week per designer; error-prone subject line formatting; no delivery SLA

### Medium-Impact Issues

**24-Hour Batch Order Lag**
- Upstream system feeds orders to MerchTank daily (after 5 PM)
- Orders not visible in MerchTank until next morning
- Users cannot track order status for same-day submitted orders
- **Impact:** 20 hours maximum latency on order visibility

**24-Hour Budget Visibility Lag**
- Oracle ERP budget allocations sync daily (batch)
- Budget impact of orders not reflected until next day
- No enforcement of budget limits at order time (overspend possible)
- **Impact:** Budget forecasting uncertainty; potential overspending

**Session Timeout Mid-Workflow**
- Session timeout observed during cart-to-checkout navigation
- Forces re-authentication via Azure AD redirect
- Poor user experience (interruption in ordering flow)
- **Impact:** User frustration; potential abandoned carts

**Role Mapping Not Visible**
- Role mapping between Azure AD groups and MerchTank roles unclear
- Likely managed within MerchTank (separate from Azure AD)
- No fine-grained SAML attribute mapping for permissions
- **Impact:** Role changes delayed; manual role adjustment in MerchTank

### Low-Impact Issues

**Search & Discovery**
- Product search is basic (no faceted filtering, limited autocomplete)
- Browse by category is primary navigation mode
- No merchant-driven search rankings or merchandising rules
- **Impact:** User experience; product discoverability

**Reporting & Analytics**
- Historical reporting relies on Excel (not MerchTank dashboards)
- No built-in BI; custom reports require manual Excel export
- **Impact:** Finance and procurement analytics limited

**Mobile Access**
- MerchTank is web-based but not responsive
- Mobile ordering experience poor
- Field users prefer desktop or tablet access
- **Impact:** Limited mobile adoption

## Migration Status

**Target Replacement:** [[salesforce-b2b-commerce|Salesforce B2B Commerce]]

**Phase 1 — Foundation (Months 1-3, Target Q2 2026):**
- Migrate product catalog to Salesforce
- Stand up B2B Commerce storefront
- Implement Azure AD SSO [[sso-authentication|single sign-on integration]]
- Launch core ordering workflow (feature parity with MerchTank)
- **Deliverable:** Salesforce storefront for merchandise ordering

**Phase 2 — Integration & Automation (Months 4-6, Target Q3 2026):**
- [[oracle-erp-integration|Oracle ERP data sync]] (real-time budget visibility)
- [[vendor-fulfillment|Vendor fulfillment integration]] (automated order transmission)
- [[tradewearables-api|TradeWearables API integration]] (product catalog)
- Eliminate Excel shadow system (Salesforce audit trail + reporting)
- Migrate creative request workflow
- **Deliverable:** Automated order-to-fulfillment workflow; real-time budget visibility

**Phase 3 — Optimization (Months 7-9, Target Q4 2026):**
- UPS tracking automation (AppExchange connector or custom middleware)
- Real-time budget enforcement (prevent overspending)
- Deprecate MerchTank; archive historical data
- **Deliverable:** MerchTank sunset; full Salesforce operation

## Notes

- MerchTank is **functionally complete but operationally brittle** — systems are tightly coupled, manual workflows don't scale, and data duplication undermines reliability
- The **Excel shadow system is a critical indicator** — tells us that BBC has low confidence in MerchTank as source of truth; Salesforce must restore that confidence via audit trail, reporting, and real-time visibility
- **No technical documentation discovered** — system knowledge is tribal (held by operations staff); migration will require extensive knowledge transfer
- The **manual UPS integration** is surprising for a logistics-heavy operation; suggests custom development was never prioritized
- **Session timeout issue is unexplained** — may indicate authentication token configuration problem (needs root-cause investigation early in project)
- MerchTank's **90+ virtual warehouse model is complex** but is not a blocker for Salesforce migration (can be managed via custom address lookup or virtual warehouse master data)
