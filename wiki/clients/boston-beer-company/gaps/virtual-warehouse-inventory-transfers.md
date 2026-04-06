---
type: gap
client: boston-beer-company
status: open
severity: high
category: inventory-management
related-feature: "[Virtual Warehouse Management]([[feature|vw-management]])"
resolution-approach: custom-dev
created: 2026-04-06
updated: 2026-04-06
sources:
  - "[[meeting|02-virtual-warehouse-walkthrough]] Workflow 2: Virtual Warehouse Transfers"
tags: inventory-transfer, virtual-warehouse, packout-unit, admin-workflow
---

# Gap: Virtual Warehouse Inventory Transfers

## Description

MerchTank allows administrators to transfer inventory (in packout units) between Virtual Warehouses. This is an admin-only function used by Procurement to rebalance inventory across users based on demand, regional needs, or user assignments.

Salesforce B2B Commerce has no concept of transferring inventory between allocations or user-specific inventory buckets. This gap depends on the [[gap|virtual-warehouse-inventory-model]] being implemented; once VWs exist as custom objects, a transfer workflow is needed.

## Current State

**MerchTank VW Transfer Workflow:**
- Transfer is admin-only function (URL path: /Core/Admin/)
- Both source and destination VWs must be selected before transfer is enabled
- Quantities are in packout units, not individual items
- Transfer quantities must be valid (> 0, <= Available Packouts)
- Inline validation on quantity fields
- Server-side validation prevents overselling

**Business Pattern:**
- Procurement redistributes stock based on seasonal demand
- Regional managers reallocate inventory between branch VWs
- User reassignments trigger inventory moves

## Target State

**Salesforce VW Transfer Architecture:**
- Custom Object `VW_Transfer__c`:
  - Fields: Source_VW__c (lookup), Destination_VW__c (lookup), Status__c (picklist: Draft/In_Progress/Completed/Cancelled), Transferred_By__c (lookup to User), Transfer_Date__c, Notes__c

- Custom Object `VW_Transfer_Line__c` (master-detail to VW_Transfer):
  - Fields: Product2__c (lookup), Transfer_Qty__c (number, in packout units), Qty_Per_Packout__c (number), Status__c

- Custom LWC `c-vw-transfer-form`:
  - Single-page state machine managing the full workflow in one component
  - State 1 (Empty): Form load, no selection
  - State 2 (Source Selected): Show source VW inventory
  - State 3 (Destination Selected): Show destination and enable item/qty selection
  - State 4 (Items Selected): Show review with source/dest/items/qtys
  - State 5 (Execute/Cancel): Final confirmation before transfer
  - Inline validation: Qty <= Available in source

- Apex Service `VWTransferService`:
  - Atomic transfer: All-or-nothing (uses savepoints for rollback)
  - Pessimistic locking: FOR UPDATE SOQL on source VW inventory
  - Creates audit record `VW_Transfer_Audit__c` with before/after quantities
  - Updates `VW_Inventory_Instance__c` quantities for both source and destination

- Permission Set: "VW Transfer Admin" for role-based access control

**Integration with Order Management:**
- VW_Inventory_Instance tracks available quantity (decrements on order, increments on transfer)
- Transfer is atomic: Succeeds completely or fails (no partial transfers)

## Gap Analysis

### What Salesforce Lacks

Salesforce B2B Commerce Inventory Management does not support:
- Inventory transfers between user allocations
- Packout-unit based transfers
- Atomic multi-item transfers with rollback
- Admin-only transfer workflows

### Root Cause

B2B Commerce assumes global inventory managed by fulfillment locations, not per-user allocations. VW transfers are specific to BBC's per-user inventory model.

### Impact

**Without Resolution:**
- Procurement cannot rebalance inventory across users
- Static allocations: Once a VW is assigned, inventory cannot move
- Demand mismatches: Popular items in one VW cannot be reallocated to high-demand users
- User reassignments are painful: No clean way to move inventory when user leaves/changes role
- Operational inflexibility

## Resolution Options

### Option 1: Custom Apex Service + LWC Transfer Form (RECOMMENDED)

**Approach:**
1. Create `VW_Transfer__c` and `VW_Transfer_Line__c` objects
2. Build `c-vw-transfer-form` LWC with state machine (5 states as above)
3. Build Apex Service `VWTransferService`:
   - `public TransferResult executeTransfer(VW_Transfer__c transfer)` method
   - Uses `Database.Savepoint` for atomic operations
   - Uses `SELECT...FOR UPDATE` for pessimistic locking (prevent concurrent transfers from same source)
   - Validates quantities, updates inventory, creates audit trail
4. Create `VW_Transfer_Audit__c` for compliance:
   - Logs before/after quantities, transfer date, user
5. Permission Set: "VW Transfer Admin"
6. Build transfer history Lightning page for admin review

**Effort:** L (Large) — 3-4 weeks
- Week 1: Object design, Apex service with locking
- Week 2: LWC state machine form
- Week 3: Audit trail, permission sets, testing
- Week 4: Performance testing under concurrent load

**Advantages:**
- Full control over transfer logic
- Atomic operations prevent overselling
- Clear audit trail
- Extensible for future enhancements (approval workflows, SLA tracking)

**Risks/Dependencies:**
- Concurrent transfer handling: Pessimistic locking may cause timeouts under high load
- Savepoint governance: Limited to 5 savepoints per transaction; may need refactoring if complex logic
- Performance: FOR UPDATE locking can impact response times
- Training: Procurement team must learn new transfer interface

**Trade-offs:**
- Complex Apex logic; requires thorough testing
- Ongoing maintenance burden
- Performance testing essential

---

### Option 2: Simplified: Manual Inventory Adjustment

**Approach:**
- Procurement manually adjusts inventory quantities in source and destination VWs via admin console
- No formal transfer object or workflow
- Uses standard Salesforce record edit

**Effort:** S (Small) — negligible

**Advantages:**
- No custom development
- Uses standard Salesforce edit interface

**Risks/Dependencies:**
- **Data integrity risk:** Manual adjustments may not be atomic; could result in inventory loss
- **No audit trail:** Difficult to track who changed inventory and why
- **Operational risk:** No validation prevents overselling or mistakes
- **Not scalable:** Manual process doesn't scale for frequent/large transfers

**Trade-offs:**
- Fundamentally risky; not recommended without mitigation (approval workflows, field-level audit)

---

### Option 3: Flow-Based Transfer (No Apex)

**Approach:**
- Build transfer form in LWC (no state machine; simpler form)
- Use Salesforce Flow (no Apex) to execute transfer:
  - Query source/destination VW inventory
  - Update source quantities (decrement)
  - Update destination quantities (increment)
  - Create audit record
- No Apex Service; Flow handles all logic

**Effort:** M (Medium) — 2-3 weeks
- Week 1: LWC transfer form (simpler, no state machine)
- Week 2-3: Flow-based transfer logic, testing

**Advantages:**
- Reduced code complexity (no Apex)
- Easier for non-developers to maintain
- Still provides audit trail

**Risks/Dependencies:**
- Flow governor limits: Complex multi-record-update flows may hit limits
- Atomic operations: Flows don't support savepoints; harder to guarantee all-or-nothing
- Concurrent transfers: No pessimistic locking; risk of overselling if transfers overlap
- Performance: Flows are slower than Apex for complex logic

**Trade-offs:**
- Less control than Apex
- May not handle high concurrency well
- Performance may be poor for large transfers

---

## Recommended Approach

**Option 1 (Apex Service + LWC Form)** is recommended because:

1. **Safety:** Atomic operations with pessimistic locking prevent overselling and data loss
2. **Scalability:** Apex is more performant than Flow for complex operations
3. **Control:** Full control over transfer logic and error handling
4. **Audit Trail:** Clear record of every transfer with before/after state

**Option 3** is a fallback if BBC has low transfer frequency (< 10/day) and can accept occasional data integrity issues.

## Effort Estimate

**Option 1:** Large (L)
- Effort: 3-4 weeks (120-160 hours)
- Confidence: Medium (concurrent transfer handling is tricky; pessimistic locking requires careful testing)
- Unknowns: Transfer frequency and concurrency patterns; packout validation rules

**Option 3:** Medium (M)
- Effort: 2-3 weeks (80-120 hours)
- Confidence: Medium (Flow limitations may require Apex workarounds)
- Unknowns: Flow governor limits in production environment

## Dependencies

### Must Happen Before
- [[gap|virtual-warehouse-inventory-model]] — VW objects must exist before transfers can be built

### Must Happen Alongside
- [[feature|vw-management-console]] — Admin tools for managing VWs and transfers

### Blocks
- [[feature|vw-rebalancing-operations]] — Procurement cannot execute rebalancing without transfers

## Evidence

### Meeting 2: Virtual Warehouse Walkthrough (Feb 2, 2026)
**Workflow 2: Virtual Warehouse Transfers**
- Current State: "Transfer quantities must be valid (> 0, <= Packouts Available)"
- "Transfer is an admin-only function"
- "Both source and destination must be selected before transfer is enabled"
- Gap Severity: High
- Recommendation: "Custom Apex service + LWC. The transfer form is a single-page state machine (5 MerchTank screens map to 1 LWC with internal states). Effort: L (3-4 weeks)."

## Open Questions

1. **Transfer Frequency:** How often does Procurement execute transfers? Daily, weekly, monthly, or ad-hoc?
   - *Impact if answered wrong:* Frequency affects concurrency strategy and performance testing scope
   - *Owner:* BBC Procurement

2. **Transfer Size:** Typical number of items/lines per transfer? (10s, 100s?)
   - *Impact if answered wrong:* Savepoint and Flow governor limits may be exceeded
   - *Owner:* BBC Procurement

3. **Approval Required:** Do transfers require approval before execution, or are they Procurement's solo decision?
   - *Impact if answered wrong:* Approval workflow must be added if required
   - *Owner:* BBC Procurement

## Related Gaps

- [[gap|virtual-warehouse-inventory-model]] — Transfers depend on VW model

## Status & Next Steps

**Status:** Open (design phase, dependent on VW model)

**Next Steps:**
1. Confirm transfer frequency and typical size with BBC Procurement
2. Confirm no approval workflow is needed
3. Finalize VW_Transfer__c schema (wait for VW model completion)
4. Begin Apex Service development (pessimistic locking strategy)
5. Design LWC state machine transfer form
6. Plan concurrent transfer testing strategy
