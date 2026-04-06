---
type: entity
client: boston-beer-company
status: active
category: system
created: 2026-04-06
updated: 2026-04-06
sources:
  - "BostonBeerCompany/meetings/02-virtual-warehouse-walkthrough/analysis/integration-assessment-vw-walkthrough.md"
  - "BostonBeerCompany/meetings/03-custom-requests/analysis/integration-assessment-custom-requests-meeting.md"
  - "BostonBeerCompany/meetings/04-fulfillment-demo/analysis/integration-assessment-fulfillment-demo.md"
  - client-email-merchtank-feeder-systems-2026-04-06
tags:
  - erp-system
  - financial
  - external-integration
  - enterprise-system
  - email
---

# Oracle ERP — Entity Record

## Overview

**Oracle ERP** (likely Oracle Financials or Oracle ERP Cloud) is Boston Beer Company's enterprise resource planning system. It manages financial planning, accounts receivable, and invoice processing.

## ⚠️ Contradiction Notice — 2026-04-06

**Previous Information** (from meeting analysis inferences):
Oracle ERP was assumed to be the system of record for brand-level budget allocations. Budget data assumed to sync daily from Oracle to MerchTank.

**New Information** (from client email, Finance department, 2026-04-06):
**Anaplan** is the system of record for OPEX budgets, not Oracle/SAP. Client states: "Anaplan — This is our BBC financial reporting system and is a widely used enterprise solution. We do NOT maintain our budgets for OPEX in SAP, it lives here."

**Resolution**: Oracle ERP's role in the budget workflow is now unclear. It may still handle invoice processing, co-op billing, and GL posting, but **brand budget allocations originate in Anaplan**. The wiki's previous assumption that Oracle was the budget SOR must be revised across all affected pages.

**Updated by**: client-email-merchtank-feeder-systems-2026-04-06

---

The system may still be the authoritative source for:

- ~~Annual budget allocations per brand~~ → **Moved to Anaplan** (see contradiction above)
- ~~Budget spending tracking~~ → Budget usage reported from MerchTank to **Anaplan** during LE cycles (~5x/year)
- Co-op billing administration (cost-split between BBC and wholesalers) — **status unclear, may remain in Oracle**
- Invoice reconciliation (vendor invoices matched to merchandise orders) — **likely still Oracle**
- Multi-year financial planning — **status unclear, may be Anaplan**

## Key Characteristics

**System Properties:**
- **Type:** Enterprise Resource Planning (ERP) system
- **Vendor:** Oracle Corporation (Oracle Financials or Oracle ERP Cloud)
- **Deployment:** Cloud (likely Oracle Cloud Infrastructure, OCI)
- **Database:** Oracle Database
- **Users:** Finance, procurement, brand management, accounting teams at BBC
- **Criticality:** Business-critical (financial system of record)
- **Status:** Active; core financial operations depend on it
- **Integration Scope:** Multi-system (accounts payable, general ledger, accounts receivable, budget management modules)

**Module Scope (Inferred):**
- **Budget Management** — Annual budget creation, allocation per cost center (brand), tracking
- **Financial Planning** — Multi-year planning, scenarios, forecasting
- **Accounts Payable** — Vendor invoices, payment processing, reconciliation
- **Accounts Receivable** — Wholesaler invoicing for co-op billing
- **General Ledger** — Chart of accounts, journal entries, reporting
- **Procurement Integration** — PO-to-invoice matching, accrual accounting

## Data Structures & Concepts

**Budget Model:**
- **Budget Allocation** — Annual per-brand budget (e.g., Samuel Adams: $1,000,000 annual)
- **Budget Period** — Fiscal year or calendar year allocation
- **Cost Center** — Brand (Samuel Adams, Twisted Tea, Angry Orchard, Dogfish Head, etc.)
- **Usage Tracking** — Ordered amount, Shipped amount, Remaining amount (available to spend)
- **Multi-Year Planning** — 2027, 2028, 2029 budget tabs observed in [[merchtank|MerchTank]] UI (data originates in Oracle)

**Co-Op Billing Model:**
- **Co-Op Agreement** — Retailer/wholesaler cost-sharing arrangement (BBC pays X%, partner pays Y%)
- **Cost Split Rule** — Per-product or per-promotion cost allocation (e.g., "tap handles: 50% BBC, 50% wholesaler")
- **Invoice Split** — Accounts receivable entry created for wholesaler's portion; BBC absorbs its share
- **Example:** "If they pay for half of the tap handles, then this is what will come out of my budget, and our wholesaler will be invoiced for the remaining part"

**Invoice Processing:**
- **Vendor Invoice** — Third-party fulfillment vendor invoice for merchandise order fulfillment
- **Order-to-Invoice Matching** — MerchTank orders correlated with Oracle invoices (reconciliation)
- **Payment Processing** — Matched invoices routed to accounts payable for payment
- **Accrual Accounting** — Orders accrued at shipment; invoices recorded when received

## Relationships & Integrations

### Integration: [[merchtank|MerchTank (Merchandise Ordering Platform)]]

- **Relationship:** [[oracle-erp-integration|Budget allocations → MerchTank; Orders → Oracle for financial reconciliation]]
- **Type:** Bidirectional data sync (batch)
- **Data Exchanged:**
  - **Inbound to MerchTank:** Budget allocations per brand, remaining amounts, co-op cost split rules
  - **Outbound to Oracle:** Order transactions for accrual, invoice matching data
- **Frequency:**
  - Budget sync: Daily or weekly batch (implied)
  - Invoice reconciliation: Per-invoice (event-driven)
- **Status:** Active; critical to merchandise ordering workflow
- **Current Issues:**
  - 24-hour batch lag on budget visibility (budgets updated daily after 5 PM)
  - No real-time enforcement of budget limits (overspend possible at order time)
  - Invoice matching manual or via reconciliation module (exact mechanism unknown)
  - Co-op billing split logic not enforced at order time in MerchTank (manual accounting adjustment later)

### Integration: [[salesforce-b2b-commerce|Salesforce B2B Commerce (Target Platform)]]

- **Relationship:** [[oracle-erp-integration|Planned integration for budget visibility and invoice sync in Salesforce migration]]
- **Type:** Bidirectional data sync (batch or real-time)
- **Data Exchanged:**
  - Budget allocations, real-time budget tracking
  - Order-to-invoice correlation
  - Financial transactions for accrual and revenue recognition
- **Frequency:** Real-time or near-real-time (target; vs. current 24-hour lag)
- **Status:** Planned in Salesforce Phase 2 (Months 4-6 of migration)
- **Benefits:**
  - Real-time budget visibility in Salesforce (vs. 24-hour lag in MerchTank)
  - Automatic enforcement of budget limits at order time (prevent overspending)
  - Seamless order-to-invoice correlation via Salesforce Order Management
  - Simplified co-op billing logic (rules embedded in pricing/cart calculation)

### Integration: [[boston-beer-company|Boston Beer Company (Financial Operations)]]

- **Relationship:** Operates and maintains Oracle ERP
- **Type:** Internal organizational ownership
- **Users:** Finance, accounting, procurement, brand management teams

## Current Integration Architecture

**System Diagram:**
```
Oracle ERP (System of Record)
  |
  +-- Budget Allocations (Daily Batch)
  |   |
  |   v
  +-> MerchTank (Budget Display, Tracking)
  |
  +-- Invoice Feed (Per-Invoice)
  |   |
  |   v
  +-> MerchTank (Order-to-Invoice Matching)
      |
      v
  MerchTank Order Data (Exported/Synced)
      |
      v
  Oracle AP Module (Invoice Processing)
      |
      v
  Check Register / Payment Processing
```

**Data Flow Details:**

1. **Budget Allocation Push (Daily):**
   - Oracle ERP budget management module generates daily budget report
   - Report extracted via (unknown mechanism: database sync, file export, API call)
   - Data loaded into MerchTank budget tracking table
   - MerchTank displays per-brand available budget to users during ordering

2. **Order Accrual (Per-Order):**
   - User submits order in MerchTank
   - Order data (cost, brand, quantity) logged in MerchTank database
   - At order submission or approval, amount deducted from available budget (soft reservation)
   - Actual accrual in Oracle GL may occur at different point (shipment vs. invoice)

3. **Invoice Matching (Per-Invoice):**
   - Vendor invoice arrives (paper or EDI, likely EDI given scale)
   - Invoice details manually entered or imported into Oracle AP module
   - System matches invoice to PO and receipt (three-way match)
   - Matched invoice routed to accounts payable for payment
   - MerchTank order record updated with invoice reference (if correlated)

4. **Co-Op Billing (Per-Order with Co-Op Agreement):**
   - Order cost split rule applied manually or via Oracle billing module
   - BBC share accrued to GL
   - Wholesaler share recorded as accounts receivable
   - Wholesaler invoiced separately (outside MerchTank visibility)

## Known Issues & Gaps

### Integration Gaps

**No Real-Time Budget Enforcement:**
- Budget limits not enforced at order time in MerchTank
- Users can place orders that exceed available budget
- Financial enforcement occurs post-order (in Oracle GL or upon invoice matching)
- **Risk:** Budget overrun; unplanned financial exposure

**24-Hour Budget Visibility Lag:**
- Budget data synced daily (after 5 PM, implied)
- Users ordering in morning see previous day's budget status
- No intra-day budget refresh
- **Impact:** Budget forecasting uncertainty; potential double-booking of same budget allocation

**Manual Invoice Matching:**
- Order-to-invoice correlation not visible in MerchTank workflow
- Reconciliation likely manual (via PO number or order number matching in Oracle)
- No automated feedback loop (invoice status not reflected in MerchTank order record)
- **Risk:** Invoice payment delays; reconciliation errors

**Co-Op Billing Complexity:**
- Cost-split logic not enforced at order time
- Manual accounting adjustments required post-order
- Wholesaler invoicing separate from MerchTank (no visibility into receivables)
- **Risk:** Billing errors; incorrect cost allocation

### Data Quality Issues

**Budget Allocation Accuracy:**
- Source of budget data in Oracle unclear
- Allocation methodology not documented (monthly vs. quarterly vs. annual bucketing unknown)
- No validation of budget totals in MerchTank against Oracle GL

**Order-to-Invoice Reconciliation:**
- No automated matching visible
- Historical reconciliation relies on Excel (per [[merchtank|MerchTank]] assessment)
- Aging invoice reports likely manual

## Salesforce B2B Commerce Integration (Planned)

**Phase 2 — Integration & Automation (Months 4-6, Target Q3 2026):**

**Objective:** Implement [[oracle-erp-integration|real-time Oracle ERP data sync]] in Salesforce B2B Commerce

**Deliverables:**
1. **Budget Allocation Sync API** — Real-time API call to Oracle to fetch current budget per brand
2. **Budget Display Component** — LWC component displaying available budget in Salesforce cart
3. **Budget Enforcement Rule** — Validation rule preventing order placement if exceeds budget
4. **Co-Op Billing Logic** — Pricing/promotion rule embedding cost-split logic
5. **Order-to-Invoice Reconciliation** — Salesforce Order Management integration with Oracle AP module
6. **Real-Time Budget Tracking** — Report showing budget utilization (Ordered, Shipped, Remaining) without batch lag

**Technical Approach:**
- Middleware (Mulesoft or Salesforce MuleSoft Cloud) for Oracle API calls
- Salesforce Platform Events for budget change notifications (optional, for real-time sync)
- Custom Apex extensions for pricing rule evaluation (co-op billing logic)
- Salesforce Order Management for order-to-invoice correlation

**Benefits vs. Current State:**
- **Budget Visibility:** Real-time (vs. 24-hour lag)
- **Budget Enforcement:** Automatic at order time (vs. manual post-order)
- **Order Status:** Linked to Oracle invoicing (vs. disconnected)
- **Co-Op Billing:** Automatic rule evaluation (vs. manual accounting adjustment)
- **Audit Trail:** Full Salesforce audit log (vs. manual Excel tracking)

## Integration Assessment Summary

| Aspect | Current State | Target State | Risk Level |
|--------|---------------|--------------|-----------|
| Budget Sync | Daily batch, 24h lag | Real-time API | Medium (requires API stability) |
| Budget Enforcement | Manual (post-order) | Automatic (order-time validation) | Low (standard Salesforce feature) |
| Invoice Matching | Manual in Oracle | Automated via Salesforce OM | High (requires 3-way match logic) |
| Co-Op Billing | Manual accounting | Automatic pricing rule | High (complex cost-split logic) |
| Data Quality | Moderate (Excel used) | High (Salesforce audit trail) | Low (improvement opportunity) |
| Latency | 24-48 hours | Real-time | Medium (depends on middleware) |

## Related Pages

**Platforms:**
- [[salesforce-b2b-commerce|Salesforce B2B Commerce]] — Target platform for Salesforce migration
- [[merchtank|MerchTank]] — Current merchandise ordering system (integrates with Oracle)

**Integrations:**
- [[oracle-erp-integration|Oracle ERP Integration]] — Detailed integration architecture and design

**Entities:**
- [[boston-beer-company|Boston Beer Company]] — Operator of Oracle ERP

## Notes

- Oracle ERP is **mission-critical financial system**; any integration work must be carefully tested and validated
- The **24-hour budget visibility lag** is operationally acceptable for merchandise ordering (not real-time enough for complex supply chains, but sufficient for promotional merchandise)
- The **co-op billing logic is complex** and should be treated as Phase 2 priority (after core ordering is stable in Phase 1)
- **No direct technical documentation of Oracle integration** was available in meeting recordings; recommend early integration discovery session with BBC IT/Finance to confirm:
  - Current Oracle data model (budget structure, co-op billing setup)
  - API availability (REST, SOAP, or database-level integration)
  - Current batch job schedule and lag tolerance
  - Approval process for new integrations (IT governance)
- The **invoice matching workflow** is likely standard Oracle AP three-way match; needs confirmation with BBC Finance on how MerchTank order numbers flow to Oracle PO/Receipt tables
