---
type: feature
client: boston-beer-company
status: draft
category: ordering
decision: custom
effort: M
priority: P1
created: 2026-04-06
updated: 2026-04-06
sources:
  - /sessions/sweet-trusting-ride/mnt/Vendale-Agentics/BostonBeerCompany/meetings/02-virtual-warehouse-walkthrough/analysis/gap-analysis-bbc-vw-walkthrough.md
  - /sessions/sweet-trusting-ride/mnt/Vendale-Agentics/BostonBeerCompany/meetings/03-custom-requests/analysis/gap-analysis-bbc-custom-requests-meeting.md
tags:
  - ordering
  - product-management
  - pricing
---

# Pack-Based Ordering Model

## Description

BBC's fundamental unit of measure is the "packout" — the physical packaging of merchandise. All quantities, pricing, and inventory are expressed in packouts, not individual items. For example: "1 packout = 12 items" or "1 packout = 50 items". Pricing is per packout, inventory is tracked in packouts, and users order in packout quantities. This model is pervasive across catalog, cart, checkout, order, and fulfillment workflows.

## Current Implementation

**Product Definition:**
- Qty per Packout: Number of individual items in one packout (e.g., 1, 12, 20, 50)
- Price per Packout: Pricing is per packout unit, not per item
- Packouts Available: Inventory tracked in packout units

**Ordering:**
- Users select quantity in packout units (not individual items)
- Cart displays "# of Packs Qty" (editable spinner)
- Pricing calculated per packout

**Business Rules:**
- Qty per Packout is informational (tells user how many items are in a pack)
- All calculations must use packout units
- Some packouts contain 1 item (special/custom items)
- Some packouts contain 50 items (bulk items)

## Target Implementation

1. **Product Data Model:**
   - Product2 field: `Qty_Per_Packout__c` (number: 1, 12, 20, 50, etc.)
   - PricebookEntry field: `Unit_Price_Per_Packout__c` (price per packout)
   - Product inventory: Tracked in packout units in VW_Inventory_Instance__c

2. **Ordering Model:**
   - CartItem.Quantity = number of packouts (not items)
   - OrderItem.Quantity = number of packouts
   - Display/validation logic: "You ordered 5 packouts of 12 items = 60 items"

3. **Display Layer (All Touchpoints):**
   - Catalog: Show "Price per pack of [Qty_Per_Packout__c]"
   - Cart: Display quantities as packouts with helper text
   - Checkout: Confirm totals in packouts and items
   - Order History: Show quantities in packouts and items

4. **Calculations:**
   - Total Items = Quantity * Qty_Per_Packout__c
   - Extended Price = Quantity * Unit_Price_Per_Packout__c
   - Budget validation: Use packouts for quantity checks, multiply by unit price for dollar amount

## Gaps & Risks

**Gap PBM-G1: Pack-Based Model Pervasive Across Platform**
- Severity: High
- Description: Every calculation (pricing, inventory, budget, reporting) depends on packout model
- Impact: If not handled consistently, order totals could be wrong
- Resolution: Consistent data model and display logic across all features
- Effort: M (threaded through multiple features)

**Gap PBM-G2: B2B Commerce Default is Item-Based**
- Severity: High
- Description: Salesforce B2B Commerce assumes individual items as unit of measure
- Impact: All standard components need customization
- Resolution: Override standard components with custom pack-aware logic
- Effort: M-L (depends on feature scope)

**Gap PBM-G3: Reporting Complexity**
- Severity: Medium
- Description: Reports must show both packouts and items for clarity
- Impact: If reports show only packouts, users won't understand quantities
- Resolution: Formula fields to calculate item counts in reports
- Effort: S (bundled with feature implementations)

**Gap PBM-G4: Customer Communication**
- Severity: Medium
- Description: Emails, invoices, and documents must clearly show packout and item quantities
- Impact: Customer confusion if unclear
- Resolution: Template variables for both packout and item quantities
- Effort: S (bundled with notification templates)

## Dependencies

- [[product-catalog-and-browse|Product Catalog]] (Qty_Per_Packout__c field)
- [[shopping-cart-with-budget|Shopping Cart]] (packout-based quantity)
- [[brand-budget-tracking|Brand Budget Tracking]] (packout pricing)
- All ordering and fulfillment features

## Open Questions

1. Are there any products where Qty_Per_Packout__c varies (e.g., customer can choose pack size)?
2. Should pricing tiers exist (e.g., bulk discount for 10+ packouts)?
3. How should partial packouts be handled if ordered (e.g., customer wants 5 items from a 12-item pack)?

## Evidence

**Meeting 2 (VW Walkthrough):**
- "Quantities are in packout units (not individual items)"
- "All quantities, pricing, and inventory operate in pack units"
- "Qty per Packout ranges from 1 to 50"
- "Cart columns: SKU, Description, Qty/Packed, $/Packed, Packs Available, Backorder Allowed?, # of Packs Qty (editable), Total Packs Qty, Total Packed $"

**Meeting 3 (Custom Requests):**
- "BBC orders merchandise in packout units (1, 12, 20, 50 per packout), not individual items"
- "Pack-based ordering model is the 'fundamental unit of measure'"
- "This must be threaded through every touchpoint: catalog, cart, checkout, order, fulfillment, reporting"
