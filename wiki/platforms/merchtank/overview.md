---
type: platform
status: legacy
category: merchandise-fulfillment
created: 2026-04-06
updated: 2026-04-06
sources:
  - "BostonBeerCompany/CLAUDE.md"
  - "BostonBeerCompany/meetings/01-merchtank-overview/analysis/bbc-system-architecture-map.md"
  - "BostonBeerCompany/meetings/04-fulfillment-demo/analysis/integration-assessment-fulfillment-demo.md"
  - "BostonBeerCompany/meetings/03-custom-requests/analysis/integration-assessment-custom-requests-meeting.md"
tags:
  - legacy-system
  - merchandise
  - fulfillment
  - asp-net
  - internal-platform
---

# MerchTank — Merchandise Ordering & Fulfillment Platform

## Overview

**MerchTank** is a custom-built ASP.NET web application used by Boston Beer Company for internal merchandise ordering, budgeting, creative asset management, and fulfillment coordination. The platform serves as a central hub for procurement, brand teams, creative operations, finance, IT, and sales representatives to order branded merchandise (promotional items, packaging, display materials, apparel, etc.), track budgets, manage creative approvals, and coordinate shipping to field locations.

MerchTank operates with **minimal system integration** — order data flows inbound from upstream systems (batch feed), notifications flow outbound via email, and financial data syncs with [[oracle-erp|Oracle ERP]] for budget tracking and invoicing. The platform is functionally monolithic; most workflows are internal to MerchTank itself.

### Key Characteristics

**Architecture & Technology:**
- **Language & Framework:** ASP.NET (likely .NET Framework or .NET Core)
- **Database:** SQL Server (implied from ASP.NET stack; details not confirmed)
- **Deployment Model:** On-premises or hosted VM (brewhub.bostonbeer.com indicates intranet)
- **User Authentication:** Azure AD SSO (SAML 2.0) via corporate identity provider
- **Scale:** 95+ virtual warehouses, thousands of daily orders, 10k+ products
- **Uptime:** Business-critical system (procurement and fulfillment operations depend on it)

**Core Capabilities:**
- **Merchandise Ordering** — Browse products by category/brand, add to cart, checkout with approval workflow
- **Pricing & Budgets** — Volume-based pricing, per-brand budget allocation, co-op billing (cost-split between BBC and wholesalers)
- **Virtual Warehouses** — 95+ inventory locations representing field locations, district warehouses, wholesale partners
- **Inventory Visibility** — Real-time product availability per virtual warehouse location
- **Delivery Instructions** — Free-text fulfillment notes per order
- **Creative Requests** — Custom merchandise design orders (creative approval workflow, file delivery via email/OneDrive)
- **Order Status Tracking** — Order lifecycle from submission through fulfillment
- **Fulfillment Coordination** — 20+ third-party fulfillment vendors managed via order release workflow
- **Financial Integration** — Budget tracking, invoice correlation, co-op billing rules
- **Reporting & Analytics** — Order history, budget usage, spending trends (dashboards not in detail)

## Core Data Model

**Product Management:**
- `Product` — SKU, description, category, price, image
- `ProductCategory` — Hierarchy of merchandise categories (Drinkware, Apparel, Promotional Items, etc.)
- `Variant` — Size, color, material options (e.g., S/M/L for shirts, colors for mugs)
- `PricingRule` — Volume-based pricing, tiered discounts (e.g., 1-10 units @ $X, 11-50 units @ $Y)
- `InventoryLocation` — Virtual warehouse representation (95+ locations)

**Order Management:**
- `Order` — Order header (order number, date, requestor, brand, status)
- `OrderItem` — Line item within order (product SKU, quantity, unit price, extended price)
- `OrderStatus` — Lifecycle states (Submitted, Approved, In-Fulfillment, Shipped, Delivered, Canceled)
- `DeliveryAddress` — Ship-to location (address fields, delivery instructions)
- `ApprovalWorkflow` — Approval state, approver identity, approval timestamp

**Financial Tracking:**
- `BudgetAllocation` — Per-brand annual budget, allocated amount, period
- `BudgetUsage` — Order-level deduction from allocated budget (Ordered, Shipped, Remaining amounts)
- `CoOpBilling` — Cost-split rules (BBC share %, Wholesaler share %)
- `Invoice` — Vendor invoice correlation (for financial reconciliation with Oracle ERP)

**Creative Management (MerchTank Custom Creative Requests):**
- `CustomRequest` — Design request (artwork, proofs, approval status)
- `RequestTemplate` — Base design asset (brand guidelines, template formats)
- `Approval` — Creative review/approval (Designer, Requestor, Approver roles)
- `DesignFile` — Final approved design (stored in OneDrive, linked via sharing URL)

**User & Roles:**
- `User` — Azure AD identity, email, corporate role
- `Role` — Requestor, Approver, Designer, Admin (role-based access control via Azure AD groups)
- `Permissions` — Budget visibility, order release authority, approval delegation

## Integration Points

### INT-001: Azure AD SSO (SAML 2.0)

**Direction:** Bidirectional (request/response)
**Data Exchanged:** SAML assertions with user identity, email, group memberships, session tokens
**Frequency:** Real-time per session; re-auth on timeout
**Protocol:** SAML 2.0 via HTTP redirect binding
**Current State:** All @bostonbeer.com users authenticate through Azure AD; federated identity provider

**Issues:**
- Session timeouts force mid-workflow re-authentication (observed during cart-to-checkout navigation)
- Role mapping between Azure AD groups and MerchTank roles not visible; likely managed within MerchTank itself
- Fine-grained SAML attribute mapping for permissions not evident

---

### INT-002: Order Intake (Upstream Batching System)

**Direction:** Inbound (one-way)
**Data Exchanged:** Order records, line items, customer details, addresses
**Frequency:** Batch, daily (after 5 PM)
**Protocol:** Unknown (batch feed mechanism not observed; likely SFTP, database sync, or message queue)
**Current State:** Automated batch feed populates MerchTank order table; orders enter status "Submitted"

**Issues:**
- Daily batch architecture introduces 24-hour latency (orders from earlier in day not visible until next morning)
- Upstream system not explored (could be SAP, custom order aggregator, or portal order capture system)
- No real-time order synchronization capability

---

### INT-003: Oracle ERP (Financial System)

**Direction:** Bidirectional
**Data Exchanged:** Budget allocations, invoice data, co-op billing splits, financial reconciliation
**Frequency:** Batch (daily or weekly for budgets; per-invoice for billing)
**Protocol:** Unknown
**Current State:** Budget data visible in MerchTank (per-brand, per-wholesaler allocations); Oracle is system of record

**Issues:**
- No visible integration detail (observed browser tab "Oracle Fr..." but workflow not demonstrated)
- Co-op billing split logic adds complexity (BBC share vs. Wholesaler share)
- Invoice correlation requires manual reconciliation or custom ETL logic
- No real-time budget deduction (ordering still allowed even if exceeding budget; financial enforcement may occur post-order)

---

### INT-004: UPS Shipping Integration (Manual)

**Direction:** Outbound (tracking number entry)
**Data Exchanged:** Tracking numbers, shipping method, delivery estimate
**Frequency:** Per-order (on shipment)
**Protocol:** Manual copy-paste (no API)
**Current State:** Operator manually copies tracking number from UPS app, pastes into MerchTank order record (3x entry points: tracking number, shipment ID, Excel shadow system)

**Issues:**
- **Complete absence of automation** — entire flow is manual copy-paste
- Operator must toggle between UPS app and MerchTank (error-prone)
- Tracking info not automatically pushed to customer (email must be manually composed by designer)
- No feedback loop from UPS (shipment confirmation, delivery proof) back to MerchTank
- High-impact automation opportunity

---

### INT-005: Third-Party Fulfillment Vendors (20+ providers)

**Direction:** Outbound (order release)
**Data Exchanged:** Order details, SKU, quantity, shipping address, delivery instructions
**Frequency:** Per-order (on order release)
**Protocol:** Unknown (likely email, EDI, or vendor portal upload; "Delivery instructions for fulfillment Provider" text area suggests manual communication)
**Current State:** Procurement team manually releases orders to assigned vendor; vendor contact directory maintained in CONTACTS tab

**Issues:**
- No automated order transmission to vendors (manual release + vendor communication)
- Delivery instructions are free-text notes (ambiguous fulfillment requirements)
- Vendor order acknowledgment and fulfillment status not fed back into MerchTank
- Multi-vendor orchestration requires procurement operator to track status across 20+ systems
- No capability to auto-assign orders to vendors based on availability, lead time, or cost optimization

---

### INT-006: Microsoft Outlook / Exchange (Email Notifications)

**Direction:** Outbound (automated notifications)
**Data Exchanged:** Order number, status change, approvals, task completion
**Frequency:** Event-driven (status change triggers email)
**Protocol:** SMTP (outbound email)
**Current State:** Automated email notifications from `no_reply@bostonbeer.com` to users on order submission, approval needed, fulfillment status change

**Issues:**
- Dual email system: Both approval and fulfillment notifications sent (separate threads, inconsistent formatting)
- Email-based approval (inline action buttons) requires callback URL to MerchTank (implies undocumented web API endpoint)
- No preference management (users cannot opt-out of notifications)
- Email-based approval creates audit trail concerns if accounts are shared or forwarded

---

### INT-007: Microsoft OneDrive / SharePoint (Design File Delivery)

**Direction:** Outbound (file storage and sharing)
**Data Exchanged:** Final design assets (JPEG, PDF, PNG, PSD, ZIP, TIF), sharing links
**Frequency:** Per-creative-request completion
**Protocol:** OneDrive web UI (manual upload); SharePoint REST API available but not used
**Current State:** Designer uploads completed designs to OneDrive "My files > Digital Files" folder; copies sharing link; sends via email to requestor

**Issues:**
- Entirely manual workflow (no MerchTank-to-OneDrive automation)
- No link between MerchTank order status and file delivery status
- No confirmation that requestor downloaded file
- OneDrive acts as external file store disconnected from MerchTank records
- Significant automation opportunity (MerchTank could auto-upload and generate sharing links)

---

### INT-008: Excel Shadow System (Dual Data Entry)

**Direction:** Bidirectional (manual entry + manual updates)
**Data Exchanged:** Full order lifecycle data (order number, items, customer, shipment status, tracking)
**Frequency:** Per-order (manually entered 2x: order submission + shipment confirmation)
**Protocol:** Manual spreadsheet operations
**Current State:** Parallel Excel workbook maintains full order history (not authoritative in MerchTank); used for reporting and historical reference

**Issues:**
- **Critical data quality issue:** Every order manually entered in both MerchTank and Excel (2x data entry)
- No reconciliation mechanism between systems
- Excel is source of truth for historical analysis (MerchTank data considered temporary)
- Scaling barrier: Excel approach breaks with volume growth
- No audit trail (deletions/edits unlogged in spreadsheet)

---

### INT-009: Brand Asset Management (BAM) System

**Direction:** Inbound (asset references)
**Data Exchanged:** Brand logos, templates, color palettes, approved designs
**Frequency:** On-demand
**Protocol:** Unknown (likely REST API or web portal navigation)
**Current State:** Creative operations team references BAM during design approval process

**Issues:**
- Not fully integrated into MerchTank workflow (manual reference)
- No programmatic asset versioning or approval rule enforcement

---

### INT-010: Field Location / Warehouse Directory

**Direction:** Inbound (reference data)
**Data Exchanged:** Virtual warehouse location names, addresses, contact info
**Frequency:** Static reference (updated as locations change)
**Protocol:** Likely manual maintenance or sync from SAP
**Current State:** 95+ virtual warehouse locations configured in MerchTank; used for inventory location and delivery address defaults

**Issues:**
- Location master data source unclear (SAP? Manual? CSV import?)
- No validation that virtual warehouse addresses match actual delivery addresses
- Location deactivation/consolidation requires manual update in MerchTank

## Known Limitations & Pain Points

**Data Quality:**
- Excel shadow system creates duplication and inconsistency
- Manual order release introduces delays and errors
- No real-time data synchronization with upstream systems

**Scalability:**
- Manual copy-paste workflows (UPS tracking, order release to vendors) don't scale beyond current volumes
- Excel approach will fail if order volume grows significantly
- Session timeout mid-workflow causes user frustration

**Integration Gaps:**
- No vendor fulfillment status feedback into MerchTank
- No UPS API integration (tracking updates, delivery proof)
- No Oracle ERP real-time budget enforcement
- No automatic designer file delivery (no OneDrive API automation)

**Audit & Compliance:**
- Email-based approvals have weak audit trail
- Excel data changes unlogged
- No formal compliance controls over procurement or budget spend
- Order release authority not enforced (procurement team has manual discretion)

**User Experience:**
- Session timeout forces re-authentication mid-workflow (frustrating)
- Manual approval workflow via email is slow (compared to in-app approval)
- No mobile app (all workflows are web-based, not responsive)
- Search and product discovery limited (no faceted search, autocomplete basic)

## Relationships & Cross-References

**Related Platforms:**
- [[salesforce-b2b-commerce|Salesforce B2B Commerce]] — Target platform for migration
- [[salesforce-lwc|Lightning Web Components & Experience Cloud]] — Technology stack for replacement

**Integrations:**
- [[oracle-erp|Oracle ERP]] — Financial system for budgets and invoicing
- [[vendor-fulfillment|Vendor Fulfillment Integration]] — 20+ third-party fulfillment providers
- [[sso-authentication|SSO & Dual Authentication]] — Azure AD federation

**Entities:**
- [[boston-beer-company|Boston Beer Company]] — Operator and primary user of platform
- [[tradewearables|TradeWearables]] — Product catalog vendor (one of many suppliers)

## Migration Strategy (To Salesforce B2B Commerce)

**Quick Wins (Phase 1):**
1. Implement SAML SSO with Azure AD (Salesforce native support)
2. Build [[oracle-erp-integration|Oracle ERP data sync]] for real-time budget visibility
3. Create B2B Commerce storefront with product catalog, cart, checkout
4. Migrate core ordering workflow from MerchTank to Salesforce

**Medium-Term (Phase 2):**
1. Eliminate Excel shadow system via Salesforce reporting and audit trail
2. Implement [[vendor-fulfillment|vendor fulfillment integration]] with automated order transmission
3. Build [[tradewearables-api|TradeWearables product catalog sync]]
4. Migrate creative request workflow to Salesforce with approval automation

**Long-Term (Phase 3):**
1. Automate UPS tracking integration (via AppExchange connector or custom middleware)
2. Build designer portal for file upload and delivery tracking
3. Implement real-time budget enforcement (prevent overspeeding via validation rules)
4. Deprecate MerchTank; migrate historical data to Salesforce archive

## Notes

- MerchTank is **not a commercial product** — it's a custom internal system built over many years
- The platform is **business-critical** for BBC operations (daily merchandise orders flow through it)
- **No technical documentation found** (system knowledge held by operators and IT)
- The [[excel-shadow-system|Excel shadow system]] is a red flag for enterprise data governance (indicates lack of trust in source system)
- Session timeout issue suggests authentication token configuration problem (standard SAML timeout is 24 hours; MerchTank appears to be much shorter)
- The absence of UPS API integration is surprising for a logistics-heavy operation (suggests custom development effort was never prioritized over manual workaround)
