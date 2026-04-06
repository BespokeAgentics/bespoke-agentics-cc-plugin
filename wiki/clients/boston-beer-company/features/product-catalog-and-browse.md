---
type: feature
client: boston-beer-company
status: draft
category: catalog
decision: config
effort: M
priority: P1
created: 2026-04-06
updated: 2026-04-06
sources:
  - /sessions/sweet-trusting-ride/mnt/Vendale-Agentics/BostonBeerCompany/meetings/01-merchtank-overview/analysis/gap-analysis-sample-bbc-merchtank.md
  - /sessions/sweet-trusting-ride/mnt/Vendale-Agentics/BostonBeerCompany/meetings/02-virtual-warehouse-walkthrough/analysis/gap-analysis-bbc-vw-walkthrough.md
  - client-email-merchtank-feeder-systems-2026-04-06
tags:
  - catalog
  - product-management
  - search
  - email
---

# Product Catalog and Browse

## Description

MerchTank organizes merchandise in a two-dimensional catalog structure: Programs (time-bound campaigns or evergreen Everyday) and Brands (12+ beer brands: Samuel Adams, Twisted Tea, Angry Orchard, Truly, Dogfish Head, etc.). Users navigate from a dashboard tile grid to filtered catalog views. Products are displayed as horizontal cards with large images, thumbnail carousels, variant options, and pack-based pricing. This feature is foundational to the merchandising business and maps well to Salesforce B2B Commerce with minor customization.

## Current Implementation

**Navigation:**
- Dashboard home page with two tile grid sections:
  - "Company Programs" (6 tiles): EVERYDAY, CUSTOM DESIGN, HOT DEALS, ITEMS FROM SCRATCH, PPE, PROGRAM SAMPLES
  - "Brands" (8+ tiles): Samuel Adams, Angry Orchard, Coney Island, Dogfish Head, Boston Beer, and others
- Clicking a tile navigates to filtered catalog view: `/Core/Catalog/CatalogID=[id]`

**Catalog Browse:**
- Products display in a grid with filtering options
- Sub-type filtering (dropdown or chips)
- Grid/list view toggle
- Sub-navigation links: "File Schedule Information", "Wholesale Gallery"

**Product Card:**
- Large product image with numbered thumbnail carousel (for alternate views)
- Variant "Options" dropdown for size, color, etc.
- Key-value detail panel:
  - SKU, Title, Qty per Packout, Ship Method, Packouts Available, Location
- "Buy/Add" button with quantity input (in packouts)
- Price displayed per packout

**Product Fields:**
- SKU, Title, Brand, Category (brand family), Pack-out size (1, 12, 20, 50, etc.)
- Pricing: Per packout (not per item)
- Location: Fulfillment warehouse location (e.g., "3601 N. Silver...")
- Shipping Method: Ground, 2nd Day Air, etc.
- Available Inventory: In packout units
- Images: Multiple per product for carousel

**Business Rules:**
- Products always assigned to exactly one brand (even if multi-brand items exist)
- Qty per Packout ranges from 1 to 50
- Packaging info displayed but pricing is per packout
- Some items may have $0.00 pricing (promotional or allocated)

## Target Implementation

Salesforce B2B Commerce provides native product catalog, search, and filtering. Significant customization needed for dashboard tiles and pack-based display.

**Proposed Salesforce Architecture:**

1. **Product Catalog Structure:**
   - Standard ProductCatalog object
   - Product2 records with custom fields:
     - `Qty_Per_Packout__c` (number: 1, 12, 20, 50, etc.)
     - `Fulfillment_Location__c` (text or lookup)
     - `Ship_Method__c` (picklist)
     - `Backorder_Allowed__c` (checkbox)
   - ProductMedia for multiple product images (supports carousel natively)

2. **Category Hierarchy:**
   - ProductCategory with two-level hierarchy:
     - Level 1: Programs (EVERYDAY, CUSTOM DESIGN, HOT DEALS, ITEMS FROM SCRATCH, PPE, PROGRAM SAMPLES)
     - Level 2: Brands (Samuel Adams, Angry Orchard, etc.)
   - Products assigned to both Program and Brand categories

3. **Dashboard Tile Grid:**
   - Custom LWC: `c-program-tile-grid` and `c-brand-tile-grid`
   - CMS Content records drive tile definitions (name, image, description, link)
   - Tiles navigat to filtered search results page with category filter pre-set

4. **Search Results Page:**
   - Standard B2B Commerce search results with custom product card LWC
   - Faceted filtering: Sub-types, Price Range, Availability
   - Grid/list view toggle (standard)
   - Sorting: Relevance, Name, Price

5. **Product Card Layout:**
   - **Option A (Minimal change):** Use standard B2B Commerce vertical card layout
     - Product image, title, price, "Add to Cart" button
     - Pack-out info as secondary text
   - **Option B (Custom layout):** Horizontal card with image + detail panel
     - Matches current MerchTank UX closely
     - Requires custom LWC

6. **Pricing:**
   - PricebookEntry with `Unit_Price__c` per packout
   - Pricing displayed as "Price per [Packout Unit]" (e.g., "$25.00 per pack of 12")

## Gaps & Risks

**Gap PCB-G1: Tile-Grid Dashboard vs. Search-First B2B Commerce**
- Severity: Medium
- Description: Standard B2B Commerce is search-first; tile navigation is non-standard
- Impact: UX differs from MerchTank; may require user retraining
- Resolution: Custom tile grid LWCs for visual continuity (quick win)
- Effort: M (1-2 weeks for LWCs)

**Gap PCB-G2: Pack-Based Pricing and Display**
- Severity: High
- Description: All pricing, inventory, and display use packouts; B2B Commerce uses items
- Impact: Must be threaded through catalog, cart, checkout, reporting
- Resolution: Custom fields + LWC display logic (see [[shopping-cart-with-budget]] for cart details)
- Effort: M (shared across multiple features)

**Gap PCB-G3: Horizontal vs. Vertical Product Card Layout**
- Severity: Low
- Description: Current MerchTank cards are horizontal; B2B Commerce standard is vertical
- Impact: UX difference
- Resolution: Option A (use standard) or Option B (custom LWC)
- Effort: Option A (S), Option B (M)

**Gap PCB-G4: Product Image Carousel**
- Severity: Low
- Description: MerchTank shows numbered thumbnail carousel for alternate views
- Impact: B2B Commerce supports multiple images but UX may differ
- Resolution: Standard B2B Commerce image carousel should be acceptable
- Effort: S (or M if exact replication needed)

## Dependencies

- [[product-data-migration|Product Data Migration]] (catalog and pricing)
- [[brand-budget-tracking|Brand Budget Tracking]] (pricing and display)
- [[program-based-ordering-windows|Program-Based Ordering Windows]] (program category visibility)
- [[pack-based-ordering|Pack-Based Ordering Model]] (quantity units)

## Open Questions

1. Should horizontal product card layout be replicated for UX continuity, or use standard vertical cards?
2. Are all 12+ brands required in Phase 1, or can Phase 1 launch with a subset?
3. Should the "Wholesale Gallery" and "File Schedule" sub-navigation remain, or can they be deprecated?
4. How many products are in the catalog? Will search performance be an issue?
5. Are there seasonal product rotations, or is the catalog relatively static?

## Evidence from Email: MerchTank Feeder Systems (2026-04-06)

Source: Client email — Brand/Creative and Procurement department notes
Date: 2026-04-06

**Item setup workflow involves WorkFront → MDM → SAP:**
- WorkFront tasks collect all needed info for an item to be set up in MerchTank
- During Paper item setup, Brand coworker goes to WorkFront to get the proof, downloads thumbnail image, uploads to MT in .jpg format
- **Procurement automation**: If "Upload to Merchtank" is selected in WorkFront, data is sent to **MDM (Master Data Management)** which notifies Procurement and Creative Operations. The specified team generates a **part number in MDM** which pushes to **SAP** and back to the WorkFront project.
- For **Hard Goods**: Procurement takes requested assets and puts them to bid with suppliers in **SAP Ariba**. Pricing and setup info shared in WorkFront for Commercial Marketing to complete MerchTank item setup.

**Key insight**: Product catalog item creation is a multi-system workflow (WorkFront → MDM → SAP → MerchTank). Salesforce migration must account for how new items will be created and part numbers generated.

## Evidence

**Meeting 1 (MerchTank Overview):**
- "The Dashboard at `/Core/Catalog/Dashboard` is the primary entry point. It presents two tile grid sections — 'Company Programs' (6 tiles) and 'Brands' (8+ branded logo tiles) — that navigate to filtered catalog views."
- Programs: EVERYDAY, CUSTOM DESIGN, HOT DEALS, ITEMS FROM SCRATCH, PPE, PROGRAM SAMPLES
- Brands: 12+ beer brands including Samuel Adams, Twisted Tea, Angry Orchard, Truly, Dogfish Head, Coney Island

**Meeting 2 (VW Walkthrough):**
- "Products display in a horizontal row layout on catalog pages. Each product card shows a large image with thumbnail carousel, an 'Options' dropdown for variants, a key-value detail panel (Label, Title, SKU, Qty Packed, Ship Method, Packouts Available, Location), and a 'Buy/Add' button with quantity input."
- Pricing: "All quantities are in packout units"
- "Qty per Packout ranges from 1 to 50"
