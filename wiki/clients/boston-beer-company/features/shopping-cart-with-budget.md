---
type: feature
client: boston-beer-company
status: draft
category: checkout
decision: custom
effort: L
priority: P1
created: 2026-04-06
updated: 2026-04-06
sources:
  - /sessions/sweet-trusting-ride/mnt/Vendale-Agentics/BostonBeerCompany/meetings/02-virtual-warehouse-walkthrough/analysis/gap-analysis-bbc-vw-walkthrough.md
  - /sessions/sweet-trusting-ride/mnt/Vendale-Agentics/BostonBeerCompany/meetings/03-custom-requests/analysis/gap-analysis-bbc-custom-requests-meeting.md
tags:
  - shopping-cart
  - budget-enforcement
  - checkout
---

# Shopping Cart with Brand-Level Budget Enforcement

## Description

MerchTank's shopping cart is the most business-logic-dense screen, combining standard e-commerce cart functionality with BBC-specific features: brand grouping, per-brand budget validation, pack-based quantity display, and proxy ordering context. Items in the cart are grouped by brand family, with a "Available Budget" and "Current Total" displayed per brand group. Users can adjust quantities and see real-time budget consumption. The system enforces budget limits at checkout (hard stop — orders cannot exceed remaining balance).

## Current Implementation

**User Workflow:**
1. User adds items from various brands to cart
2. Cart displays items grouped by brand (e.g., "Samuel Adams" brand badge)
3. Per-brand group shows: Available Budget, Current Total
4. Cart columns: SKU, Description, Qty/Packed (units per packout), $/Packed (price per packout), Packs Available, Backorder Allowed?, # of Packs Qty (editable), Total Packs Qty, Total Packed $
5. User enters per-line "Need By" date
6. User can adjust pack quantities via spinner controls
7. Real-time budget validation: as quantities change, "Current Total" updates and turns red if budget exceeded
8. System prevents checkout if any brand budget is exceeded

**Business Rules:**
- Quantities are in packout units (e.g., 12, 20, 50 items per packout)
- Pricing is per packout (not per item)
- Items grouped by brand family
- Available Budget = Initial Allocation - Previously Ordered - Current Cart Total
- Qty Packed = number of individual items in one packout unit
- Packs Available = current inventory for that item in packouts
- Backorder Allowed = flag indicating if user can order beyond available inventory
- Need By dates are entered per line item
- Proxy ordering context appears as green header: "VW (Sandra Paterson) | Paterson, Sandra"

**Current Technical Implementation:**
- Custom cart table layout in MerchTank
- Brand grouping via JavaScript/query logic
- Real-time budget validation (no page reload)
- Budget lookup queries the brand budget table
- Quantity changes trigger budget recalculation

**Systems Involved:**
- MerchTank cart, brand/product data, budget tables, checkout validation logic

## Target Implementation

Salesforce B2B Commerce provides a standard cart and checkout, but BBC's brand grouping, pack-based display, and budget enforcement are entirely custom.

**Proposed Salesforce Architecture:**

1. **Custom LWC: `c-merchtank-cart`**
   - Replace standard B2B Commerce cart component
   - Two-column layout: Product list on left, Budget Summary on right
   - Brand grouping by rendering items within brand sections
   - Per-brand budget summary card: Available Budget, Current Total, Remaining (updates in real-time)
   - Cart table columns: SKU, Description, Qty per Packout, Price per Packout, Packs Available, # of Packs (editable spinner), Total Packs, Total $
   - Per-line Need By Date field (date input)
   - Real-time calculation as user adjusts quantities
   - Color coding: Red background if brand budget exceeded

2. **Budget Enforcement Logic:**
   - Apex class `CartBudgetValidator` implementing `sfdc_checkout.CartValidation` interface
   - On checkout attempt: Query Brand_Budget__c records for current user
   - Group cart items by brand
   - For each brand: Sum cart total, compare to available balance
   - If any brand exceeds budget: Return validation error with message per brand
   - Checkout is blocked until all brands are within budget

3. **Custom Fields:**
   - CartItem: Add `Need_By_Date__c` (date field for per-line need-by dates)
   - CartItem: Add `Pack_Quantity__c` (number of packouts, not individual items)
   - Product2: Confirm `Qty_Per_Packout__c` and `Price_Per_Packout__c` fields exist

4. **Proxy Ordering Context:**
   - If in proxy mode: Display green banner at top of cart: "VW ([Owner Name]) | [Owner Name]"
   - Cart totals and budget availability calculated against the VW owner's budget, not the logged-in user's budget
   - See [[proxy-ordering]] feature for full context

5. **Real-Time Calculation:**
   - JavaScript in the LWC listens to quantity change events
   - On change: Call Apex method to recalculate budget availability for all brands in cart
   - Update display without page reload
   - Toggle color coding on budget summary cards

## Gaps & Risks

**Gap SCB-G1: Pack-Based Ordering Model**
- Severity: High
- Description: MerchTank uses packouts as the unit of measure; B2B Commerce uses individual items
- Impact: Every calculation (cart totals, pricing, budget, inventory) must work in packouts
- Resolution: Add Qty_Per_Packout__c and Price_Per_Packout__c to Product2; custom cart LWC to display/calculate in packouts
- Effort: M (pervasive across multiple features)
- Risk: If not handled consistently, order totals could be wrong

**Gap SCB-G2: Brand Grouping**
- Severity: Medium
- Description: Standard B2B Commerce cart displays flat item list; BBC cart groups by brand
- Impact: UX differs significantly
- Resolution: Custom cart LWC with brand-based grouping logic
- Effort: M (custom rendering)

**Gap SCB-G3: Real-Time Budget Validation**
- Severity: High
- Description: No page reload; as user adjusts quantities, budget availability updates in real-time
- Impact: If calculation is slow, UX suffers
- Resolution: Efficient Apex method that calculates only affected brands; lightweight state management in LWC
- Effort: M (performance optimization)

**Gap SCB-G4: Per-Line Need By Dates**
- Severity: Medium
- Description: Each item in cart can have a different need-by date
- Impact: Need-by dates must flow through to OrderItem level
- Resolution: Custom Need_By_Date__c field on CartItem and OrderItem
- Effort: S (field definition + data passing)

**Gap SCB-G5: Enforcement Behavior Clarity**
- Severity: High
- Description: Assumed hard stop (prevents checkout if budget exceeded)
- Impact: If soft warning is desired, approval workflow needed
- Resolution: Confirm with BBC business stakeholders
- Effort: M (if approval needed)

**Gap SCB-G6: Backorder Handling**
- Severity: Medium
- Description: Items may allow ordering beyond available inventory if "Backorder Allowed" flag is true
- Impact: Quantity validation must check Backorder_Allowed__c flag
- Resolution: Cart validation logic: if qty > available AND NOT backorder_allowed, return error
- Effort: Bundled with SCB-G1

## Dependencies

- [[brand-budget-tracking|Brand Budget Tracking]] (budget availability data)
- [[virtual-warehouse-model|Virtual Warehouse Model]] (if budgets are per-VW)
- [[product-catalog-and-browse|Product Catalog]] with pack-based pricing
- [[proxy-ordering|Proxy Ordering]] (for proxy context display)
- [[checkout-apis|Checkout APIs]] (for budget validation hook)

## Open Questions

1. Is budget enforcement a hard stop or a soft warning with approval?
2. Can users save carts and return later, or is checkout immediate?
3. Are there cart-level discounts or promotions beyond per-item pricing?
4. Should the cart remember quantities from previous orders (quick reorder)?
5. Are there SKU aliases or product codes that users prefer to use for search/entry?
6. How should the cart handle out-of-stock items? Remove, gray out, or show as unavailable?

## Evidence

**Meeting 2 (Virtual Warehouse Walkthrough):**
- "The cart at `/order/cart?orderid=[id]` is the most business-logic-dense screen in MerchTank."
- "It combines standard cart functionality with brand grouping, budget validation, pack-based display, and proxy ordering context."
- "Items appear in cart grouped by brand (e.g., 'Samuel Adams' brand badge)"
- "Each brand group shows: Available Budget and Current Total"
- "Checkout prevents checkout when order exceeds remaining budget" (hard stop assumption)

**Meeting 3 (Custom Requests):**
- Merchandise ordering section describes "Pack-Based Ordering Model" as critical
- "All quantities, pricing, and inventory operate in pack units"
