---
type: entity
client: boston-beer-company
status: active
category: vendor
created: 2026-04-06
updated: 2026-04-06
sources:
  - "BostonBeerCompany/meetings/02-virtual-warehouse-walkthrough/analysis/integration-assessment-vw-walkthrough.md"
  - "BostonBeerCompany/meetings/04-fulfillment-demo/analysis/integration-assessment-fulfillment-demo.md"
tags:
  - vendor
  - supplier
  - merchandise
  - apparel
  - product-catalog
---

# TradeWearables — Vendor Entity

## Overview

**TradeWearables** is one of Boston Beer Company's merchandise and apparel suppliers. The company provides branded merchandise products (apparel, drinkware, promotional items) to BBC and is integrated into [[merchtank|MerchTank]] as a product catalog vendor.

TradeWearables is referenced in BBC's [[vendor-fulfillment|fulfillment vendor ecosystem]] and merchandise sourcing operations. As a strategic integration opportunity, TradeWearables' product catalog is being evaluated for automated API integration into [[salesforce-b2b-commerce|Salesforce B2B Commerce]].

## Key Characteristics

**Vendor Properties:**
- **Type:** Merchandise and apparel supplier
- **Product Categories:** Apparel (shirts, hats, outerwear), drinkware, promotional items, branded merchandise
- **Relationship to BBC:** Product supplier; integrated into MerchTank catalog
- **Status:** Active supplier (in current product database)
- **Integration Type:** Product catalog synchronization

**Products Offered (Inferred):**
- Branded apparel with BBC logo and brand customization
- Drinkware (mugs, glasses, bottle koozies)
- Promotional merchandise (hats, bags, keychains)
- Custom design and embroidery services (likely)
- Size/color variants

## Integration with BBC

### Current Integration (MerchTank)

**Integration Type:** Product catalog integration
- **Direction:** Inbound (product list, pricing, availability)
- **Data Exchanged:** Product SKU, description, price, variants, inventory/availability status
- **Frequency:** Unclear (static catalog likely; updated on schedule or via manual upload)
- **Protocol:** Unknown (likely vendor portal API, file upload, or manual data entry)
- **Status:** Active (TradeWearables products visible in MerchTank product listings)

**Product Discovery:**
- Users browse MerchTank product catalog by category (Apparel, Drinkware, etc.)
- TradeWearables items appear alongside other vendor products
- Price, description, and variants displayed
- User can select items and add to cart

**Fulfillment:**
- TradeWearables is one of 20+ fulfillment vendors in MerchTank
- Orders assigned to TradeWearables via procurement manual release workflow
- Fulfillment instructions sent via (unknown mechanism: email, vendor portal, EDI)
- Order fulfillment status not tracked in MerchTank (manual coordination by procurement)

### Planned Integration (Salesforce B2B Commerce)

**Phase 2 — Integration & Automation (Months 4-6, Target Q3 2026):**

**Objective:** Implement [[tradewearables-api|automated product catalog API integration]] with TradeWearables

**Current State Assessment:**
- TradeWearables product catalog is currently static or manually updated in MerchTank
- No real-time inventory synchronization (likely)
- Pricing may be manually maintained

**Target State:**
- **Real-Time Catalog Sync** — Automatic synchronization of product catalog, pricing, and availability from TradeWearables API
- **Automated Inventory Tracking** — Real-time stock levels per product (if TradeWearables provides inventory data)
- **Dynamic Pricing** — Volume-based pricing rules or promotional pricing pushed from TradeWearables
- **Order Transmission** — Automated order transmission to TradeWearables (vs. current manual email/portal)
- **Order Status Tracking** — Fulfillment status feed from TradeWearables back to Salesforce

**Integration Architecture (Proposed):**
```
TradeWearables API
  |
  +-- Product Catalog (nightly batch or hourly sync)
  |   |
  |   v
  +-> Salesforce Product2 & Variants (via middleware or Salesforce integration)
  |
  +-- Pricing Data
  |   |
  |   v
  +-> Salesforce PricebookEntry (volume tiers, cost)
  |
  +-- Inventory/Availability
  |   |
  |   v
  +-> Salesforce Inventory object (real-time or batch)
  |
  When User Orders:
  Order created in Salesforce
  |
  v
  Salesforce Order → TradeWearables API (order transmission)
  |
  v
  TradeWearables Fulfillment (internal process)
  |
  v
  TradeWearables → Salesforce (fulfillment status feed)
  |
  v
  Salesforce Order Status Updated (tracking visibility to customer)
```

**Benefits:**
- No manual product maintenance (catalog stays in sync with TradeWearables data)
- Real-time inventory visibility (vs. static listing)
- Dynamic pricing (volume tiers apply automatically at cart time)
- Automated order transmission (vs. manual email/portal upload)
- Order tracking (fulfillment status visible to users)

## Product Categories & Examples

Based on typical merchandise supplier portfolios:

| Category | Examples | Size/Color Variants |
|----------|----------|-------------------|
| **Apparel** | T-shirts, polos, hoodies, jackets, hats | S-3XL, multiple colors |
| **Drinkware** | Pint glasses, coffee mugs, water bottles, koozies | 16-32 oz, colors |
| **Promotional** | Tote bags, keychains, pens, stress balls | N/A, limited colors |
| **Accessories** | Socks, belts, scarves, earmuffs | One-size, multiple colors |
| **Equipment** | Umbrellas, coolers, backpacks | Standard, colors |

**Example Product Data (Expected):**
```json
{
  "sku": "TW-TSH-SAMAD-BLU-L",
  "name": "Samuel Adams Logo T-Shirt",
  "description": "100% cotton t-shirt with embroidered Samuel Adams logo",
  "category": "Apparel > T-Shirts",
  "brand": "Samuel Adams",
  "list_price": 12.99,
  "volume_pricing": [
    { "min_qty": 1, "price": 12.99 },
    { "min_qty": 50, "price": 10.50 },
    { "min_qty": 100, "price": 9.25 }
  ],
  "variants": {
    "size": ["S", "M", "L", "XL", "2XL", "3XL"],
    "color": ["Navy Blue", "Black", "Gray"]
  },
  "available_qty": 250,
  "lead_time_days": 7
}
```

## Vendor Contact & Relationship

**Contact Information (Inferred):**
- Primary contact: Likely listed in [[merchtank|MerchTank]] CONTACTS tab
- Email: Procurement team has direct email for order submission (current manual workflow)
- Account Manager: BBC likely has dedicated account rep at TradeWearables
- Terms: Volume discounts, lead times, payment terms (30, 60, or 90 days net)

**Relationship Management:**
- Strategic supplier (one of 20+)
- Integrated into product catalog (suggests preferred status)
- Procurement team maintains relationship (order release authority)
- Likely quarterly business reviews (QBRs) on sales, inventory, lead times

## Technical Integration Requirements

**API Capabilities (Expected):**
Based on typical merchandise supplier APIs:

1. **Product Catalog API**
   - GET /products — List all products with SKU, description, pricing
   - GET /products/{id} — Single product detail
   - Variants endpoint — Sizes, colors, configurations
   - Update frequency: Daily batch or real-time webhook

2. **Inventory API**
   - GET /inventory/{sku} — Current stock level
   - Update frequency: Hourly or real-time webhook

3. **Pricing API**
   - GET /pricing/{sku} — Volume-based pricing rules
   - Promotional pricing changes

4. **Order Management API**
   - POST /orders — Create order (SKU, quantity, shipping address, delivery date)
   - GET /orders/{id} — Order status and tracking
   - Webhooks for order status changes (Confirmed, Shipped, Delivered)

5. **Authentication**
   - OAuth 2.0 (likely) or API key-based
   - Sandbox environment for testing
   - Rate limiting and quotas

## Integration Risks & Mitigation

| Risk | Severity | Mitigation |
|------|----------|-----------|
| API downtime (catalog not syncing) | High | Implement fallback to last-known good data; alert on sync failure |
| Data quality (invalid SKU, missing pricing) | Medium | Data validation rules; manual review of product imports |
| Inventory accuracy (overselling) | Medium | Real-time sync with buffer inventory; order confirmation workflow |
| Pricing errors (wrong volume tiers) | Medium | Unit tests on pricing calculations; manual spot-check |
| API rate limits (bulk catalog updates) | Low | Batch processing; pagination; exponential backoff retry logic |
| Security (API key exposure) | High | Store API credentials in Salesforce Secrets; rotate regularly |

## Salesforce Configuration (Phase 2)

**Standard Salesforce Objects:**
- `Product2` — TradeWearables product (SKU, name, description, category)
- `ProductVariationParent` — Product variant parent (for size/color options)
- `ProductVariation` — Variant SKU (e.g., TSH-BLU-L)
- `PricebookEntry` — Pricing per product per price book (with volume tiers)
- `Inventory` (custom object likely) — Stock levels per product/location

**Custom Integration:**
- **Middleware (Mulesoft, Zapier, or custom Apex)** — Sync TradeWearables API → Salesforce
- **Scheduled Flow or Batch Apex** — Run nightly (or hourly) to pull product/inventory updates
- **Custom Pricing Rule** — Evaluate volume tiers at cart calculation time
- **Order Extension** — Transmit Salesforce order → TradeWearables API

**Development Effort Estimate:**
- API discovery & documentation: 1-2 weeks
- Salesforce data model setup: 1 week
- Middleware/integration code: 2-3 weeks
- Testing & validation: 1-2 weeks
- **Total: 5-8 weeks (Phase 2 scope)**

## Related Pages

**Platforms:**
- [[salesforce-b2b-commerce|Salesforce B2B Commerce]] — Target platform for integration
- [[merchtank|MerchTank]] — Current system (TradeWearables catalog in use)

**Integrations:**
- [[tradewearables-api|TradeWearables API Integration]] — Detailed integration architecture
- [[vendor-fulfillment|Vendor Fulfillment Integration]] — Multi-vendor orchestration

**Entities:**
- [[boston-beer-company|Boston Beer Company]] — Customer of TradeWearables
- [[oracle-erp|Oracle ERP]] — Financial system (invoicing)

## Notes

- TradeWearables is **one of 20+ fulfillment vendors** (others not documented in detail)
- API integration priority depends on:
  - TradeWearables order volume (% of total merchandise orders)
  - Current catalog update frequency (static vs. dynamic)
  - Availability of TradeWearables API (needs discovery call)
  - Strategic importance to BBC (preferred supplier vs. commodity)
- If TradeWearables API is not available, consider:
  - EDI/X12 catalog feed (traditional in retail)
  - CSV file upload (weekly manual refresh)
  - Web scraping (fragile; not recommended)
- **Recommend early integration discovery call** with TradeWearables to confirm API capabilities, authentication model, rate limits, and data formats before Phase 2 detailed design
