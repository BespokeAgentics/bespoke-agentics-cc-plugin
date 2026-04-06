---
type: gap
client: boston-beer-company
status: open
severity: critical
category: financial-operations
related-feature: "[Order Management]([[feature|order-management]])"
resolution-approach: custom-dev
created: 2026-04-06
updated: 2026-04-06
sources:
  - "[[meeting|01-merchtank-overview]] Gap W4-G1"
  - "[[meeting|03-custom-requests]] Gap W2-G1"
  - "[[meeting|04-fulfillment-demo]] Co-op Billing"
tags: co-op, cost-sharing, wholesaler-billing, financial-impact, critical-blocker
---

# Gap: Co-op Billing / Cost Sharing with Wholesaler

## Description

MerchTank allows users to split order costs with wholesalers on specific items (e.g., wholesaler pays 50% of tap handle costs). When a co-op order is placed, the system tracks the cost split and generates separate billing records: one for BBC, one for the wholesaler. The wholesaler is then invoiced for their portion through the accounts payable system.

Salesforce B2B Commerce has no native co-op billing capability. This is a significant financial and operational function that affects budget calculations, invoicing, and downstream financial reconciliation.

## Current State

**MerchTank Co-op Model:**
- Users can designate line items as "co-op" during checkout
- Co-op items have a pre-established cost split (e.g., "Tap Handle Blue — Wholesaler covers 50%")
- Checkout calculates BBC portion and wholesaler portion separately
- Order captures both amounts for later invoicing
- Rootstock ERP receives order data and generates invoices:
  - BBC invoice for BBC portion
  - Wholesaler invoice for wholesaler portion
- Finance team reconciles co-op charges back to the wholesaler (possibly via SAP AP)
- Co-op arrangements are pre-established between BBC and wholesalers; not negotiated per-order

**Critical Business Requirements:**
- [[meeting|04-fulfillment-demo]] Critical Req #16: "Co-op billing designation with wholesaler"
- [[meeting|04-fulfillment-demo]] Critical Req #23: "Co-op costs with wholesaler"
- [[meeting|04-fulfillment-demo]] Critical Req #26: "Co-Op/Billable Reporting for Accounting — must include: ship date, cost center, SKU info, description, billable amount, QTY of POS ordered"

## Target State

**Salesforce Co-op Architecture:**
- Custom Object `CoopAgreement__c`:
  - Fields: Account__c (lookup to wholesaler), Product2__c (lookup), Wholesaler_Cost_Percent__c (number, 0-100), BBC_Cost_Percent__c (formula: 100 - Wholesaler_Percent), Active__c (checkbox), Start_Date__c, End_Date__c
  - Unique constraint: Account + Product + Effective_Date
  - Records: One per wholesaler + product combination with active cost split

- Custom Object `OrderCoopAllocation__c`:
  - Master-Detail to OrderItemSummary (or custom Order_Item__c if needed)
  - Fields: CoopAgreement__c (lookup), Total_Line_Amount__c (currency), BBC_Amount__c (formula), Wholesaler_Amount__c (formula), Wholesaler_Account__c (lookup, denormalized from CoopAgreement)
  - Rollup on OrderSummary: Total_Co-op_Wholesaler_Amount__c, Total_BBC_Amount__c

- Checkout Integration:
  - Custom Cart Calculate API step that:
    - Queries CoopAgreement for each line item
    - Applies cost split based on item/account/date
    - Populates OrderCoopAllocation records on order submission
  - Order detail LWC shows co-op designations and amounts per line

- Billing Integration:
  - Platform Event `OrderCoopAllocationCreatedEvent` published on order submit
  - Rootstock integration subscriber receives event and generates separate invoices
  - Finance report (custom LWC or Salesforce Report) aggregates co-op amounts by wholesaler for billing/reconciliation

**Integration with [[gap|budget-management-engine]]:**
- Open Question: Does full line amount decrement from BBC budget, or only BBC portion?
- Assumption (pending confirmation): Full amount decrements from BBC budget (BBC bears inventory risk)

## Gap Analysis

### What Salesforce Lacks

Salesforce B2B Commerce provides no co-op billing:
- No line-item cost split capability
- No co-op configuration objects
- Cart Calculate API has no co-op split hooks
- OrderItemSummary has no co-op fields
- No invoice generation with split amounts

### Root Cause

B2B Commerce is designed for straightforward B2B ordering: one buyer, one price, one invoice. Co-op billing is a B2B variant that requires:
1. Pre-configured cost split rules (per customer + product)
2. Dynamic calculation at order time
3. Separate invoicing to multiple parties
4. Financial reconciliation workflows

This is specialized domain logic that requires custom development.

### Impact

**Without Resolution:**
- Users cannot designate co-op items → All costs charged to BBC
- Wholesalers are not invoiced for their portion → Revenue leakage
- Budget doesn't account for co-op split → Budget reporting is inaccurate
- Invoicing is manual: Finance team must manually split charges and create wholesaler invoices
- Financial reconciliation is broken → Accounts payable cannot reconcile
- Reporting for finance is manual: No automated co-op billing report for accounting

## Resolution Options

### Option 1: Custom Co-op Objects + Checkout Extension (RECOMMENDED)

**Approach:**
1. Create `CoopAgreement__c` object as designed above
2. Create `OrderCoopAllocation__c` object to track cost splits per order
3. Extend checkout Cart Calculate API with custom Flow:
   - For each line item, query CoopAgreement (Account + Product + Date)
   - If found, calculate BBC and Wholesaler amounts
   - Create OrderCoopAllocation records on order finalization
4. Extend OrderItemSummary or create custom Order_Item__c with co-op fields:
   - CoopAgreement__c (lookup)
   - BBC_Amount__c, Wholesaler_Amount__c (formulas or fields)
5. Order detail LWC displays co-op information per line item
6. Custom Report or LWC dashboard for Finance:
   - Co-op charges aggregated by Wholesaler and date range
   - Used for invoicing and reconciliation
7. Platform Event integration:
   - OrderCoopAllocationCreatedEvent published on order submit
   - Rootstock integration subscribes and generates invoices

**Effort:** L (Large) — 3-4 weeks
- Week 1: Object design, CoopAgreement CRUD, data migration
- Week 2: Cart Calculate API integration, OrderCoopAllocation logic
- Week 3: Order detail LWC, Finance reporting
- Week 4: Rootstock integration, testing, documentation

**Advantages:**
- Full control over co-op rules
- Audit trail: Every co-op split is recorded
- Integrates tightly with checkout flow
- Supports future enhancements (e.g., wholesaler-specific cost splits, approval workflows)
- Clear invoicing path: Separate invoice amounts for BBC and wholesaler

**Risks/Dependencies:**
- Data migration: CoopAgreements must be migrated from MerchTank
- Rootstock API: Must support receiving co-op split data and generating separate invoices
- Cart Calculate complexity: Adding cost split logic to cart recalculation must not impact performance
- Budget integration: Must confirm whether full amount or BBC portion affects budget (see Gap W2-G1)

**Trade-offs:**
- Requires Rootstock integration development
- Ongoing maintenance of checkout logic
- Finance team must be trained on co-op reporting

---

### Option 2: Post-Order Co-op Processing (ERP-Driven)

**Approach:**
- Order is placed with all items at full BBC cost (no co-op designation in Salesforce checkout)
- Rootstock ERP receives order data and applies co-op rules based on ERP master data
- ERP generates separate invoices (BBC + Wholesaler)
- Finance team reconciles using ERP reports, not Salesforce

**Effort:** M (Medium) — 2 weeks
- Week 1: Rootstock ERP integration design, API review
- Week 2: Integration development, testing

**Advantages:**
- Minimal Salesforce customization
- ERP remains single source of truth for co-op rules
- Reduces Salesforce maintenance burden
- Aligns co-op logic with ERP financial processes

**Risks/Dependencies:**
- ERP must have co-op split logic (confirm with BBC IT)
- Salesforce has no visibility into co-op amounts → Budget and reporting are inaccurate
- Users cannot see co-op split before checkout → May confuse users
- If ERP is unavailable, co-op processing is delayed or manual

**Trade-offs:**
- Salesforce is not source of truth for co-op data
- Budget reporting is incomplete (doesn't show wholesaler portion)
- Finance must manage co-op rules in two systems (ERP + Salesforce)
- Users lose transparency into cost sharing

---

### Option 3: Hybrid Model: Co-op Configuration in Salesforce, Processing in ERP

**Approach:**
- `CoopAgreement__c` objects created in Salesforce for visibility and management
- Checkout shows co-op designation but does NOT calculate amounts
- Order submitted to ERP with co-op flag (e.g., "Line Item: Tap Handle Blue, Quantity: 100, Co-op: YES")
- ERP applies cost split based on its own rules and generates invoices
- Salesforce displays co-op designation but amount calculations come from ERP

**Effort:** M (Medium) — 2-3 weeks
- Week 1: CoopAgreement CRUD, checkout co-op designation
- Week 2-3: ERP integration, invoice linkage

**Advantages:**
- Balanced approach: Salesforce owns co-op configuration, ERP owns financial processing
- Users see co-op designation at checkout
- ERP remains single source for financial amounts
- Reduces custom Apex development

**Risks/Dependencies:**
- Co-op amounts in ERP don't feed back to Salesforce → Reporting still incomplete
- Must keep CoopAgreement in Salesforce synchronized with ERP rules
- If rules differ, confusion and reconciliation issues

**Trade-offs:**
- Data duplication: Co-op rules in two systems
- Salesforce reporting still incomplete
- Requires strong governance around master data synchronization

---

## Recommended Approach

**Option 1 (Custom Co-op Objects + Checkout Extension)** is recommended because:

1. **Visibility:** BBC needs to see cost splits at checkout time for transparency to users.
2. **Budget Integration:** Co-op amounts must feed into [[gap|budget-management-engine]] for accurate spending tracking.
3. **Control:** Salesforce has clear record of every co-op split for audit and compliance.
4. **Reporting:** Finance team gets automated co-op reporting (Critical Req #26) without manual ERP queries.

**Option 2** becomes attractive if Rootstock ERP already handles all co-op logic and BBC is comfortable with Salesforce having no visibility (unlikely given Critical Req #26).

## Effort Estimate

**Option 1:** Large (L)
- Effort: 3-4 weeks (120-160 hours)
- Confidence: Medium-High (co-op rules are well-defined; integration with checkout is standard; risk is Rootstock API)
- Unknowns: CoopAgreement count and data quality; Rootstock invoice generation complexity; Budget impact (full vs. partial amount)

**Option 2:** Medium (M)
- Effort: 2 weeks (80 hours)
- Confidence: Medium (depends on Rootstock capability)
- Unknowns: Rootstock co-op processing capability; integration complexity

**Option 3:** Medium (M)
- Effort: 2-3 weeks (80-120 hours)
- Confidence: High (straightforward Salesforce + ERP integration)
- Unknowns: Rule synchronization overhead; reporting completeness acceptable to Finance

## Dependencies

### Must Happen Before
- [[decision|Budget-Integration-with-CoOp]] — Budget validation must clarify whether full or BBC-only amount affects budget
- [[gap|budget-management-engine]] — Co-op amounts must integrate with budget tracking

### Must Happen Alongside
- [[feature|checkout-flow-budget-validation]] — Checkout must validate both budget and co-op amounts
- [[feature|invoice-access-and-sync]] — Rootstock invoice generation must handle co-op splits

### Blocks
- [[feature|order-management]] — Order submission is incomplete without co-op designation
- [[feature|finance-reporting]] — Critical Req #26 (co-op billable reporting) requires this gap resolved

## Evidence

### Meeting 1: MerchTank Overview (Dec 4, 2025)
**Gap W4-G1: Co-op Billing / Cost Sharing with Wholesaler**
- Severity: Critical
- Description: "MerchTank allows users to split costs on specific items with the wholesaler (e.g., wholesaler pays 50% of tap handles). The wholesaler is then invoiced for their portion. Salesforce B2B Commerce has no native co-op billing."
- Impact: "Co-op arrangements are a significant part of BBC's relationship with distributors and affect budgets."
- Recommendation: "Custom Co-op Object + Checkout Extension...with checkout logic that splits order amounts and generates separate billing records. (~L effort, 2-3 weeks)"

### Meeting 3: Custom Requests (Mar 9, 2026)
**Critical Requirements:**
- Req #16: "Co-op billing designation with wholesaler"
- Req #23: "Co-op costs with wholesaler"

### Meeting 4: Fulfillment Demo (Mar 25, 2026)
**Critical Requirements:**
- Req #26: "Co-Op/Billable Reporting for Accounting — must include: ship date, cost center, SKU info, description, billable amount, QTY of POS ordered"

## Validation Notes

SFCC Validation Report confirms:
- "Salesforce B2B Commerce does not have co-op billing"
- "Custom objects are required for co-op tracking"
- "Rootstock invoice API should support split amounts"

## Open Questions

1. **Budget Impact:** When a co-op order is placed, does the full line amount decrement from BBC budget, or only the BBC portion?
   - *Impact if answered wrong:* Budget calculation logic changes; CoopAllocation must integrate tightly with budget objects
   - *Owner:* BBC Finance/Procurement

2. **CoopAgreement Scope:** How many co-op agreements exist today? Are they stable or frequently renegotiated?
   - *Impact if answered wrong:* Data migration effort and ongoing maintenance burden change
   - *Owner:* BBC Procurement/Finance

3. **Wholesaler Invoicing:** How are wholesalers currently invoiced for co-op portions? Is it a separate AR/AP flow in SAP, or integrated with order invoicing?
   - *Impact if answered wrong:* Rootstock integration design changes
   - *Owner:* BBC Finance

4. **Approval Workflow:** Do co-op orders require approval before submission, or are they auto-approved if within co-op agreement?
   - *Impact if answered wrong:* Checkout flow adds approval complexity
   - *Owner:* BBC Procurement

## Related Gaps

- [[gap|budget-management-engine]] — Co-op amounts must respect budget constraints
- [[gap|invoice-access-and-sync]] — Separate invoices generated for BBC and wholesaler

## Status & Next Steps

**Status:** Open (design phase)

**Next Steps:**
1. Schedule co-op rules workshop with BBC Finance/Procurement
2. Confirm whether full or BBC-only amount affects budget
3. Validate CoopAgreement data and count
4. Review Rootstock invoice generation capability
5. Finalize CoopAgreement__c and OrderCoopAllocation__c schema
6. Begin checkout extension development
7. Start Rootstock integration design
