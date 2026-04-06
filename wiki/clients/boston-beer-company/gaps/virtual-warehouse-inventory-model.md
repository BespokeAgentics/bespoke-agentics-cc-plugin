---
type: gap
client: boston-beer-company
status: open
severity: critical
category: core-architecture
related-feature: "[Order Management]([[feature|order-management]])"
resolution-approach: custom-dev
created: 2026-04-06
updated: 2026-04-06
sources:
  - "[[meeting|02-virtual-warehouse-walkthrough]] Workflow 1: Virtual Warehouse Management"
  - "[[meeting|04-fulfillment-demo]] Inventory Model"
tags: inventory, virtual-warehouse, packout-unit, user-allocation, architectural-foundation
---

# Gap: Virtual Warehouse Inventory Model

## Description

MerchTank's architecture is built on the concept of Virtual Warehouses (VWs): per-user allocated inventory buckets where each VW is assigned to a single user and contains a set of items with specific quantities (measured in packout units). There are 95 VWs in the current system, each with a 1:1 constraint to a Unit (a concept representing a physical location or entity).

Salesforce B2B Commerce tracks inventory globally (by location or fulfillment center) or by standard inventory management patterns. It has no concept of per-user allocated inventory with individual item allocations. This VW model is the **architectural foundation** of MerchTank and underpins ordering, budgeting, proxy ordering, and fulfillment workflows.

Without a custom VW implementation, the entire ordering paradigm cannot function.

## Current State

**MerchTank Virtual Warehouse Model:**
- 95 Virtual Warehouses exist in production
- Each VW is assigned to exactly one user (1:1 constraint, server-side enforced)
- Some users have multiple VWs (e.g., Cyrus Sampsel manages Lots #1003 and #1082)
- VWs can be unassigned or reassigned
- Each VW contains item-level inventory with quantities tracked in packout units (e.g., "5 packouts of Tap Handle Blue")
- VWs are enumerated as "Lots" in the UI (e.g., "Lot #1003")
- VW inventory is the sole source of available inventory for ordering; users cannot order outside their VW allocation
- VW Transfer workflow allows admins to move inventory between VWs (see [[gap|virtual-warehouse-inventory-transfers]])

**Supporting Concepts:**
- Unit: A physical entity (warehouse, regional center, or tracking code) linked 1:1 to a VW
- Packout: A selling unit (e.g., "1 packout = 144 tap handles")
- Lot Number: A unique identifier for a VW (e.g., "Lot #1003")

## Target State

**Salesforce Custom VW Architecture:**
- Custom Object `Virtual_Warehouse__c`:
  - Fields: Lot_Number__c (unique), Owner__c (lookup to User/Contact), Unit_ID__c (unique, enforces 1:1 constraint), Active__c (checkbox), Description__c
  - Permissions: Admin-only visibility and edit

- Custom Object `VW_Inventory_Instance__c`:
  - Master-Detail to Virtual_Warehouse__c
  - Fields: Product2__c (lookup), Available_Quantity__c (number), Packout_Qty_Per_Unit__c (number), Status__c (picklist: Active/Inactive), Item_Type__c (picklist: Standard/Customizable), Sell_Price__c (currency)
  - Rollup summary for total items, total value per VW

- Custom LWC `c-vw-management-console`:
  - VW selector bar (dropdown or tile grid of assigned VWs)
  - Filter bar (search by product SKU, brand, or item type)
  - Inventory data table (Product | Available Qty | Packout Unit | Status | Actions)
  - Edit modal for inline quantity adjustments
  - Audit trail logging

- Apex Trigger on Virtual_Warehouse__c:
  - Before Insert/Update: Enforce 1:1 Unit-to-VW constraint
  - After Insert/Update/Delete: Create audit records

- Experience Cloud Page:
  - Admin-only role-based visibility
  - Dedicated VW Management console for Procurement team

**Integration with Ordering:**
- When a user places an order, items are reserved/decremented from their assigned VW(s)
- Proxy ordering must reference owner's VW (see [[gap|proxy-delegate-ordering]])
- Order detail shows which VW was the source of inventory

## Gap Analysis

### What Salesforce Lacks

Salesforce B2B Commerce and standard inventory management do not provide:
- Per-user inventory allocation buckets
- Item-level quantity tracking within an allocation
- Packout unit abstraction (quantities are typically atomic items)
- 1:1 User-to-Location constraint
- VW management console for admin reassignment and transfers

### Root Cause

B2B Commerce is designed for seller-to-buyer commerce (catalog → cart → checkout → fulfillment). Inventory is managed at the seller's level (global or by fulfillment location), not allocated per buyer. BBC's model is a B2B internal ordering platform where inventory is pre-allocated to users as "working stock" — a fundamentally different paradigm.

### Impact

**Without Resolution:**
- No inventory allocation model: Users would see all inventory; procurement loses control over item distribution
- Proxy ordering cannot function: No reference point for "whose inventory is being ordered"
- Budget validation becomes meaningless: Budget is tied to VW; without VW, budget context is lost
- No inventory transfer workflow: Admins cannot rebalance stock between users
- Fulfillment routing is ambiguous: No clear source of inventory for each order

## Resolution Options

### Option 1: Full Custom Virtual Warehouse Build (RECOMMENDED)

**Approach:**
1. Create `Virtual_Warehouse__c` and `VW_Inventory_Instance__c` objects as designed above
2. Build Apex trigger enforcing 1:1 Unit-to-VW constraint
3. Build custom LWC VW Management console for Procurement
4. Integrate with Order object: Add VW__c (lookup) field to OrderSummary to track source VW
5. Build VW Transfer workflow (see [[gap|virtual-warehouse-inventory-transfers]])
6. Create audit trail object for VW changes: `VW_Audit_Log__c`

**Effort:** XL (Extra Large) — 5-6 weeks
- Week 1: Object design, schema finalization, Apex trigger
- Week 2-3: VW Management console LWC
- Week 4: Order integration and VW field population
- Week 5: Transfer workflow integration
- Week 6: Testing, audit trail, documentation

**Advantages:**
- Feature parity with current system
- Full control over VW rules and lifecycle
- Extensible for future VW features (bulk transfers, auto-rebalancing, etc.)
- Clear audit trail for compliance

**Risks/Dependencies:**
- Data migration: 95 VWs + inventory must be migrated from MerchTank
- Ordering logic depends on VW model: Must integrate simultaneously with order creation
- User adoption: Procurement team must learn new VW console UI
- Concurrent VW inventory decrements: Risk of overselling if not carefully implemented with locking

**Trade-offs:**
- Largest effort in the entire migration
- Ongoing maintenance of custom code
- VW management console adds UI/UX burden to training

---

### Option 2: Simplified Account-Based Inventory Allocation

**Approach:**
- Eliminate per-user VW concept; instead use Buyer Accounts as the inventory allocation unit
- Each Buyer Account (wholesaler) gets a global inventory allocation
- No per-item tracking; instead, use standard Salesforce inventory with account-level entitlements
- Users within the account can order any available inventory (no user-specific allocation)

**Effort:** M (Medium) — 2-3 weeks
- Week 1: Design account-based entitlement model
- Week 2-3: Build entitlement policies and order validation

**Advantages:**
- Simpler than full VW build
- Leverages standard Salesforce inventory patterns
- Reduces data migration complexity
- Easier to maintain

**Risks/Dependencies:**
- **Significant business model change:** Eliminates user-level inventory control. Sales Reps might over-order or underutilize stock.
- **Breaks proxy ordering logic:** Procurement can no longer "order on behalf of Sales Rep using their VW"; instead, ordering is at the account level.
- **Budget integration complex:** Budget is tied to brand/user in current system; account-level budget may not align.
- **Rejection risk:** BBC procurement team may reject this simplification as a loss of control.

**Trade-offs:**
- Fundamentally different operational model
- Requires significant change management
- May not meet BBC's business requirements

---

### Option 3: Hybrid Model: VWs as Entitlements Only (No Qty Tracking)

**Approach:**
- Create `Virtual_Warehouse__c` as an identity/permission object (Owner, Lot Number, Active) but without detailed `VW_Inventory_Instance__c`
- Inventory quantities are managed in Salesforce standard inventory (Product2/InvItsem/AlternativeSkus)
- VW acts as a "buyer group" or "catalog entitlement" that controls which products a user can see/order
- On order, items decrement from the global inventory pool, not from user-specific VW buckets

**Effort:** M-L (3-4 weeks)
- Week 1: VW object design (identity-only)
- Week 2: Entitlement policy integration
- Week 3: Order integration and global inventory decrement logic
- Week 4: Testing and data migration

**Advantages:**
- Simpler than full VW build (no item-level VW tracking)
- Maintains VW identity and proxy ordering context
- Uses Salesforce standard inventory patterns
- Reduces data migration effort

**Risks/Dependencies:**
- **Inventory visibility changed:** Procurement loses per-user inventory allocation view. No more "VW #1003 has 50 tap handles"; instead, "Global inventory has 50 tap handles."
- **Inventory rebalancing becomes hard:** If Procurement needs to move inventory between users, it must be done via manual global adjustments or a transfer workflow at the Entitlement level.
- **May not align with inventory planning:** If Procurement uses VW quantities for planning, this model breaks that workflow.

**Trade-offs:**
- Middle ground between full VW build and complete simplification
- Preserves VW context for ordering but loses granular inventory tracking
- May not meet BBC's operational requirements if they rely on VW-level inventory visibility

---

## Recommended Approach

**Option 1 (Full Custom Virtual Warehouse Build)** is recommended because:

1. **Business Requirement:** VW is the architectural foundation of MerchTank. BBC's procurement team explicitly manages 95 VWs with item-level inventory. Simplifying would fundamentally break their operational model.
2. **Scope Certainty:** VW requirements are clearly defined from current system; less design uncertainty.
3. **Feature Parity:** Supports proxy ordering, budget enforcement, and all downstream workflows.
4. **Future-Proofing:** VW model supports advanced features like inventory auto-rebalancing, regional allocation, etc.

**Option 3** is a fallback if BBC accepts VW as an identity/entitlement model (not an inventory model). This could accelerate Phase 1 and defer detailed inventory tracking to Phase 2.

## Effort Estimate

**Option 1:** Extra Large (XL)
- Effort: 5-6 weeks (200-240 hours)
- Confidence: Medium-High (VW concept is clear; integration with ordering/budgeting/proxy is complex but well-defined)
- Unknowns: Detailed VW business rules (special cases, archive strategy, etc.); data migration volume and cleanliness

**Option 2:** Medium (M)
- Effort: 2-3 weeks (80-120 hours)
- Confidence: Low (requires business acceptance of operational model change)
- Unknowns: How BBC will adapt to account-level inventory; impact on procurement workflows

**Option 3:** Medium-Large (M-L)
- Effort: 3-4 weeks (120-160 hours)
- Confidence: High (leverages Salesforce standard patterns)
- Unknowns: BBC acceptance of VW as entitlement-only; inventory visibility requirements

## Dependencies

### Must Happen Before
- [[decision|Core-Architecture-Paradigm]] — VW model choice must be decided before any ordering logic is built
- [[decision|Inventory-Data-Migration]] — 95 VWs + item-level inventory must be migrated; schema must finalize before migration planning

### Must Happen Alongside
- [[feature|order-creation-and-vw-decrement]] — Order placement must integrate with VW inventory decrement
- [[feature|proxy-delegate-ordering]] — Proxy ordering depends on VW ownership model
- [[gap|budget-management-engine]] — Budget per VW/user requires VW model in place

### Blocks
- [[feature|order-management]] — Ordering cannot function without VW model
- [[gap|virtual-warehouse-inventory-transfers]] — Transfer workflow depends on VW objects
- [[feature|catalog-browsing]] — VW-based catalog entitlements depend on VW model

## Evidence

### Meeting 2: Virtual Warehouse Walkthrough (Feb 2, 2026)
**Workflow 1: Virtual Warehouse Management**
- Current State: "One VW per Unit (1:1 constraint, server-side enforced)"
- "VW inventory includes per-item quantity tracked in packout units"
- "95 Virtual Warehouses exist"
- Gap Severity: Critical
- "The VW model is the architectural foundation of MerchTank. Without it, ordering, budgeting, and proxy workflows cannot function."

**Assessment Breakdown:**
- Gap identified as requiring significant custom development
- VW Management Readiness: "Significant Effort"

### Meeting 4: Fulfillment Demo (Mar 25, 2026)
**Feature Inventory: Inventory Model**
- VW concept mentioned in context of fulfillment vendor assignment
- VW inventory must be tracked for availability during checkout

## Validation Notes

SFCC Validation Report (VW Walkthrough, Meeting 2) confirms:
- "Salesforce B2B Commerce does not have a per-user inventory allocation concept"
- "Custom object approach is viable and recommended"
- "Packout unit abstraction will require custom field and validation logic"

## Open Questions

1. **VW Archive/Deactivation:** What is the lifecycle of a VW when a user leaves or is reassigned? Can VWs be archived or must inventory be transferred?
   - *Impact if answered wrong:* Object lifecycle design and audit trail requirements change
   - *Owner:* BBC Procurement/IT

2. **VW Inventory Reallocation:** How often does Procurement rebalance inventory between VWs? Is there a formal process or ad-hoc?
   - *Impact if answered wrong:* Transfer workflow frequency and approval rules change
   - *Owner:* BBC Procurement

3. **Multi-VW Ordering:** Can a user order from multiple VWs in a single order? Or does each order reference a single source VW?
   - *Impact if answered wrong:* OrderSummary.VW__c field design and order consolidation logic changes
   - *Owner:* BBC Procurement/Sales

4. **Packout Unit Variation:** Are packout quantities standard across all items, or do they vary by product category?
   - *Impact if answered wrong:* VW_Inventory_Instance__c field design and order quantity validation changes
   - *Owner:* BBC Procurement/Finance

## Related Gaps

- [[gap|virtual-warehouse-inventory-transfers]] — Transfer workflow depends on VW model
- [[gap|proxy-delegate-ordering]] — Proxy ordering requires VW ownership context
- [[gap|budget-management-engine]] — Budget per VW/user requires VW model
- [[gap|program-window-time-gating]] — Program availability may be VW-specific

## Status & Next Steps

**Status:** Open (design phase)

**Next Steps:**
1. Confirm VW as architectural requirement (vs. considering Option 2/3)
2. Schedule VW business rules workshop with BBC Procurement
3. Finalize Virtual_Warehouse__c and VW_Inventory_Instance__c schema
4. Plan data migration approach for 95 VWs + inventory
5. Begin Apex trigger development
6. Start VW Management console LWC design in parallel with order integration
