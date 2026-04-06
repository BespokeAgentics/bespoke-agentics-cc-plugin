---
type: feature
client: boston-beer-company
status: draft
category: budget
decision: custom
effort: L
priority: P1
created: 2026-04-06
updated: 2026-04-06
sources:
  - /sessions/sweet-trusting-ride/mnt/Vendale-Agentics/BostonBeerCompany/meetings/01-merchtank-overview/analysis/gap-analysis-sample-bbc-merchtank.md
  - /sessions/sweet-trusting-ride/mnt/Vendale-Agentics/BostonBeerCompany/meetings/03-custom-requests/analysis/gap-analysis-bbc-custom-requests-meeting.md
  - client-email-merchtank-feeder-systems-2026-04-06
tags:
  - budget-management
  - financial-controls
  - procurement
  - email
---

# Brand-Level Budget Tracking

## Description

MerchTank tracks budget allocations per brand family per wholesaler per user. Each sales rep or distributor is assigned a budget for each brand (Samuel Adams, Twisted Tea, Angry Orchard, etc.) that limits their merchandise spending. The system displays budget visibility showing: initial allocation, amount ordered, amount shipped, and remaining balance. This is a core financial control mechanism that prevents overspending and provides transparency into merchandise spending across BBC's brand portfolio.

## Current Implementation

**User Workflow:**
- Users access a budget dashboard that shows per-brand budget summary
- Dashboard displays columns: Brand Family, Initial Budget, Amount Ordered, Amount Shipped, Remaining Balance
- Budgets are broken down by wholesaler context (each wholesaler sees only their allocated budget)
- Budget checks occur during checkout — orders cannot exceed remaining balance (hard stop enforcement)
- Budgets roll over annually (reference to 2026 turnover)

**Business Rules:**
- Budget is allocated per brand family per wholesaler per user
- Annual allocation resets on a fiscal year boundary
- "Amount Ordered" includes pending and open orders
- "Amount Shipped" only counts orders that have shipped (not all orders placed)
- Budget enforcement prevents checkout when order would exceed remaining balance
- Some users have multiple VW assignments and thus multiple budget allocations

**Current Technical Implementation:**
- Budget data stored in MerchTank SQL Server database
- Budget lookup occurs during cart/checkout validation
- Real-time decrement as orders are placed
- Dashboard component queries budget tables and calculates remaining balance

**Systems Involved:**
- MerchTank backend, budget database tables, checkout validation logic
- **Anaplan** — BBC financial reporting system; source of brand budget allocations (NOT SAP/Oracle for OPEX budgets)
- Brand budgets pulled from Anaplan → loaded into template → fed to MT to populate budgets
- Budget usage reporting pulled from MT during LE cycles (~5x/year) → Anaplan updated

## Target Implementation

Salesforce B2B Commerce has NO native budget management capability. This entire feature must be built as a custom solution.

**Proposed Salesforce Architecture:**

1. **Custom Objects:**
   - `Brand_Budget__c`: Master record per brand family per wholesaler per user
     - Fields: Brand__c (lookup to Product Family or custom Brand object), Wholesaler__c (lookup to Account), User__c (lookup to User), Fiscal_Year__c, Initial_Amount__c, Current_Balance__c
   - `Budget_Transaction__c`: Audit trail of budget debits/credits
     - Fields: Budget__c (master-detail), Transaction_Type__c (Order, Ship, Adjustment, Reversal), Amount__c, Related_Order__c, Created_Timestamp__c

2. **Cart Validation:**
   - Apex class implementing `sfdc_checkout.CartValidation` interface
   - Queries Brand_Budget__c for current user's allocated budget
   - Sums all items in cart by brand, checks against available balance
   - Returns validation errors if any brand would exceed budget

3. **Budget LWC Dashboard:**
   - Custom component displays brand budget summary table
   - Real-time calculation: Initial_Amount - (sum of shipped orders) = remaining balance
   - Sortable/filterable by brand, wholesaler
   - Highlights low-balance brands (warning threshold)

4. **Automation:**
   - Record-Triggered Flow on Order: When order reaches "Shipped" status, create Budget_Transaction__c record
   - Async process to decrement Brand_Budget__c balance nightly based on shipped orders

## Gaps & Risks

**Gap BBT-G1: No Native B2B Commerce Budget Management**
- Severity: Critical
- Resolution: Custom objects + checkout validation as described above
- Effort: L (3-4 weeks)
- Risk: Concurrent budget consumption could cause race conditions if multiple orders placed simultaneously

**Gap BBT-G2: Enforcement Behavior Unconfirmed**
- Severity: High
- Current behavior assumed to be "hard stop" (prevents checkout if budget exceeded)
- Alternative: Soft warning (allows checkout with approval)
- Impact: If soft warning is the actual requirement, approval process integration needed
- Resolution: Confirm with BBC business stakeholders before design

**Gap BBT-G3: Budget Consumption Timing**
- Severity: Medium
- Current: "Amount Ordered" may include pending orders or only confirmed orders
- Current: "Amount Shipped" explicitly only counts shipped orders
- Risk: Difference affects checkout validation logic
- Resolution: Clarify with BBC whether budget is consumed at order creation or at shipment

**Gap BBT-G4: Anaplan Budget Integration**
- Severity: High
- ⚠️ Updated 2026-04-06 per client email: Budget source is **Anaplan**, not Oracle ERP. BBC states: "We do NOT maintain our budgets for OPEX in SAP, it lives here [Anaplan]."
- Current: Brand budgets are pulled from Anaplan → loaded into a template → fed to MerchTank. Budget usage reporting pulled from MT during LE cycles (~5x/year) → Anaplan updated.
- Impact: Salesforce must integrate with Anaplan (not Oracle) for budget sync, or manage budgets standalone with periodic Anaplan reconciliation.
- Resolution: Define Anaplan integration approach (API sync, file-based import, or manual template load)

## Dependencies

- [[virtual-warehouse-model|Virtual Warehouse Model]] (if budgets are per-VW)
- [[buyer-account-model|Buyer Account Model]] for user/wholesaler mapping
- [[shopping-cart-with-budget-enforcement|Shopping Cart]] implementation (cart validation hook)
- Order object and Order lifecycle

## Open Questions

1. Is budget enforcement a hard stop or a soft warning with approval?
2. ~~Are budgets managed independently in MerchTank or synced from Oracle ERP?~~ **ANSWERED (2026-04-06):** Budgets originate in **Anaplan**, not Oracle ERP. Loaded into MT via template. Usage reported back to Anaplan ~5x/year during LE cycles.
3. When is budget "consumed" — at order creation or at shipment?
4. How are budget resets triggered annually — automatic on a date or manual?
5. Can budgets be adjusted mid-year? By whom? Is there an approval workflow?
6. Are brand budgets the only budget level, or are there wholesaler-level or user-level budgets?
7. **NEW:** What is the Anaplan → MerchTank template format? (CSV, API, manual entry?) This determines Salesforce integration approach.
8. **NEW:** What are "LE cycles"? How frequently (~5x/year) and what triggers them?

## ⚠️ Contradiction Notice — 2026-04-06

This client email contradicts the wiki's previous assumption about the budget data source:

**Previous Information** (from meeting analysis inferences):
Oracle ERP is the system of record for brand-level budget allocations. Budget data synced daily from Oracle.

**New Information** (from client email, Finance department):
"Anaplan — This is our BBC financial reporting system and is a widely used enterprise solution. We do NOT maintain our budgets for OPEX in SAP, it lives here. Brand budgets get pulled from Anaplan and loaded into a template. This template gets fed to MT to populate the budgets. Reporting on budget usage gets pulled from MT during our LE cycles (about 5x per year) and Anaplan gets updated."

**Resolution**: Anaplan is the budget source of truth, not Oracle ERP. The Oracle ERP integration pages and entity records must be updated to reflect this. The Salesforce integration strategy for budgets should target Anaplan (or the template mechanism) rather than Oracle.

**Updated by**: client-email-merchtank-feeder-systems-2026-04-06

## Evidence from Email: MerchTank Feeder Systems (2026-04-06)

Source: Client email — Finance department notes on MerchTank feeder systems
Date: 2026-04-06

**Budget source is Anaplan, not Oracle ERP:**
- Anaplan is BBC's financial reporting system for OPEX budgets
- Brand budgets are pulled from Anaplan → loaded into a template → fed to MerchTank
- Budget usage reporting is pulled from MerchTank during LE cycles (~5x/year) → Anaplan is updated
- This is a bidirectional flow: Anaplan → template → MT (allocations), MT → Anaplan (usage reporting)

## Evidence

**Meeting 1 (MerchTank Overview):**
- "Users view a budget dashboard that shows: initial budget allocation, amount ordered, amount shipped, and remaining balance — broken down by brand family for the selected wholesaler."
- "Budgets roll over annually"
- "Budget is checked during checkout to prevent overspending"
- "Without this, orders cannot be validated against budgets, and users lose visibility into spending"

**Meeting 3 (Custom Requests):**
- "Budget Approval" field on custom request form indicates budget tracking at request level
- Mention of "Budget Approval" suggests approval workflow may exist
