---
type: integration
client: boston-beer-company
status: planned
system-name: tradewearables-api
direction: inbound
frequency: batch
auth-method: oauth-2.0
created: 2026-04-06
updated: 2026-04-06
sources:
  - "BostonBeerCompany/meetings/02-virtual-warehouse-walkthrough/analysis/integration-assessment-vw-walkthrough.md"
tags:
  - vendor-api
  - product-catalog
  - apparel
  - phase-2
  - planned
---

# Integration: TradeWearables Product Catalog API

## Overview

[[tradewearables|TradeWearables]] is a merchandise and apparel supplier providing branded products to Boston Beer Company. This integration synchronizes TradeWearables product catalog, pricing, and inventory into [[salesforce-b2b-commerce|Salesforce B2B Commerce]], eliminating manual product maintenance and enabling real-time stock visibility.

**Business Drivers:**
- Current product catalog in [[merchtank|MerchTank]] is static (manually updated)
- Pricing changes in TradeWearables not reflected in Salesforce real-time
- No inventory synchronization (potential overselling)
- Manual product data maintenance is error-prone and time-consuming

**Target Users:**
- Catalog managers (real-time product sync)
- Procurement team (accurate inventory levels)
- End-users (accurate pricing, availability)

## Data Flow

### Inbound Flow (TradeWearables → Salesforce)

**Product Catalog Synchronization:**

```
TradeWearables Catalog System
  - Product master (SKU, name, description, images)
  - Variants (size, color, material)
  - Pricing (list price, volume tiers)
  - Inventory (stock levels per warehouse)
  |
  v
TradeWearables API Endpoint
  GET /api/products
  GET /api/products/{sku}
  GET /api/pricing/{sku}
  GET /api/inventory/{sku}
  |
  v
Salesforce Middleware (Mulesoft or Custom Apex)
  - Call API at scheduled intervals (daily or hourly)
  - Parse JSON response
  - Transform to Salesforce data model
  |
  v
Salesforce Platform Event
  Product_Sync_Event__e
    - product_sku, product_name, list_price, available_qty
  |
  v
Salesforce Flows & Triggers
  - Upsert Product2 record (create if new, update if exists)
  - Upsert ProductVariation records (size/color variants)
  - Upsert PricebookEntry (volume tiers)
  - Upsert Inventory (stock levels)
  |
  v
Salesforce B2B Commerce Storefront
  - Product appears in catalog
  - Pricing and availability displayed correctly
  - Real-time inventory prevents overselling
```

**Data Transformation:**

| TradeWearables Field | Salesforce Field | Mapping Logic |
|----------------------|------------------|---------------|
| SKU | Product2.ProductCode | Unique identifier |
| Product Name | Product2.Name | Display name |
| Description | Product2.Description | Full text, HTML if available |
| Category | ProductCategory (relationship) | Map to BBC category hierarchy |
| Image URL | Content Asset (or external URL) | Download and store or link |
| List Price | PricebookEntry.UnitPrice | For default price book |
| Volume Tier 1 (qty 1-50) | PricebookEntry.UnitPrice (qty 1) | Create separate entry per tier |
| Volume Tier 2 (qty 51-100) | PricebookEntry.UnitPrice (qty 51) | Tiered pricing |
| Available Quantity | Inventory.QuantityOnHand | Real-time stock |
| Lead Time Days | Product2.Lead_Time_Days__c | For fulfillment planning |

**Frequency:**
- **Recommended:** Hourly or 4-hour batch (to catch pricing/inventory changes)
- **Minimum:** Daily batch
- **Maximum:** Real-time (only if TradeWearables provides webhooks)

**Error Handling:**
- API timeout: Retry with exponential backoff
- Invalid product data: Log and skip; alert catalog manager
- Duplicate SKU: Upsert (update existing, don't create duplicate)
- Inventory negative: Flag as alert; prevent overselling

## Current Implementation

### Current State (MerchTank)

- **Product Catalog:** Static list in MerchTank database (manually imported from TradeWearables)
- **Update Frequency:** Ad-hoc (when TradeWearables notifies BBC of new products)
- **Pricing:** Manual entry (sourced from TradeWearables price list)
- **Inventory:** No visibility (TradeWearables inventory tracked in their system; MerchTank has no sync)
- **Issues:** Stale data, pricing errors, no stock visibility, manual maintenance burden

### Target State (Salesforce)

- **Product Catalog:** Real-time sync from TradeWearables API
- **Update Frequency:** Hourly or 4-hourly batch
- **Pricing:** Automatic volume tier calculations
- **Inventory:** Real-time availability
- **Benefits:** Accurate data, reduced manual effort, prevents overselling

## Integration Architecture

### Technical Design

**1. Authentication & API Access**

```
TradeWearables OAuth 2.0 Configuration
  Client ID: (provided by TradeWearables)
  Client Secret: (stored in Salesforce Secrets)
  Authorization URL: https://api.tradewearables.com/oauth/authorize
  Token URL: https://api.tradewearables.com/oauth/token
  Scopes: catalog.read, inventory.read, pricing.read

Salesforce Connected App
  - Authenticates via client credentials
  - Refreshes token hourly (or as needed)
  - Stores credentials in Secrets
```

**2. API Endpoints**

```
GET /api/v1/products
  Query Parameters:
    - page (pagination)
    - limit (25, 50, 100)
    - updated_since (timestamp, for incremental sync)
  Response: List of products with SKU, name, description, category, images

GET /api/v1/products/{sku}
  Response: Detailed product (all fields)

GET /api/v1/pricing/{sku}
  Response: Volume tiers, effective dates, promotional pricing

GET /api/v1/inventory/{sku}
  Query Parameters:
    - warehouse (optional, for multi-location stock)
  Response: Available quantity, reserved, backorder

POST /api/v1/webhooks
  (Optional) Register Salesforce webhook for real-time updates
  Events: product.created, product.updated, inventory.changed
```

**3. Salesforce Data Model**

```
Product2 (Standard Object - Extended)
  - ProductCode (TradeWearables SKU)
  - Name (TradeWearables product name)
  - Description (HTML description)
  - Product_Family (e.g., "Apparel", "Drinkware")
  - Category (Lookup to ProductCategory)
  - Lead_Time_Days__c (custom field)
  - Supplier (Text, "TradeWearables")
  - External_ID (TradeWearables SKU for upsert key)

ProductVariation
  - Parent product (e.g., "Samuel Adams T-Shirt")
  - Variant attributes: Size (S/M/L/XL), Color (Navy, Black)
  - SKU (e.g., "TSH-SAMAD-BLU-L")

PricebookEntry (Tiered Pricing)
  - Product (Lookup to Product2)
  - Pricebook (e.g., "TradeWearables Price Book")
  - UnitPrice (price at min quantity)
  - Quantity_Threshold__c (1, 50, 100, etc.)

Inventory (Custom Object)
  - Product (Lookup)
  - Warehouse (Lookup, if multi-location)
  - Quantity_On_Hand (from TradeWearables)
  - Quantity_Reserved (from orders)
  - Available_Quantity (formula: OnHand - Reserved)
  - Last_Sync_Date (timestamp)
```

**4. Integration Flow**

```
Scheduled Flow (Mulesoft or Apex Batch Job) - Runs Hourly
  |
  1. Authenticate to TradeWearables API (OAuth token refresh)
  2. Call GET /api/v1/products (with pagination)
  3. For each product:
     a. Call GET /api/v1/pricing/{sku}
     b. Call GET /api/v1/inventory/{sku}
  4. Transform to Salesforce data
  5. Upsert Product2, ProductVariation, PricebookEntry, Inventory
  6. Handle errors (log, retry, alert)
  7. Send Platform Event (for downstream processes)
  |
  v
Salesforce Flows & Triggers
  - Notify catalog managers of changes
  - Update search indexes
  - Recalculate cart prices (if active carts exist)
  |
  v
B2B Commerce Storefront
  - Products display with current pricing
  - Inventory levels show real-time availability
  - Volume tiers apply automatically
```

## Security & Authentication

**OAuth 2.0 Setup:**
1. Register Salesforce as OAuth client in TradeWearables
2. Store client_id and client_secret in Salesforce Secrets
3. Implement token refresh logic (before expiry)
4. Audit log all API calls (who, what, when)

**Data Security:**
- HTTPS with TLS 1.2+ (required)
- Certificate pinning (if TradeWearables supports)
- Rate limiting (respect TradeWearables API quotas)
- No sensitive data in logs (filter SKU if needed)

**Access Control:**
- Salesforce Field-Level Security (who can see pricing)
- Catalog managers can view sync logs
- IT can manage credentials

## Error Handling

| Scenario | Handling | Recovery |
|----------|----------|----------|
| API timeout | Retry 3x with backoff | Alert catalog manager; skip sync |
| Invalid product data | Log error; skip record | Catalog manager reviews logs |
| Duplicate SKU | Upsert (update existing) | No action; expected behavior |
| Negative inventory | Warn in alert | Investigate in TradeWearables |
| Authentication failure | Refresh OAuth token; retry | Page on-call if persistent |
| Rate limit hit | Implement backoff | Queue sync for next interval |

## Dependencies

**TradeWearables Requirements:**
- API documentation (endpoints, auth, rate limits)
- OAuth credentials (client_id, client_secret)
- Sandbox environment for testing
- SLA on API uptime

**Salesforce Requirements:**
- B2B Commerce installed and configured
- Custom objects (Inventory__c) created
- Mulesoft or custom Apex for integration
- Secrets management configured

**Data Preparation:**
- TradeWearables SKU mapping (consistent with BBC product codes)
- Category hierarchy (BBC categories → TradeWearables categories)
- Pricing strategy (volume tiers, margins, discounts)

## Implementation Timeline (Phase 2)

| Week | Activity | Deliverable |
|------|----------|-------------|
| 1-2 | API Discovery | Endpoint documentation, credentials, sandbox access |
| 3-4 | Data Mapping | SKU mapping, category hierarchy, pricing rules |
| 5-6 | Salesforce Model | Product2, ProductVariation, PricebookEntry, Inventory |
| 7-8 | Integration Code | Mulesoft flow or Apex batch job |
| 9 | Testing | End-to-end product sync, pricing, inventory |
| 10 | UAT | Catalog managers test storefront product display |

**Total Effort:** 10 weeks (Phase 2 scope)

## Open Questions

1. **API Availability:** Does TradeWearables expose product, pricing, and inventory APIs?
2. **Webhook Support:** Does TradeWearables offer webhooks for real-time updates?
3. **Product Identifiers:** Are SKUs globally unique or manufacturer-specific?
4. **Pricing Structure:** Are volume tiers static or dynamic (based on market demand)?
5. **Inventory Accuracy:** How frequently does TradeWearables update inventory? (Daily? Real-time?)
6. **Rate Limiting:** What are TradeWearables API rate limits?
7. **Historical Data:** Should historical product pricing be migrated from MerchTank?

## Related Pages

**Platforms:**
- [[salesforce-b2b-commerce|Salesforce B2B Commerce]] — Target platform
- [[merchtank|MerchTank]] — Current system

**Integrations:**
- [[vendor-fulfillment|Vendor Fulfillment Integration]] — Order transmission to TradeWearables
- [[oracle-erp-integration|Oracle ERP Integration]] — Invoice matching

**Entities:**
- [[tradewearables|TradeWearables]] — Vendor
- [[boston-beer-company|Boston Beer Company]] — Customer

## Notes

- TradeWearables product catalog sync is **Phase 2 priority** (after core B2B Commerce launch)
- Recommend **API discovery call** with TradeWearables early to confirm capabilities
- Consider **phased rollout**: Start with TradeWearables (strategic vendor), then expand to other suppliers
- Inventory sync is **critical to prevent overselling** — test thoroughly in sandbox before production
