---
type: gap
client: boston-beer-company
status: open
severity: high
category: order-management
related-feature: "[Order Management]([[feature|order-management]])"
resolution-approach: custom-dev
created: 2026-04-06
updated: 2026-04-06
sources:
  - "[[meeting|03-custom-requests]] Gap W2-G3"
  - "[[meeting|04-fulfillment-demo]] Critical Req #9 (Out of Office Proxy)"
tags: proxy-ordering, delegate-ordering, manager-workflow, operational-blocker
---

# Gap: Proxy / Delegate Ordering

## Description

BBC's Procurement team regularly places orders on behalf of Sales Reps using the rep's Virtual Warehouse (VW) and budget allocation. This is a core operational pattern where a manager/admin orders merchandise under a user's VW context (consuming that user's inventory and budget, not the manager's).

Salesforce B2B Commerce does not natively support "order on behalf of" for internal users within the same organization. The standard B2B Commerce pattern is: users place orders for themselves using their own catalog entitlements and budget.

This gap affects Procurement's ability to execute their primary function.

## Current State

**MerchTank Proxy Ordering:**
- Procurement users can select a Sales Rep's VW and place orders in that context
- Order is placed from the Sales Rep's VW inventory (not Procurement's)
- Budget consumed from Sales Rep's budget allocation (not Procurement's)
- Order appears in Sales Rep's order history
- Manager/admin can reassign approval authority during out-of-office periods (Critical Req #9)

**Critical Business Requirement:**
- [[meeting|04-fulfillment-demo]] Critical Req #9: "Out of Office Proxy — admin access to change approver. This requires the ability for a Buyer Manager to reassign approval authority during absence."

## Target State

**Salesforce Proxy Ordering Architecture:**
- Custom context object: `OrderingContext__c`:
  - Fields: Performing_User__c (lookup to User, who is placing the order), Acting_As_User__c (lookup to User, whose VW/budget is being used), Context_Type__c (picklist: Self/Proxy), Start_Date__c, End_Date__c (for temporary proxy)
  - Permission Set: "Proxy Ordering" allows designated users (Procurement) to create OrderingContext records

- Cart/Order Integration:
  - WebCart.Acting_User__c (formula or custom field): Populated from OrderingContext
  - Order.Original_Ordering_User__c (lookup): Tracks who physically placed the order
  - Order.Acting_As_User__c (formula): Tracks whose context was used (for budget/VW tracking)

- Procurement Console LWC: `c-proxy-ordering-console`
  - Dropdown to select Sales Rep (whose VW to order from)
  - Date range selector (optional, for temporary proxy setup)
  - Confirmation message showing VW being ordered from and budget constraints
  - Redirects to normal cart/checkout after selection

- Approval Routing Override:
  - Approval Process configured to route based on Acting_As_User, not Performing_User
  - Manager can reassign approval authority to another manager via custom LWC (temporary delegation)
  - `ApprovalDelegation__c` custom object:
    - Fields: Primary_Approver__c, Temporary_Approver__c, Start_Date__c, End_Date__c
    - Used in approval process formula to select current approver

## Gap Analysis

### What Salesforce Lacks

Salesforce B2B Commerce Experience Cloud does not provide:
- "Order on behalf of" functionality for internal users
- Order context switching (user A places order as user B)
- Budget inheritance in proxy scenarios
- Approval routing based on acting-as context
- Temporary delegation of approval authority

### Root Cause

B2B Commerce is designed for self-service commerce: each user orders for themselves. Proxy ordering is an administrative/operational pattern common in internal B2B platforms but not a standard commerce feature. BBC's procurement workflow requires custom objects and order context logic.

### Impact

**Without Resolution:**
- Procurement team cannot place orders for Sales Reps
- Sales Reps must place all orders themselves → Procurement loses control over inventory allocation
- Procurement cannot respond to time-sensitive orders from field representatives
- Out-of-office managers cannot delegate approval authority → Backlog of pending orders
- Ordering workflow is bottlenecked by Sales Rep availability

## Resolution Options

### Option 1: Custom Ordering Context + Proxy Console LWC (RECOMMENDED)

**Approach:**
1. Create `OrderingContext__c` object to track proxy sessions
2. Build `c-proxy-ordering-console` LWC:
   - Sales Rep selector (dropdown filtering by Procurement-assigned reps)
   - Optional date range for temporary proxy
   - Confirmation dialog showing VW and budget
   - Sets OrderingContext record and redirects to cart
3. Extend Order object with:
   - Original_Ordering_User__c (lookup to User)
   - Acting_As_User__c (formula from OrderingContext)
4. Create Permission Set "Proxy Ordering" for Procurement users
5. Integrate with Approval Process:
   - Approval routing based on Acting_As_User, not Performing_User
6. Create `ApprovalDelegation__c` object for out-of-office delegation:
   - Procurement/Buyer Manager can create delegation records
   - Approval process uses formula to select current approver
7. Order detail shows original orderer and acting-as context

**Effort:** M (Medium) — 2-3 weeks
- Week 1: OrderingContext object, Proxy Console LWC, permission sets
- Week 2: Order integration, Approval Process configuration
- Week 3: ApprovalDelegation workflow, testing

**Advantages:**
- Clear audit trail: Tracks who placed order and on whose behalf
- Flexible: Supports temporary proxy (date ranges) or permanent
- Extensible: Can support multi-level delegation (manager → assistant)
- Aligns with Salesforce permission model

**Risks/Dependencies:**
- Permission set governance: Must ensure only authorized users (Procurement) can create OrderingContext
- Approval Process complexity: Formula-based routing can be difficult to maintain
- Data integrity: Requires careful constraint checks (cannot proxy to unrelated users)

**Trade-offs:**
- Requires Procurement team training on proxy console
- Approval process logic is custom and may be fragile
- Ongoing maintenance of delegation workflows

---

### Option 2: Delegated Administrator Role

**Approach:**
- Use Salesforce's Buyer Manager role (from Batch 3 analysis)
- Grant Buyer Manager role to Procurement team
- Buyer Manager can "Place Order for Buyer" using standard Salesforce Buyer Manager API
- No custom objects required; leverage standard Salesforce delegation

**Effort:** S (Small) — 1-2 weeks
- Week 1: Configure Buyer Manager permission sets, test Place Order for Buyer API
- Week 2: User training

**Advantages:**
- No custom development
- Leverages standard Salesforce functionality
- Lower maintenance burden

**Risks/Dependencies:**
- "Place Order for Buyer" API may not exist or may have limited scope
- Standard Buyer Manager role may not align exactly with BBC's Procurement role
- Approval routing may not work correctly in delegated context

**Trade-offs:**
- Limited customization
- May not support all BBC use cases (e.g., temporary delegation)
- Relies on standard Salesforce capabilities that may not be flexible enough

---

### Option 3: Post-Order User Assignment (Simplified)

**Approach:**
- Procurement places order normally (self-service)
- Post-order, create custom Flow that reassigns order to Sales Rep
- Order.OwnerId or custom Owner_User__c field changed to Sales Rep
- Budget and inventory are consumed from Procurement's allocation; manually reconcile later

**Effort:** S (Small) — 1-2 weeks

**Advantages:**
- Minimal custom development
- Fast to implement

**Risks/Dependencies:**
- **Breaks budget model:** Order consumes Procurement's budget, not Sales Rep's → Budget tracking is incorrect
- **Inventory mismatch:** Inventory is consumed from Procurement's VW, not Sales Rep's
- **Operational confusion:** Order appears in both users' histories; unclear who really owns it
- **Not true proxy:** This is a workaround, not a real solution

**Trade-offs:**
- Fundamentally breaks BBC's operational model (budget and inventory context)
- Not recommended; only viable if Procurement and Sales Rep VWs are consolidated

---

## Recommended Approach

**Option 1 (Custom Ordering Context + Proxy Console)** is recommended because:

1. **Preserves Budget/Inventory Context:** Ordering consumes from the Sales Rep's budget/VW, maintaining budget accuracy.
2. **Audit Trail:** Clear tracking of who placed order and on whose behalf.
3. **Supports Temporary Delegation:** ApprovalDelegation object enables out-of-office scenarios (Critical Req #9).
4. **Operational Alignment:** Matches BBC's current procurement workflow.

**Option 2** is only viable if Salesforce's Buyer Manager API supports Place Order for Buyer with full budget/inventory context. Needs validation.

## Effort Estimate

**Option 1:** Medium (M)
- Effort: 2-3 weeks (80-120 hours)
- Confidence: High (standard Salesforce patterns; risks are well-known)
- Unknowns: Approval Process formula complexity; Procurement role scope; number of proxy relationships

**Option 2:** Small (S)
- Effort: 1-2 weeks (40-80 hours)
- Confidence: Low (depends on Buyer Manager API capabilities)
- Unknowns: API existence and scope; approval routing behavior

## Dependencies

### Must Happen Before
- [[gap|virtual-warehouse-inventory-model]] — Proxy ordering depends on VW model; must know whose VW is being ordered from
- [[gap|budget-management-engine]] — Budget must support proxy context; order must consume from Acting_As_User's budget

### Must Happen Alongside
- [[feature|approval-process-configuration]] — Approval routing logic must integrate with proxy context

### Blocks
- [[feature|order-management]] — Procurement cannot manage orders without proxy ordering

## Evidence

### Meeting 3: Custom Requests (Mar 9, 2026)
**Gap W2-G3: Proxy / Delegate Ordering**
- Severity: High
- Description: "Salesforce B2B Commerce does not natively support 'order on behalf of' for internal users within the same org. BBC's Procurement team regularly orders for Sales Reps using their Virtual Warehouse and budget allocation."
- Impact: "Without proxy ordering, Procurement cannot perform their core function. This is a go-live blocker for the Procurement team."

### Meeting 4: Fulfillment Demo (Mar 25, 2026)
**Critical Requirement #9:**
- "Out of Office Proxy — admin access to change approver. This requires the ability for a Buyer Manager to reassign approval authority during absence."

## Open Questions

1. **Proxy Authorization:** Which users are authorized to place proxy orders? All Procurement staff or only specific managers?
   - *Impact if answered wrong:* Permission set design changes
   - *Owner:* BBC Procurement/IT

2. **Proxy Scope:** Can any Procurement user proxy for any Sales Rep, or are there specific mappings (regional managers proxy for their reps)?
   - *Impact if answered wrong:* OrderingContext constraint logic changes
   - *Owner:* BBC Procurement

3. **Temporary vs. Permanent:** Is proxy authorization temporary (date ranges) or permanent delegations?
   - *Impact if answered wrong:* ApprovalDelegation object design changes
   - *Owner:* BBC Procurement

4. **Out-of-Office Delegation:** How is out-of-office delegation currently managed? Is there a formal process or ad-hoc?
   - *Impact if answered wrong:* ApprovalDelegation workflow design changes
   - *Owner:* BBC Procurement/HR

## Related Gaps

- [[gap|virtual-warehouse-inventory-model]] — Proxy ordering requires knowing whose VW is involved
- [[gap|budget-management-engine]] — Proxy ordering must consume from Acting_As_User's budget

## Status & Next Steps

**Status:** Open (design phase)

**Next Steps:**
1. Confirm proxy authorization model with BBC Procurement
2. Define proxy scope (any rep or specific mappings)
3. Finalize OrderingContext__c and ApprovalDelegation__c schema
4. Begin Proxy Console LWC development
5. Validate Approval Process formula logic
6. Test temporary delegation workflow
