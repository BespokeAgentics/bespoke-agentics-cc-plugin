---
type: feature
client: boston-beer-company
status: draft
category: inventory
decision: custom
effort: XL
priority: P1
created: 2026-04-06
updated: 2026-04-06
sources:
  - /sessions/sweet-trusting-ride/mnt/Vendale-Agentics/BostonBeerCompany/meetings/02-virtual-warehouse-walkthrough/analysis/gap-analysis-bbc-vw-walkthrough.md
  - /sessions/sweet-trusting-ride/mnt/Vendale-Agentics/BostonBeerCompany/meetings/03-custom-requests/analysis/gap-analysis-bbc-custom-requests-meeting.md
tags:
  - inventory-management
  - account-structure
  - virtual-allocation
---

# Virtual Warehouse Model

## Description

A Virtual Warehouse (VW) is BBC's unique inventory allocation concept. Each VW represents a personal inventory allocation assigned to an individual user (typically a sales rep or distributor contact). MerchTank currently maintains 95 VWs, each with a 1:1 assignment to a Unit (a unique identifier). Each VW contains allocated quantities of specific merchandise items. This model allows BBC to manage per-user inventory visibility and controls while maintaining centralized warehousing. It is the foundational architectural concept in MerchTank and has no direct equivalent in Salesforce B2B Commerce.

## Current Implementation

**User Workflow (Admin):**
1. Navigate to `/Core/Management/VirtualWarehouse` (admin-only)
2. Select a VW from dropdown of 95 entries (sorted alphabetically by owner name)
3. Format: "VW ([Person Name]) Lot # [number]" (e.g., "VW (Cyrus Sampsel) Lot # 1003")
4. View VW instance table: ID, Thumbnail, SKU, Name, Status, Item Type, Available Quantity, Sell Price, Description
5. Search/filter instances by phrase, SKU, item type, status, inventory presence
6. Edit VW properties via modal: Name, Owner (searchable dropdown), Active toggle
7. Create new VWs via "+ Add Virtual Warehouse" action
8. Export instance data to Excel

**Business Rules:**
- One VW per Unit (1:1 constraint, server-side enforced)
- Owner is a required field
- VWs can be unassigned or assigned to specific users
- Some users have multiple VWs (e.g., Cyrus Sampsel has Lots #1003 and #1082)
- VW inventory tracked in packout units (not individual items)
- Each item in the VW has: SKU, Name, Status, Qty Packed (items per packout), Available Quantity (in packouts), Sell Price

**Current Technical Implementation:**
- Virtual Warehouse table in SQL Server database
- VW_Instance table tracking individual item allocations
- VW_Status codes (Active, Inactive, etc.)
- Dropdown UI with search capability
- Admin page at `/Core/Management/VirtualWarehouse`

**Systems Involved:**
- MerchTank backend, VW/Unit database tables, admin UI

## Target Implementation

Salesforce B2B Commerce has no native per-user inventory allocation model. This requires custom objects and a complete admin application to replicate VW functionality.

**Proposed Salesforce Architecture:**

1. **Custom Objects:**
   - `Virtual_Warehouse__c`: Master VW record
     - Fields: Lot_Number__c (unique, external ID), Unit__c (unique, 1:1 relationship), Owner__c (lookup to User or Contact), Active__c (checkbox), Name, Created_Date__c, Last_Modified__c
     - Relationships: One-to-one with Unit
   - `Unit__c` (if required): Represents the organizational unit or account entity
     - Fields: Unit_ID__c (unique), Unit_Name__c, Region__c, etc.
   - `VW_Inventory_Instance__c`: Individual item allocations within a VW
     - Fields: Virtual_Warehouse__c (master-detail), Product__c (lookup to Product2), Available_Quantity__c (in packouts), Status__c, Item_Type__c, Sell_Price__c, Description__c
   - `VW_Transfer__c`: Transfer records (for VW Transfers feature)
   - `VW_Transfer_Line__c`: Line items in a transfer

2. **Admin Application:**
   - Custom LWC: `c-vw-management-console`
     - Selector bar: Dropdown to choose VW from 95 entries (with search/type-ahead)
     - Filter bar: Search by phrase, SKU, item type, status, inventory presence
     - Instance data table: ID, Thumbnail, SKU, Name, Status, Available Quantity, Sell Price, Description
     - Edit modal: Edit Name, Owner, Active status
     - Create new VW button
     - Export to Excel action
   - Validation: Enforce 1:1 Unit-to-VW constraint via Apex trigger
   - Performance: Cache the 95 VWs in client-side state to avoid repeated SOQL queries

3. **Accessibility Improvements:**
   - Replace two-modal pattern (modal-over-modal validation) with inline toast notifications
   - Use standard `lightning-combobox` for dropdown instead of custom implementation
   - Add keyboard navigation and ARIA labels
   - Support responsive design for mobile access

4. **Data Model Mapping:**
   - MerchTank Virtual_Warehouse → Salesforce Virtual_Warehouse__c
   - MerchTank Unit → Salesforce Unit__c
   - MerchTank VW_Instance → Salesforce VW_Inventory_Instance__c
   - Owner (User ID/Name) → Salesforce User lookup

## Gaps & Risks

**Gap VWM-G1: No Per-Person Inventory Allocation in B2B Commerce**
- Severity: Critical
- Description: Salesforce B2B Commerce tracks inventory globally or by fulfillment location, not per-user or per-VW
- Impact: VW is the architectural foundation of MerchTank; without it, ordering, budgeting, and proxy workflows cannot function
- Resolution Options:
  1. **Full custom build** - 3-4 custom objects, 4-5 LWC components, 3-4 Apex classes. Effort: XL (6-8 weeks)
  2. **Simplify to budget-only model** - Eliminate per-item inventory; track only dollar budgets. Effort: M (2-3 weeks), but loses inventory visibility
  3. **B2B Commerce Inventory Locations** - Map each VW to an Inventory Location. Partially standard, stretches the model. Effort: L (4-5 weeks)
- Recommendation: Option 1 for feature parity; validate with BBC whether Option 2 simplification is acceptable
- Risk: If VW is just a display layer for inventory allocation without business rule enforcement, Option 3 might suffice

**Gap VWM-G2: 1:1 Unit-to-VW Constraint**
- Severity: Medium
- Description: Server-side validation enforces that only one VW can exist per Unit
- Impact: Data integrity; prevents duplicate VWs
- Resolution: Apex trigger on VW insert/update
- Effort: S

**Gap VWM-G3: 95 Virtual Warehouses at Scale**
- Severity: Medium
- Description: 95 VWs may cause performance issues with large dropdown selections and admin operations
- Impact: Admin console could be slow with 95+ items in list
- Resolution: Implement pagination, lazy loading, type-ahead search; cache in JavaScript
- Effort: Bundled with VWM-G1

**Gap VWM-G4: Unclear VW Usage Model**
- Severity: High
- Description: Is VW a display layer for inventory management, or does it enforce business rules?
- Impact: If VWs enforce rules (e.g., user can only see their VW's items), architecture changes significantly
- Resolution: Clarify with BBC whether VWs are:
  - A) Pure inventory visualization (display layer only)
  - B) Access control mechanism (user can only browse/order from their assigned VW)
  - C) Budget allocation container (budget tied to VW)

**Gap VWM-G5: Unit Concept Unclear**
- Severity: Medium
- Description: "Unit" is referenced as a unique identifier with 1:1 VW relationship, but its meaning is unclear
- Impact: If Unit represents Account, Department, or other entity, data model changes
- Resolution: Clarify Unit definition with BBC (is it a sales territory, wholesaler, cost center, etc.?)

## Dependencies

- [[buyer-account-model|Buyer Account Model]] (if Units map to Accounts)
- [[brand-budget-tracking|Brand Budget Tracking]] (if budgets are per-VW)
- [[product-catalog-and-browse|Product Catalog]] (VW contains product references)
- [[shopping-cart|Shopping Cart]] (items ordered from specific VW)
- [[virtual-warehouse-transfers|Virtual Warehouse Transfers]] (secondary feature)

## Open Questions

1. Is the VW model a pure inventory display layer, or does it enforce access control?
2. Are units in scope for phase 1, or can Unit-to-VW mapping be deferred?
3. How frequently are VWs created/modified? Is 95 static or growing?
4. Can a user be assigned to multiple VWs? (Yes, observed: Cyrus Sampsel has 2 VWs)
5. What determines which products are allocated to which VWs? Forecast? Manual assignment? Automatic distribution?
6. Do all 95 VWs need to be migrated, or can the first phase start with a subset?
7. Should the admin console be accessible to only the IT admin, or to procurement/brand team admins as well?

## Evidence

**Meeting 2 (Virtual Warehouse Walkthrough):**
- "Virtual Warehouses are the foundational concept in MerchTank. Each VW is a personal inventory allocation identified by a Lot number and assigned to an individual (typically a sales rep or distributor contact). The system currently holds 95 VWs."
- "The VW model is the architectural foundation of MerchTank. Without it, ordering, budgeting, and proxy workflows cannot function."
- "1:1 Unit-to-VW Constraint: Server-side validation enforces that only one VW can exist per Unit."
- "Some users have multiple VWs (e.g., Cyrus Sampsel has Lots #1003 and #1082)"
- Admin path: `/Core/Management/VirtualWarehouse`
