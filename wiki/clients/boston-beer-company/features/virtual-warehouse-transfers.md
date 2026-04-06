---
type: feature
client: boston-beer-company
status: draft
category: inventory
decision: custom
effort: L
priority: P2
created: 2026-04-06
updated: 2026-04-06
sources:
  - /sessions/sweet-trusting-ride/mnt/Vendale-Agentics/BostonBeerCompany/meetings/02-virtual-warehouse-walkthrough/analysis/gap-analysis-bbc-vw-walkthrough.md
tags:
  - inventory-management
  - virtual-warehouse
---

# Virtual Warehouse Transfers

## Description

Procurement staff can transfer inventory between Virtual Warehouses via an admin-level transfer workflow. This allows BBC to redistribute stock based on demand and availability. The workflow displays source and destination VWs, shows available inventory per item, allows selection of items to transfer, and executes the transfer atomically (all-or-nothing).

## Current Implementation

**User Workflow:**
1. Navigate to `/Core/Admin/VirtualWarehouseTransfer`
2. Select source VW from dropdown (populates item table with available inventory)
3. Select destination VW from dropdown (supports type-ahead filtering)
4. Review items table: SKU, Title, Qty per Packout, Packouts Available to Transfer
5. Check items to transfer via per-row checkboxes
6. Enter transfer quantities via numeric spinner (packout units)
7. Click Transfer to execute (or Cancel)

**Business Rules:**
- Transfer quantities must be valid (> 0, <= Packouts Available)
- Quantities are in packout units, not individual items
- Transfer is admin-only function
- Both source and destination must be selected before transfer is enabled
- Inline validation on quantity fields
- Atomic operation: all-or-nothing, with savepoint for rollback

## Target Implementation

1. **Custom Objects:**
   - `VW_Transfer__c`: Master transfer record
   - `VW_Transfer_Line__c`: Individual item transfers (master-detail to VW_Transfer__c)

2. **Transfer Form LWC: `c-vw-transfer-form`**
   - Single-page state machine managing full workflow
   - States: Empty → Source Selected → Source Items Loaded → Destination Selected → Item Selection → Qty Entry → Execute/Cancel
   - Source VW dropdown with search
   - Item selection checkboxes
   - Quantity spinners (in packout units)
   - Transfer button

3. **Apex Service: `VWTransferService`**
   - Atomic transfer with savepoint
   - Optimistic locking to prevent concurrent transfers
   - Audit trail creation
   - Validation of quantities

## Gaps & Risks

**Gap VWT-G1: No Inventory Transfer Mechanism**
- Severity: High
- Description: B2B Commerce has no concept of transferring inventory between allocations
- Impact: Without transfers, VW inventory becomes static
- Resolution: Custom Apex service + LWC (see above)
- Effort: L (3-4 weeks)

**Gap VWT-G2: Concurrent Transfer Locking**
- Severity: Medium
- Description: Two admins could transfer from same source VW simultaneously, causing overallocation
- Impact: Inventory could become negative
- Resolution: Pessimistic locking via `FOR UPDATE` SOQL
- Effort: Bundled with VWT-G1

**Gap VWT-G3: Transfer Approval Workflow**
- Severity: Low
- Description: Should large transfers require approval?
- Impact: Quality control on inventory movements
- Resolution: Optional Flow-based approval for transfers over threshold
- Effort: M (if required)

## Dependencies

- [[virtual-warehouse-model|Virtual Warehouse Model]] (VW and inventory data)

## Open Questions

1. Are there size/amount thresholds that trigger approval for transfers?
2. Should the transfer audit trail be visible to non-admins?
3. Are there restrictions on which VWs can transfer to which?
4. How frequently are transfers used? Is this a Phase 1 priority?

## Evidence

**Meeting 2 (VW Walkthrough):**
- "Admin-level function at `/Core/Admin/VirtualWarehouseTransfer` for moving inventory between VWs"
- "Multi-step workflow within a single page"
- "Transfer is an admin-only function"
- "Both source and destination must be selected before transfer is enabled"
- "Inline validation on quantity fields"
