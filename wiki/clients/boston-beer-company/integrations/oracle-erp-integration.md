---
type: integration
client: boston-beer-company
status: planned
system-name: oracle-erp-integration
direction: bidirectional
frequency: batch
auth-method: oauth-2.0
created: 2026-04-06
updated: 2026-04-06
sources:
  - "BostonBeerCompany/meetings/02-virtual-warehouse-walkthrough/analysis/integration-assessment-vw-walkthrough.md"
  - "BostonBeerCompany/meetings/04-fulfillment-demo/analysis/integration-assessment-fulfillment-demo.md"
  - client-email-merchtank-feeder-systems-2026-04-06
tags:
  - erp
  - financial
  - budget-management
  - phase-2
  - planned
  - email
---

# Integration: Oracle ERP Budget & Invoice Sync

## ⚠️ Contradiction Notice — 2026-04-06

**Previous Information** (from meeting analysis inferences):
This page assumed Oracle ERP was the source of budget allocations synced to MerchTank.

**New Information** (from client email, Finance department, 2026-04-06):
**Anaplan** is the system of record for OPEX budgets. Client states: "We do NOT maintain our budgets for OPEX in SAP, it lives here [Anaplan]. Brand budgets get pulled from Anaplan and loaded into a template. This template gets fed to MT to populate the budgets."

**Resolution**: The budget allocation inbound flow described in this page may need to be **re-targeted at Anaplan** instead of Oracle ERP. Oracle may still handle invoice processing, GL posting, and co-op billing — but the budget sync origin is Anaplan, not Oracle. A separate Anaplan integration page may be needed.

**Impact**: The "Inbound Flow (Oracle → Salesforce)" section describing budget allocation sync is likely **incorrect as designed**. The data source should be Anaplan, not Oracle.

**Updated by**: client-email-merchtank-feeder-systems-2026-04-06

---

## Overview

This integration synchronizes budget allocations from ~~[[oracle-erp|Oracle ERP]]~~ **[[anaplan|Anaplan]]** (corrected per client email 2026-04-06) into [[salesforce-b2b-commerce|Salesforce B2B Commerce]] and correlates merchandise orders with invoice data for financial reconciliation. The integration enables:

- **Real-time budget visibility** in Salesforce (vs. current 24-hour batch lag in [[merchtank|MerchTank]])
- **Automatic budget enforcement** at order time (prevent overspending)
- **Order-to-invoice correlation** (via Salesforce Order Management)
- **Co-op billing logic** (automatic cost-split calculation)
- **Financial reporting** (budget utilization, spend trending)

**Business Drivers:**
- Current 24-hour budget visibility lag creates forecasting uncertainty
- No budget enforcement at order time (overspend is possible)
- Manual invoice matching (reconciliation errors)
- Complex co-op billing logic requires manual post-order accounting adjustment

**Target Users:**
- Brand managers (budget visibility in Salesforce cart)
- Procurement team (real-time budget tracking)
- Finance team (automated order-to-invoice reconciliation)

## Data Flow

### Inbound Flow (Oracle → Salesforce)

**Budget Allocation Synchronization:**

```
Oracle ERP (Budget Module)
  |
  v
Budget Report Extract (Daily batch, after 5 PM current state)
  - Per-brand annual allocation (e.g., Samuel Adams: $1,000,000)
  - Allocation period (fiscal year, calendar year)
  - Cost center / brand mapping
  - Available-to-spend amount
  |
  v
Middleware (Mulesoft or Salesforce Integration Cloud)
  - REST API call to Oracle ERP budget endpoint
  - Filter by BBC organization / legal entity
  - Map Oracle cost center → Salesforce brand/product catalog
  |
  v
Salesforce Platform Event (Platform_Event__e)
  - budget_allocation_updated event
  - Payload: brand_id, allocated_amount, available_amount, period, timestamp
  |
  v
Salesforce Flows or Apex Trigger
  - Create/update custom Budget__c record
  - Store current available balance
  - Log historical changes (for trending)
  |
  v
Salesforce Product Catalog
  - Link Budget__c to Product2 (via Brand field)
  - Components display available budget in cart
```

**Frequency:**
- **Current (MerchTank):** Daily batch, after 5 PM (24-hour lag)
- **Target (Salesforce):** Real-time API calls (or hourly batch with <1 hour lag)
- **Trigger:** Budget allocation change in Oracle; scheduled batch job; on-demand button

**Data Transformation:**

| Oracle Field | Salesforce Field | Notes |
|--------------|------------------|-------|
| Cost Center ID | Brand (Lookup to Product2) | Map Oracle CC to BBC brand |
| Cost Center Name | Brand Name | Samuel Adams, Twisted Tea, etc. |
| Annual Budget | Allocated_Amount__c | Total annual allocation |
| YTD Spent | OrderedAmount__c | Cumulative orders (from Salesforce) |
| Uncommitted Balance | Available_Amount__c | Allocated - Ordered |
| Period Start Date | Period_Start__c | Fiscal year start |
| Period End Date | Period_End__c | Fiscal year end |

**Error Handling:**
- **Missing Cost Center Mapping:** Log warning; skip record; alert procurement
- **Negative Budget (overspend):** Flag in budget record; trigger alert to finance
- **API Timeout:** Retry 3x with exponential backoff; alert on failure
- **Data Quality Issue:** Quarantine record; manual review by finance

### Outbound Flow (Salesforce → Oracle)

**Order Accrual to General Ledger:**

```
Salesforce Order Created
  - Order header: order_number, order_date, brand, total_amount
  - Order items: SKU, quantity, unit_price, extended_amount
  |
  v
Salesforce Order Management (Fulfillment Tracking)
  - Order transitions through lifecycle
  - Fulfillment tracking (shipped amount, shipped cost)
  |
  v
Scheduled Flow or Batch Apex (Nightly)
  - Identify new/changed orders
  - Create journal entry payload
  |
  v
Middleware (Mulesoft)
  - POST to Oracle ERP GL API
  - Payload:
    - Account code (merchandise expense, brand overhead)
    - Debit/credit amounts
    - Cost center (brand)
    - Order reference (for audit trail)
    - Timestamp
  |
  v
Oracle General Ledger
  - Journal entry posted
  - Accrual account updated
  - Budget consumed from available balance
  |
  v
Error Handling
  - Journal entry validation (pre-posting)
  - Retry on API failure
  - Reconciliation report (GL postings vs. Salesforce orders)
```

**Frequency:**
- Nightly batch (after order fulfillment data is stable)
- Per-order GL posting (if real-time preferred; higher API overhead)

**Accrual Rules:**
- **At Order Submission:** Accrue estimated cost to merchandise expense GL account
- **At Shipment:** Move from estimated to actual; adjust if qty/price changed
- **At Invoice Receipt:** Match invoice to order; if variance, adjust

### Invoice Matching Flow

**Order-to-Invoice Reconciliation:**

```
Oracle AP Module
  - Vendor invoice received (email, EDI, or portal)
  - Invoice entered or auto-imported
  - 3-way match: PO → Receipt → Invoice
  |
  v
Oracle Interface Table (if configured)
  - Invoice data exported to interface table
  - Order number / PO reference
  - Line item details, amount
  |
  v
Middleware (Scheduled API Call or EDI Feed)
  - Retrieve invoices from Oracle (by date range or status)
  - Filter by merchandise-related GL accounts
  |
  v
Salesforce Order Management
  - Create OrderPaymentSummary or OrderSummary record
  - Link to Salesforce Order via order_reference
  - Record invoice amount, invoice date, vendor
  |
  v
Finance Reconciliation Report
  - Show orders with matching invoices
  - Flag invoices without orders (vendor error)
  - Flag orders without invoices (pending receipt)
  - Variance analysis (order amount vs. invoice amount)
```

**Frequency:**
- Daily or weekly batch (invoice matching cycle)
- Triggered by invoice posting in Oracle

## Current Implementation

### Current State (MerchTank)

**Budget Synchronization:**
- **Mechanism:** Daily batch export from Oracle ERP
- **Schedule:** After 5 PM (implied)
- **Latency:** 24 hours (orders placed in morning show previous day's budget)
- **Data Source:** Oracle Budget Management module
- **Format:** Unknown (likely CSV, database dump, or API export)
- **Storage:** MerchTank SQL Server database

**Budget Enforcement:**
- **Mechanism:** None (soft reservation only)
- **Behavior:** Users can place orders exceeding available budget
- **Financial Enforcement:** Occurs post-order in Oracle GL (accounts payable or budget module)
- **Risk:** Unplanned budget overruns

**Invoice Matching:**
- **Mechanism:** Manual or semi-automatic (unclear)
- **Workflow:** Vendor invoice → Oracle AP → Manual matching in MerchTank
- **Status Tracking:** MerchTank order record may reference invoice number (but not bidirectional)
- **Issues:** Orphaned invoices (no matching order); orders without invoices (pending receipt)

**Co-Op Billing:**
- **Mechanism:** Manual accounting adjustment post-order
- **Workflow:**
  1. User places order in MerchTank with co-op product
  2. Order cost accrued to BBC GL account
  3. Finance team manually creates secondary invoice to wholesaler for their share
  4. Manual journal entry splits cost between BBC and wholesaler
- **Issues:** Error-prone; delay in cost allocation; no enforcement of agreed split percentages

### Current Issues & Pain Points

| Issue | Severity | Impact |
|-------|----------|--------|
| 24-hour budget visibility lag | High | Users forecast budgets on stale data; potential double-booking |
| No budget enforcement at order time | High | Overspending possible; financial controls ineffective |
| Manual invoice matching | Medium | Reconciliation errors; payment delays; auditor concerns |
| Manual co-op billing adjustment | High | Billing errors; margin loss; relationship risk with wholesalers |
| No real-time budget balance update | Medium | Users must refresh/log out to see current balance |
| Disconnected order-to-invoice system | Medium | Orphaned invoices; orders pending indefinitely |

## Target Architecture

### Design Principles

1. **Real-Time Budget Visibility** — API calls or change data capture (CDC) from Oracle; latency <1 hour
2. **Automatic Enforcement** — Salesforce validation rule prevents order placement if exceeds budget
3. **Transparent Co-Op Billing** — Pricing/promotion rules automatically apply cost splits; no manual adjustment
4. **Order-to-Invoice Correlation** — Salesforce Order Management links to invoice via order number
5. **Audit Trail** — All budget movements, order accruals, invoice matches logged in Salesforce

### Integration Components

**1. Middleware Layer (Mulesoft Anypoint or Salesforce Integration Cloud)**

```
Purpose: Translate between Oracle and Salesforce data models
Responsibilities:
  - REST API calls to Oracle ERP endpoints
  - Data transformation (Oracle fields → Salesforce fields)
  - Error handling and retry logic
  - Logging and monitoring
  - Scheduling (batch jobs)

Deployment: Mulesoft Cloud or Salesforce Integration Cloud (MuleSoft)
Maintenance: BBC IT or integration service partner
```

**2. Salesforce Objects & Custom Fields**

```
Budget__c (Custom Object)
  - Brand__c (Lookup to Product2)
  - Allocated_Amount__c (Currency)
  - Ordered_Amount__c (Currency, Roll-up Summary from Order)
  - Shipped_Amount__c (Currency, Roll-up Summary from Fulfillment)
  - Available_Amount__c (Formula: Allocated - Ordered)
  - Period_Start__c (Date)
  - Period_End__c (Date)
  - Last_Sync_Date__c (DateTime)
  - Sync_Status__c (Successful, Failed, Pending)

Product2 (Standard Object - Extended)
  - Brand__c (Text field for brand grouping)
  - Brand_Lookup__c (Lookup to Budget__c for performance)
  - Co_Op_Percentage_BBC__c (Number 0-100)
  - Co_Op_Percentage_Partner__c (Number 0-100)

Order / OrderItem (Salesforce Order Management)
  - Budget__c (Lookup to Budget__c)
  - Oracle_GL_Account__c (Text - for audit trail)
  - Oracle_Invoice_Number__c (Text - matched from AP)
  - Invoice_Amount__c (Currency)
  - Invoice_Date__c (Date)
  - Reconciliation_Status__c (Pending, Matched, Variance, Unmatched)
```

**3. Apex Triggers & Flows**

```
Trigger: Budget__c Insert/Update
  - Validate budget balance ≥ 0 (warn if negative)
  - Log sync history (for audit)
  - Trigger notification if budget < 20% remaining

Trigger: Order Insert
  - Lock Budget record (prevent concurrent updates)
  - Calculate Ordered_Amount roll-up
  - Apply co-op cost split (if applicable)
  - Check budget sufficiency; throw error if exceeds available
  - Release Budget lock

Flow: Nightly Batch Sync
  - Call Oracle API via Mulesoft (GET /budgets, GET /invoices)
  - Upsert Budget__c records
  - Upsert Invoice matching records
  - Log sync results
  - Send notification on error

Invocable Action: Manual Budget Refresh
  - Allow finance user to trigger sync on-demand
  - Useful for emergency budget adjustments
```

**4. Components & UI**

```
Product List Page (Catalog)
  - Show available budget in header (e.g., "Samuel Adams: $45,000 remaining")
  - Update dynamically as items added to cart

Cart Component
  - Display budget impact: "You have $2,000 allocated. This order is $500. Remaining: $1,500."
  - Warn if order approaches budget limit (e.g., "Only $100 remaining")
  - Prevent checkout if exceeds budget (validation rule)

Checkout Confirmation
  - Show co-op cost split (if applicable): "BBC: $250 | Partner: $250"
  - Confirm final order amount

Finance Dashboard (Reports & Dashboards)
  - Budget vs. Actual report (all brands)
  - Order aging report (Ordered vs. Shipped vs. Invoiced)
  - Invoice reconciliation report (matched vs. unmatched)
  - Variance report (order amount vs. invoice amount)
```

### Security & Authentication

**OAuth 2.0 with Oracle Cloud Identity**
- Salesforce registered as Connected App in Oracle Cloud Identity
- Authorization grant: Client Credentials (service-to-service)
- Scopes: `read_budgets`, `read_invoices`, `post_journalentries`
- Token lifetime: 1 hour (refreshed automatically by middleware)
- Secret management: Salesforce Secrets or Mulesoft Vault

**Network Security**
- API calls via HTTPS with certificate pinning (if available)
- IP whitelisting (Mulesoft IP range → Oracle firewall)
- VPN or private network endpoint (if on-premises Oracle)

**Data Security**
- PII (employee names) in order data encrypted in transit
- Budget data classified as Confidential (Salesforce-only visibility)
- Audit logging for all budget changes (who, what, when)
- Salesforce Field-Level Security restricts budget visibility by role

### Error Handling & Retry Strategy

| Error Type | Cause | Retry Strategy | Escalation |
|-----------|-------|-----------------|-----------|
| API Timeout | Network latency | Exponential backoff (1s, 2s, 4s, 8s) | Alert after 3 retries |
| API Rate Limit | Too many requests | Throttle to 10 req/sec; backoff | Auto-retry next hour |
| Authentication Failure | Invalid token | Refresh OAuth token; retry | Page on-call engineer |
| Data Validation Error | Missing field or bad format | Log and skip record; flag for manual review | Email to finance |
| Budget Not Found | Cost center not mapped | Create placeholder; alert procurement | Manual mapping required |
| Journal Entry Rejection | GL account invalid | Log error; notify finance | Manual GL posting |

### Monitoring & Alerting

**Salesforce Setup → Monitoring:**
- Monitor API calls to Oracle (Workbench or Einstein Analytics)
- Monitor trigger execution (debug logs, Apex limits)
- Monitor data sync latency (Platform Events or Flows)

**Mulesoft Setup:**
- Monitor HTTP requests (response time, error rate)
- Monitor queue depth (if using asynchronous processing)
- Monitor data transformation performance

**Alerts Triggered:**
- Sync failed (no data received from Oracle in 24 hours)
- Budget balance negative (overspend detected)
- Order rejected due to budget insufficiency
- Invoice-order mismatch (orphaned invoice)
- API rate limit hit (throttle active)

## Authentication & Security

**OAuth 2.0 Configuration:**
1. Register Salesforce as Connected App in Oracle Cloud Identity
2. Configure Client Credentials flow (not User Credentials)
3. Request scopes: `read_budgets`, `read_invoices`, `write_journalentries`
4. Obtain client_id and client_secret; store in Salesforce Secrets
5. Token refresh automatically handled by Mulesoft/integration cloud

**API Key Management:**
- Store in Salesforce Encrypted Custom Settings or Secrets
- Rotate annually
- Audit access logs (who requested credentials)

**Network Security:**
- HTTPS with TLS 1.2+ (minimum)
- Certificate pinning if available
- IP whitelisting (Mulesoft IPs on Oracle firewall)
- VPN or private cloud connection (if on-premises Oracle)

**Data Encryption:**
- Encrypted in transit (TLS)
- Encrypted at rest in Salesforce (optional, via Salesforce Shield)
- Budget data classified as Confidential

## Error Handling

### Budget Synchronization Errors

| Scenario | Handling | Recovery |
|----------|----------|----------|
| Oracle API unavailable | Retry 3x; cache last known budgets; warn users | Manual refresh when API online |
| Missing cost center mapping | Log warning; create temp placeholder | Finance team maps cost center |
| Negative budget (overspend) | Flag in Budget__c; alert finance | Manual adjustment in Oracle |
| Data format error (bad amount) | Log error; skip record | Validate in Oracle; resubmit |

### Order Submission Errors

| Scenario | Handling | Recovery |
|----------|----------|----------|
| Budget exceeded | Order rejected; show available balance | User reduces qty or waits for next budget period |
| Budget lock timeout | Retry order submission | Rare; escalate to support |
| GL account invalid | Order created but GL posting fails | Finance manually posts; reconciliation report flags |

### Invoice Matching Errors

| Scenario | Handling | Recovery |
|----------|----------|----------|
| Invoice-order mismatch | Create mismatch record; alert finance | Manual review and correction |
| Multiple orders match invoice | Flag ambiguous match; require manual selection | Finance resolves ambiguity |
| Invoice amount variance | Log variance; create exception record | Finance approves variance or rejects invoice |

### Reconciliation & Monitoring

**Daily Reconciliation Report:**
- Orders created vs. orders accrued in Oracle GL (should match)
- Budget allocated vs. budget used (track utilization %)
- Invoices matched vs. orders (should be 1:1)
- Orphaned invoices (not matched to order)
- Aging analysis (orders pending fulfillment, pending invoicing)

**Monthly Financial Review:**
- Budget variance by brand (actual spend vs. plan)
- Order cycle time (submission to fulfillment)
- Invoice variance analysis (order amount vs. invoice amount)
- Co-op billing accuracy (split percentages applied correctly)

## Dependencies

**Salesforce Dependencies:**
- B2B Commerce storefront deployed and operational (Phase 1)
- Order Management module enabled
- Mulesoft or Integration Cloud provisioned
- Custom objects (Budget__c) created and documented

**Oracle ERP Dependencies:**
- Budget Management module active
- API endpoints available (REST or SOAP)
- GL module configured for merchandise accrual
- AP module configured for invoice matching
- User account created for Salesforce service principal
- Cost center (budget) structure stable and documented

**Organizational Dependencies:**
- Finance team approval for GL accrual rules
- Procurement team trained on budget visibility in Salesforce
- IT governance approved for Oracle API access
- Service level agreement (SLA) on Oracle API uptime

**Data Preparation:**
- Cost center mapping (Oracle CC ID → Salesforce Brand)
- GL account mapping (merchandise expense accounts)
- Co-op billing rules documented and configured in Salesforce pricing
- Historical invoices imported for reconciliation (optional)

## Implementation Timeline (Phase 2)

| Week | Activity | Deliverable |
|------|----------|-------------|
| 1-2 | API Discovery & Documentation | Confirmed Oracle ERP API endpoints, auth method, rate limits |
| 3-4 | Salesforce Data Model | Custom objects, fields, relationships designed and created |
| 5-6 | Middleware Configuration | Mulesoft flows, transformations, error handling |
| 7-8 | Apex Development | Triggers, flows, batch jobs for budget sync and order accrual |
| 9-10 | UI Components | Cart budget display, dashboard, reporting |
| 11-12 | Integration Testing | End-to-end budget sync, order placement, GL posting tests |
| 13-14 | User Acceptance Testing (UAT) | Procurement, finance, brand teams test workflows |
| 15 | Go-Live Preparation | Cutover plan, data migration, user training |

**Total Effort:** 15 weeks (Phase 2 scope, assuming parallel workstreams)

## Open Questions

1. **Oracle API Availability:** Does Oracle ERP expose budget and invoice data via REST API? Or only via database-level access, file export, or EDI?
2. **Budget Accrual Rule:** Should orders be accrued to GL at submission (estimated) or at shipment (actual)?
3. **Co-Op Billing Complexity:** Are co-op cost splits per product, per order, or per promotion? Can rules be embedded in Salesforce pricing?
4. **Invoice Matching SLA:** What is acceptable latency for invoice matching? Same-day, next-day, or weekly?
5. **Historical Data:** Should historical orders and invoices from MerchTank be migrated to Salesforce? (Recommended: archive in MerchTank; use Salesforce for forward-looking only)
6. **Approval Workflow:** Does Oracle budgeting module allow over-spending with post-order correction? Or is hard-stop enforcement required?
7. **Multi-Entity Ledger:** Does BBC use multiple legal entities in Oracle? If so, how should orders be allocated to correct entities?

## Related Pages

**Platforms:**
- [[salesforce-b2b-commerce|Salesforce B2B Commerce]] — Target platform
- [[merchtank|MerchTank]] — Current system (provides baseline)

**Entities:**
- [[boston-beer-company|Boston Beer Company]] — Customer
- [[oracle-erp|Oracle ERP]] — External system

**Other Integrations:**
- [[vendor-fulfillment|Vendor Fulfillment Integration]] — Coordinates with order accrual
- [[sso-authentication|SSO & Dual Authentication]] — Identity provider

## Notes

- This integration is **Phase 2 priority** (after core ordering in Phase 1)
- Real-time budget enforcement is **critical to success** — eliminates overspending and financial surprises
- Co-op billing logic is **complex** and should be mapped out in detail before design (recommend workshop with BBC Finance)
- Recommend **early discovery call with BBC IT/Finance** to confirm Oracle API availability and preferred integration approach
- Consider **parallel run period** (both MerchTank and Salesforce orders) to validate budget sync accuracy before MerchTank sunset
