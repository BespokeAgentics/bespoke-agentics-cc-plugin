---
type: gap
client: boston-beer-company
status: open
severity: critical
category: core-commerce
related-feature: "[Order Management]([[feature|order-management]])"
resolution-approach: custom-dev
created: 2026-04-06
updated: 2026-04-06
sources:
  - "[[meeting|01-merchtank-overview]] Gap W2-G1, W2-G2"
  - "[[meeting|03-custom-requests]] Gap W2-G1"
  - "[[meeting|04-fulfillment-demo]] Order Management"
  - client-email-merchtank-feeder-systems-2026-04-06
tags: budget, financial-control, checkout-validation, critical-blocker, email
---

# Gap: Budget Management Engine

## Description

Boston Beer Company's MerchTank platform enforces per-wholesaler, per-brand family budget constraints at order time. Salesforce B2B Commerce has no native budget allocation, tracking, or enforcement system. This is a critical business function that affects every order and is a core value proposition of the current system.

Users currently view a budget dashboard showing: initial allocation, amount ordered, amount shipped, and remaining balance — all broken down by brand family per wholesaler. Budgets roll over annually. Budget is validated during checkout to prevent overspending.

Without a custom budget engine, orders cannot be validated against available funds, and users lose visibility into spending commitments.

## Current State

**MerchTank Budget Model:**
- Budget tracked at the wholesaler + brand family level
- Budget is allocated annually and decrements on order placement
- Dashboard shows: Initial Budget | Amount Ordered | Amount Shipped | Remaining Balance
- Checkout validates cart total against remaining budget before submission
- Budget rules are relatively straightforward (annual allocation with simple decrement, no complex accruals)
- Budget data lives in MerchTank's SQL Server database

**Key Workflows:**
- Procurement sets annual budget per wholesaler/brand family
- Sales reps check available budget before ordering
- Co-op orders may have split costs (see [[gap|co-op-billing]])
- Budget is consumed on order, regardless of shipment status (initially)

**Budget Source (confirmed 2026-04-06):**
- Brand budgets originate in **Anaplan** (BBC's financial reporting system for OPEX), NOT Oracle/SAP
- Budgets pulled from Anaplan → loaded into template → fed to MerchTank
- Budget usage reporting pulled from MerchTank during LE cycles (~5x/year) → Anaplan updated
- This changes the integration strategy: Salesforce must integrate with Anaplan (or replicate the template-based load process) for budget data

## Target State

**Salesforce Budget Architecture:**
- Custom object suite: `Budget__c` (master record), `BudgetAllocation__c` (per brand family per account), `BudgetTransaction__c` (debit/credit ledger)
- Budget allocation tied to Account (wholesaler) and Brand Family (custom field or picklist)
- Real-time dashboard showing allocation → ordered → shipped → remaining
- Cart validation Flow that prevents checkout if order exceeds remaining budget
- Transaction audit trail for finance reconciliation
- Near-real-time refresh after order placement

**Design Considerations:**
- Budget must decrement atomically during checkout (prevent concurrent overallocations)
- Partial shipments may affect budget reporting (shipped vs. ordered distinction)
- Co-op split amounts must not exceed brand budget per order
- Budget administrators need visibility and edit capability for adjustments/resets

## Gap Analysis

### What Salesforce Lacks

Salesforce B2B Commerce provides no budget management:
- No out-of-the-box object for budget allocation or tracking
- Cart Calculate API does not enforce budget constraints
- Checkout API does not have budget validation hooks
- No standard dashboard component for budget visibility per buyer account

### Root Cause

B2B Commerce is designed for standard e-commerce patterns (account-wide spending limits, if any, managed in Approval Processes). BBC's model is more granular: budget is tied to brands, users, and time periods (annual rollover). This requires custom domain objects and business logic.

### Impact

**Without Resolution:**
- Orders can be placed beyond allocated budget
- Users have no spending visibility → financial surprises
- Procurement loses control over brand spend
- Finance cannot reconcile spending against budget allocations
- Ordering decisions are not financially constrained

## Resolution Options

### Option 1: Custom Budget Object Suite (RECOMMENDED)

**Approach:**
1. Build `Budget__c` master object with fields: Account (lookup), BudgetYear (year picklist/field), TotalAllocation (currency), CurrentBalance (currency)
2. Build `BudgetAllocation__c` detail object: Brand_Family (picklist), InitialAmount (currency), Ordered (rollup), Shipped (rollup), RemainingBalance (formula)
3. Build `BudgetTransaction__c` for audit trail: Budget__c lookup, Type (Order/Shipment/Adjustment), Amount (currency), OrderSummary (lookup), CreatedDate
4. Apex Trigger on Order/OrderSummary: On checkout, query BudgetAllocation for the brand families in the cart, decrement balance, create transaction records
5. Cart Calculate API Extension: Custom Flow that validates budget during cart recalculation
6. Custom LWC Dashboard: Displays allocation table (Brand | Initial | Ordered | Shipped | Remaining) with refresh on every order placement

**Effort:** L (Large) — 3-4 weeks
- Week 1: Design and create objects; build Apex trigger
- Week 2: Cart validation Flow and checkout integration
- Week 3: LWC dashboard component and testing
- Week 4: Performance testing, edge case handling, data migration prep

**Advantages:**
- Full control over budget rules and enforcement
- Tight integration with checkout flow
- Audit trail for compliance and reconciliation
- Scalable to more complex rules (per-user limits, quarterly budgets, etc.)

**Risks/Dependencies:**
- Requires careful Apex coding to prevent concurrent overallocation (use pessimistic locking or savepoints)
- Cart validation must fire synchronously; if slow, impacts checkout UX
- Budget data migration from SQL Server is non-trivial

**Trade-offs:**
- Ongoing maintenance of custom code
- Requires Load/Performance testing to ensure checkout latency is acceptable
- More complex than a third-party solution

---

### Option 2: AppExchange Budget Solution

**Approach:**
- Evaluate available solutions (e.g., Copado, Kimble, other ISVs)
- Integrate with B2B Commerce via API calls in Flow

**Effort:** M (Medium) — 2-3 weeks
- Week 1: Evaluate 3-5 solutions; determine fit against BBC's rules
- Week 2-3: License, configure, integrate with checkout Flow

**Advantages:**
- Reduces custom code maintenance
- May provide additional features (budget forecasting, analytics) as bonus
- Vendor support for bug fixes

**Risks/Dependencies:**
- Few AppExchange solutions are purpose-built for B2B Commerce budget enforcement
- Licensing cost per user or transaction may be significant
- Vendor viability and roadmap alignment are unknowns
- Integration latency could impact checkout performance

**Trade-offs:**
- Less control over enforcement rules
- Ongoing licensing costs
- Potential dependency on vendor for feature enhancements

---

### Option 3: External Budget System Integration (Anaplan)

**Approach:**
- ~~If BBC has an ERP system (Rootstock, SAP) that already tracks budgets, integrate via API~~ **Updated 2026-04-06:** BBC uses **Anaplan** for budget management (not Oracle/SAP)
- Salesforce calls Anaplan API at checkout to validate budget in real-time, or syncs budget data periodically from Anaplan
- Anaplan remains source of truth; Salesforce does not store budget state (or caches it)

**Effort:** M-L (2-4 weeks depending on ERP API availability)
- Week 1: Validate ERP API contract; design integration pattern
- Week 2-3: Build MuleSoft flow or custom Apex callout; test error handling
- Week 4: Performance validation; fallback strategy if ERP is unavailable

**Advantages:**
- Single source of truth for budget (ERP)
- Reduces data duplication
- Budget rules maintained in ERP where finance team manages them

**Risks/Dependencies:**
- ERP API must have budget validation endpoints (confirm with IT)
- Synchronous API calls at checkout = network latency impact
- If ERP is unavailable, checkout is blocked (need fallback strategy)
- ERP API changes could break Salesforce integration

**Trade-offs:**
- External system dependency introduces operational risk
- Requires robust error handling and fallback (cached budget, temporary cap, etc.)
- Less visibility in Salesforce (budget data stays in ERP)

---

## Recommended Approach

**Option 1 (Custom Budget Object Suite)** is recommended for initial launch because:

1. **Control:** BBC's budget rules are bespoke (annual allocation, brand-based, with co-op complexity). Custom objects allow exact rule enforcement.
2. **Speed:** Building custom objects is faster than evaluating and integrating a third-party solution.
3. **Integration:** Direct integration with Salesforce checkout flow and Order objects ensures synchronous, reliable enforcement.
4. **Future-Proofing:** If budget rules evolve (e.g., quarterly limits, regional budgets), custom objects are easier to extend than a third-party tool.

**Conditional:** If BBC's ERP (Rootstock) has a stable, performant budget validation API, **Option 3** becomes attractive as a Phase 2 enhancement (move budget source of truth to ERP, use Salesforce only for display).

## Effort Estimate

**Option 1:** Large (L)
- Effort: 3-4 weeks (120 hours)
- Confidence: High (standard Salesforce patterns; risks are well-known)
- Unknowns: Exact budget rules (annual-only or more complex?); co-op split logic complexity

**Option 2:** Medium (M)
- Effort: 2-3 weeks (80-120 hours)
- Confidence: Medium (depends on solution fit)
- Unknowns: Which solution is the best fit; licensing cost

**Option 3:** Medium-Large (M-L)
- Effort: 2-4 weeks (80-160 hours)
- Confidence: Medium (depends on ERP API availability and performance)
- Unknowns: ERP API contract; latency characteristics; fallback strategy

## Dependencies

### Must Happen Before
- [[decision|Order-Data-Model-Design]] — Budget objects must integrate with OrderSummary; schema design decision required
- [[decision|Co-op-Billing-Design]] — Co-op orders affect budget consumption logic; co-op design must finalize before budget implementation
- [[feature|checkout-flow]] — Checkout integration requires finalized checkout flow design

### Must Happen Alongside
- [[feature|budget-dashboard]] — Dashboard LWC development parallels budget object build
- [[feature|cart-validation]] — Cart Calculate API integration parallels object build

### Blocks
- [[feature|order-management]] — Orders cannot be submitted without budget validation
- [[meeting|04-fulfillment-demo]] — Financial reconciliation requires budget transaction audit trail

## Evidence

### Meeting 1: MerchTank Overview (Dec 4, 2025)
**Gap W2-G1: Per-Wholesaler/Per-Brand Budget Tracking**
- "Severity: Critical"
- "There is no out-of-the-box budget allocation, tracking, or enforcement in Salesforce B2B Commerce. This is a core business function that affects every order."
- Evidence: Current state shows budget dashboard with initial/ordered/shipped/remaining per brand family
- Resolution: Build Budget__c, BudgetAllocation__c, BudgetTransaction__c objects with Apex triggers

### Meeting 3: Custom Requests (Mar 9, 2026)
**Gap W2-G1: Brand-Level Budget Enforcement in Cart**
- Severity: High
- "Salesforce B2B Commerce does not have budget validation at cart time"
- Impact: "Users could exceed their allocated spend"
- Resolution: Custom Cart Calculate API integration with budget object lookup

### Meeting 4: Fulfillment Demo (Mar 25, 2026)
**Order Management Feature Inventory**
- Order-level budget enforcement requirement identified
- Co-op orders must respect budget constraints
- Budget visibility required in Order History and Order Detail views

## Validation Notes

SFCC Validation Report (Custom Requests, Meeting 3) confirms:
- "B2B Commerce does not have a native budget module"
- "Cart validation points exist for custom logic injection"
- "OrderSummary has no budget_spent__c field; must create custom field or object"

## Open Questions

1. **Budget Rules Complexity:** Are budget rules limited to annual allocation with simple decrement? Or are there quarterly limits, regional overrides, or other complex rules?
   - *Impact if answered wrong:* Custom rules could add 1-2 weeks to effort
   - *Owner:* BBC Finance/Procurement

2. **Co-op Budget Impact:** When a co-op order splits cost (e.g., wholesaler pays 50%), does the full amount decrement from budget, or only the BBC portion?
   - *Impact if answered wrong:* Budget calculation logic must be redesigned
   - *Owner:* BBC Procurement/Finance

3. **Budget Visibility During Shipment:** Is budget considered "consumed" on order or only when shipped?
   - *Impact if answered wrong:* BudgetTransaction__c ledger structure changes
   - *Owner:* BBC Finance

4. **Multi-Warehouse Budget:** Does budget allocation vary by fulfillment vendor, or is it brand-wide?
   - *Impact if answered wrong:* BudgetAllocation__c schema changes
   - *Owner:* BBC Procurement

## Related Gaps

- [[gap|co-op-billing]] — Co-op split amounts must respect budget constraints
- [[gap|program-window-time-gating]] — Budget must enforce per program if programs have separate budgets
- [[gap|checkout-flow-budget-validation]] — Checkout validation depends on budget objects (see Gap W4-G2)

## Status & Next Steps

**Status:** Open (design phase)

**Next Steps:**
1. Schedule budget rules workshop with BBC Finance/Procurement
2. Confirm budget rules complexity (annual-only vs. more complex)
3. Determine co-op budget impact (full amount or BBC portion only)
4. Finalize Budget__c, BudgetAllocation__c, BudgetTransaction__c schema
5. Begin Apex trigger and Cart Calculate API integration development
6. Build LWC dashboard component in parallel
