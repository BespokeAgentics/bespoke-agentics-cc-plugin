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
  - "[[meeting|01-merchtank-overview]] Gap W5-G1"
  - "[[meeting|02-virtual-warehouse-walkthrough]] Procurement Workflow"
tags: order-release, procurement-workflow, order-lifecycle, batch-processing
---

# Gap: Procurement-Controlled Order Release

## Description

MerchTank implements a procurement workflow where program pre-orders sit in a "pending" state until the procurement team explicitly releases them. This release typically happens after all items have been received from vendors and the inventory is confirmed to be available.

Salesforce B2B Commerce processes orders immediately upon checkout and moves them through standard order lifecycle states (Entered → Approved → Fulfilled → Shipped). There is no concept of a "pending release" state controlled by procurement.

This workflow is critical to BBC's operational model where orders are pre-sold before inventory is physically received.

## Current State

**MerchTank Order Release Workflow:**
- Users place pre-orders during a program window
- Orders enter "Pending" state
- Procurement team reviews pending orders (batch or daily)
- Once vendors deliver inventory, Procurement confirms items are received
- Procurement explicitly releases orders (batch operation for all orders for a program)
- Released orders move to "Open" state and are sent to fulfillment vendors
- Users see "Pending Release" status in order history

**Operational Pattern:**
- Pre-orders are common for seasonal campaigns (e.g., Suncruiser Summer 2026)
- Procurement releases all orders for a program at once (not individually)
- Release is data-driven: Procurement sees pending order queue and bulk-releases

## Target State

**Salesforce Order Release Workflow:**
- Custom Object `OrderReleaseBatch__c`:
  - Fields: Program__c (lookup), Status__c (picklist: Created/In_Review/Released), Release_Date__c, Released_By__c (lookup to User), Notes__c

- Custom Object `OrderReleaseMap__c` (junction between Order and Batch):
  - OrderSummary__c (lookup), OrderReleaseBatch__c (lookup)
  - Allows tracking which orders are in which release batch

- Order Lifecycle Extensions:
  - Custom Status on Order: "Pending Release" (added to standard lifecycle)
  - Orders created during program window initially have Status = "Pending Release"
  - Procurement can bulk-update Status → "Open" (via batch action in custom console)

- Procurement Queue / Release Console LWC:
  - List of pending order batches grouped by program
  - Bulk action: "Release Batch" (releases all orders in batch)
  - Confirmation dialog showing order count and items being released
  - Audit trail: logs who released batch and when

- Bulk Release Flow:
  - Triggered by "Release Batch" action
  - Updates all OrderSummary.Status__c = "Open" in batch
  - Creates Platform Event `OrdersReleasedEvent` for fulfillment vendor integration
  - Sends notification to fulfillment vendors about released orders

## Gap Analysis

### What Salesforce Lacks

Salesforce B2B Commerce Order Management does not provide:
- Pending/held order states in the standard lifecycle
- Batch release workflow
- Procurement queue or dashboard for pending orders
- Bulk order action capability (update status for multiple orders)

### Root Cause

B2B Commerce assumes immediate order fulfillment after checkout. The pending/release model is a specialized procurement pattern unique to BBC's pre-order business model.

### Impact

**Without Resolution:**
- Orders are immediately open upon checkout → Cannot hold for inventory confirmation
- Procurement loses visibility into pending order queue
- No mechanism to bulk-release orders → Manual per-order confirmation required
- Fulfillment vendors may receive incomplete orders → Inventory mismatch
- Users see "Open" status immediately → Misrepresents readiness for fulfillment

## Resolution Options

### Option 1: Custom Order Status + Release Batch Workflow (RECOMMENDED)

**Approach:**
1. Create custom object `OrderReleaseBatch__c` and `OrderReleaseMap__c` as designed above
2. Extend Order object with custom field: `Release_Status__c` (picklist: Pending_Release/Released)
3. Add Order to Release Batch via OrderReleaseMap on order creation (automatic Flow)
4. Build Procurement Release Console LWC:
   - Pending orders grouped by program/batch
   - Bulk select/filter options
   - "Release Batch" bulk action button
5. Create Scheduled Flow or batch Apex to auto-populate OrderReleaseBatch:
   - Groups pending orders by program
   - Creates batches for easier management
6. Build Release Batch Flow:
   - On "Release Batch" action, update all orders in batch: Release_Status__c = "Released"
   - Create OrdersReleasedEvent for vendor notification
   - Log audit trail
7. Order detail shows release status and batch

**Effort:** M (Medium) — 2-3 weeks
- Week 1: Object design, order status custom fields
- Week 2: Release Console LWC, bulk action Flow
- Week 3: Batch grouping logic, vendor notification, testing

**Advantages:**
- Clear audit trail: Every release is recorded with timestamp and user
- Batch management: Reduces operational overhead (release once, not per-order)
- Flexibility: Can release individual orders or batches
- Extensible: Can add approval workflows, SLA tracking

**Risks/Dependencies:**
- Order status governance: Release_Status must be kept in sync with order lifecycle
- Bulk update timing: Large batches may have performance implications
- Vendor notification: Must ensure fulfillment vendors receive released order notification promptly

**Trade-offs:**
- Requires Procurement team training on release console
- Ongoing maintenance of release batch logic
- Potential data duplication (Release_Status vs. standard Order Status)

---

### Option 2: Approval Process + Conditional Workflow

**Approach:**
- Use Salesforce Approval Process for order release
- Orders start in "Pending" status
- Approval process routes to Procurement team
- Approvers can batch-approve orders or approve individually
- Approval completion updates order status to "Open"

**Effort:** M (Medium) — 2-3 weeks

**Advantages:**
- Leverages standard Salesforce approval framework
- Audit trail from approval process
- No custom order status field needed

**Risks/Dependencies:**
- Approval process doesn't support efficient bulk approval
- Approvers would need to approve each order individually or use bulk approve (less control)
- Cannot group orders by program/batch in approval process

**Trade-offs:**
- Less flexible than custom batching
- May create approval bottleneck if many pending orders

---

### Option 3: Simplified: No Pending State (Manual Process)

**Approach:**
- Orders are immediately "Open" upon checkout
- Procurement manually confirms order readiness outside of Salesforce
- No pending/release workflow in system

**Effort:** S (Small) — negligible

**Advantages:**
- No custom development
- Simpler order lifecycle

**Risks/Dependencies:**
- **Breaks workflow:** Orders appear "Open" before inventory is confirmed
- **Loss of visibility:** No queue or dashboard for pending orders
- **Manual tracking:** Procurement must track pending orders outside Salesforce
- **Operational risk:** Orders may be sent to fulfillment before inventory is available

**Trade-offs:**
- Fundamentally changes BBC's operational model
- Not recommended without business acceptance of changed process

---

## Recommended Approach

**Option 1 (Custom Order Status + Release Batch Workflow)** is recommended because:

1. **Preserves Workflow:** Maintains BBC's pending/release operational model
2. **Audit Trail:** Records every release with timestamp and user
3. **Scalability:** Batch release reduces operational overhead for large order volumes
4. **Extensibility:** Can add approval workflows, SLA tracking, or automation later

## Effort Estimate

**Option 1:** Medium (M)
- Effort: 2-3 weeks (80-120 hours)
- Confidence: High (standard Salesforce patterns)
- Unknowns: Order volume at release time; batch size complexity; vendor notification latency requirements

**Option 2:** Medium (M)
- Effort: 2-3 weeks (80-120 hours)
- Confidence: Medium (approval process bulk operations less common)
- Unknowns: Approval process user experience with high volume orders

**Option 3:** Small (S)
- Effort: Negligible (business decision, not technical)

## Dependencies

### Must Happen Before
- [[decision|Order-Lifecycle-Design]] — Pending release status must be defined in order lifecycle

### Must Happen Alongside
- [[feature|vendor-notification]] — Vendor integration must handle "Order Released" event

### Blocks
- [[feature|order-management]] — Program pre-order workflow depends on pending/release states

## Evidence

### Meeting 1: MerchTank Overview (Dec 4, 2025)
**Gap W5-G1: Procurement-Controlled Order Release**
- Severity: High
- Description: "Program pre-orders sit as 'pending' until the procurement team explicitly releases them after all items are received from vendors. This is a procurement workflow, not a standard B2B Commerce pattern."
- Impact: "Procurement loses their primary order management workflow."
- Recommendation: "Custom order status flow with a 'Pending Release' stage and procurement queue. Procurement users get a custom list view/action to release batches. (~M effort)"

## Open Questions

1. **Release Frequency:** How often does Procurement release orders? Daily, weekly, by program, or on-demand?
   - *Impact if answered wrong:* Batch grouping and automation strategy changes
   - *Owner:* BBC Procurement

2. **Bulk Size:** What is typical batch size for a release? (10s, 100s, 1000s of orders)
   - *Impact if answered wrong:* Performance testing and bulk operation strategy changes
   - *Owner:* BBC Procurement

3. **Release Criteria:** What criteria determines when a batch is ready to release? (All items received, specific date, manual review)
   - *Impact if answered wrong:* Release automation logic changes
   - *Owner:* BBC Procurement

4. **Approval Required:** Does release require approval from management, or is it Procurement's solo decision?
   - *Impact if answered wrong:* Approval workflow is added if needed
   - *Owner:* BBC Procurement

## Related Gaps

- [[gap|program-window-time-gating]] — Program windows create pre-order periods
- [[gap|batch-order-upload]] — Bulk order processing may accompany release workflow

## Status & Next Steps

**Status:** Open (design phase)

**Next Steps:**
1. Confirm release frequency and batch size with BBC Procurement
2. Define release criteria (inventory confirmation, date-based, etc.)
3. Confirm no approval workflow is needed (or design if required)
4. Finalize OrderReleaseBatch__c and OrderReleaseMap__c schema
5. Begin Release Console LWC development
6. Design vendor notification event
