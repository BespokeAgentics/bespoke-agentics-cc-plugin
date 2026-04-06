---
type: platform
status: active
category: e-commerce
created: 2026-04-06
updated: 2026-04-06
sources:
  - "Lightning-web-runtime-docs/07-B2B-Commerce-Architecture-DataModel-Setup.md"
  - "Lightning-web-runtime-docs/08-B2B-Commerce-APIs-Extensions-Reference.md"
  - "salesforce/salesforce-commerce-product-configuration-guide/README.md"
  - "salesforce/sf-commerce-bootstrap-kit/01_bootstrap_runbook.md"
tags:
  - commerce-cloud
  - b2b
  - lwr
  - experience-builder
---

# Salesforce B2B Commerce — Platform Overview

## Overview

Salesforce B2B Commerce is a purpose-built e-commerce platform built on **Lightning Web Runtime (LWR)** that enables enterprise retailers, wholesalers, and distributors to operate customized storefronts. The platform combines pre-built commerce components with a standardized data model and extensible APIs, allowing rapid deployment of complex B2B ordering and fulfillment workflows.

B2B Commerce ships as the **Commerce Experience Builder template** — distinct from the generic "Build Your Own (LWR)" template — and includes dozens of pre-built Lightning Web Components for product catalogs, shopping carts, checkout, search, and order management.

### Key Characteristics

**Architecture & Deployment:**
- Runs exclusively on [[salesforce-lwc|Lightning Web Runtime (LWR)]]
- Available in Enterprise, Unlimited, and Developer editions with B2B Commerce add-on license
- Built on pre-configured multi-tenant Salesforce infrastructure
- Supports seamless third-party integration via APIs and middleware

**Core Capabilities:**
- **Product Management:** Catalogs with categories, variants, bundles, and hierarchical product structures
- **Pricing & Discounts:** Multiple price books, buyer group-specific pricing, volume discounts, promotional rules, coupon systems
- **Cart & Checkout:** Real-time inventory, multiple active carts per buyer, delivery group splitting, payment gateway integration
- **Search & Navigation:** Faceted search with 50+ filterable attributes, configurable sort rules, merchant-driven merchandising
- **Buyer Management:** Buyer groups (account hierarchies), role-based entitlements, negotiated pricing per buyer
- **Order Processing:** Order creation, confirmation workflows, integration with Salesforce Order Management and field service
- **Shipping & Fulfillment:** Built-in shipping calculations, third-party carrier integration, fulfillment provider APIs
- **Tax Compliance:** Configurable tax calculations, external tax service integration, tax exemption management
- **Extensibility:** Commerce Extensions framework for pricing, inventory, shipping, and tax customization

**Data Model Foundation:**
- `WebStore` — Store configuration, buyer groups, entitlements, publication settings
- `Product2` — Product records with SKU, description, active status, family and class
- `ProductCategory` — Category hierarchy and product-category associations
- `ProductCatalog` — Product catalog assignments to stores
- `PricebookEntry` — Pricing across multiple price books and buyer groups
- `WebCart` — Shopping cart records, per-buyer, with lifecycle tracking
- `CartItem` — Line items within carts with quantity, pricing, promotions
- `CartDeliveryGroup` — Grouping of cart items for separate shipments/delivery
- `Order` / `OrderItem` — Transactional records created after checkout
- `Promotion` — Discount rules, coupon codes, terms and conditions
- `Inventory` — Stock levels per location (virtual warehouse or fulfillment center)
- **Shipping:** Shipping methods, transit times, rate tables
- **Tax:** Tax configuration, rate lookups, exemption handling

**Data Limits & Constraints:**
- Filterable attributes per store: 50 (contact support for up to 100)
- Searchable attributes per store: 25 (contact support for up to 100)
- Facets per search query: 10 (auto-faceting returns top 10 most populated)
- Filter/facet values per attribute: 100 (hard limit)
- Sort rules per store: 10 (combined with attributes cannot exceed 70 total)
- Products per store: Generally 100k+ (verify with Salesforce for your org)
- Order history retention and performance tested to millions of orders

## Core API Architecture

B2B Commerce exposes the **Connect Commerce API** for all commerce operations:

**Address Management:**
- GET/POST/PATCH/DELETE operations for customer addresses
- Shipping and billing address separation
- Default address assignment

**Cart API:**
- Create/manage multiple active carts per buyer
- Add/remove items, adjust quantities (batch add up to 100 items)
- Apply promotions, coupons, delivery group splitting
- Transfer items to/from wishlists
- Real-time cart messages for stock availability, price changes, promotion notifications

**Checkout API:**
- Multi-step checkout flow: Contact → Shipping Address → Shipping Method → Tax/Payment → Order Placement
- Automatic shipping method and tax calculation on address change
- Saved payment method support for registered users
- Payment authorization before order placement (does NOT collect/store sensitive payment data)

**Product & Catalog APIs:**
- Browse product catalog with variants and bundles
- Search with faceted filtering and sort options
- Category navigation
- Pricing and inventory queries

**Pricing & Promotions API:**
- Real-time price calculation per buyer/buyer group
- Promotion applicability checking
- Coupon validation and redemption
- Volume pricing evaluation

**Order Management:**
- Order summary retrieval
- Order history and order detail queries
- Reorder workflows (bulk item transfer to new cart)
- Order status tracking

**Wishlist API:**
- Create and manage wishlists per user
- Add/remove items
- Share wishlists
- Transfer to carts

**Tax API:**
- Tax rate lookup by location
- Tax exemption handling
- External tax service integration

**Shipping API:**
- Shipping method availability checking
- Rate calculation per carrier/service level
- Shipping address validation
- Third-party carrier integration

## Extension & Integration Framework

### Commerce Extensions (Recommended)

**Architecture:**
Extensions hook into specific lifecycle points in cart calculation, checkout, and order processing. They are the **preferred approach** over the legacy Integrations framework (Winter 2024+).

**Domains:**
- **Pricing Extension** — Override list prices, apply negotiated pricing, implement complex discount logic
- **Inventory Extension** — Real-time inventory checks, allocation logic, backorder handling
- **Shipping Extension** — Custom carrier selection, rate calculation, service level routing
- **Tax Extension** — External tax engine integration, jurisdiction-based rules, exemption logic
- **Additional Domains** — Extensible to custom commerce services as needed

**Implementation Pattern:**
1. Create an Apex class implementing the Commerce extension interface
2. Register via Commerce Extension setup configuration
3. Extension executes during cart calculation or checkout lifecycle
4. Returns data or exceptions that modify flow (e.g., pricing override, inventory hold)

### Legacy Integrations Framework

Deprecated in favor of Extensions but still supported for existing B2B stores:

- **Tax Integration** — External tax calculation services (e.g., Avalara, Vertex)
- **Shipping Integration** — External shipping rate providers (e.g., EasyPost, ShipStation)
- **Payment Integration** — Payment gateway adapters (server-side or client-side)
- **Inventory Integration** — Real-time stock checks from WMS or ERP
- **Pricing Integration** — External pricing engines (e.g., SAP APM)

### Payment Processing

**Architecture:**
- Payment gateways registered in Salesforce Setup
- Payment gateway adapters implement `commercepayments.PaymentGatewayAdapter` interface
- Authorization occurs **before** order placement
- Platform components do NOT collect or store payment information

**Modes:**
- **Server-Side Payment Processing** — Sensitive data stays on Salesforce servers; communicates directly with payment provider; more secure, higher PCI compliance scope
- **Client-Side Payment Processing** — Embedded payment form (Stripe Elements, PayPal Hosted Fields); uses iframe; reduced PCI scope; requires CSP configuration

## Deployment & Development

**SFDX-First Approach:**
- Salesforce recommends **Salesforce DX (SFDX)** for all custom component development
- Source-driven deployment: version control → scratch org → production
- Parallel environment testing before production promotion
- GitHub repositories provided by Salesforce with reference implementations

**Required Tools:**
- Salesforce CLI (SFDX) for source synchronization
- Visual Studio Code with Salesforce Extension Pack
- Git for version control
- Node.js for component compilation (optional but recommended)

**Development Workflow:**
1. Create SFDX project: `sf project generate --name my-store`
2. Authorize org: `sf org login web --alias mystore`
3. Create scratch org or connect to sandbox
4. Develop custom Lightning Web Components following LWC patterns
5. Deploy: `sf project deploy start --target-org mystore`
6. Add components to Experience Builder via drag-and-drop

**Open Source Components:**
Salesforce provides open source implementations of standard B2B Commerce components (product pricing, search facets, cart, checkout, etc.). These can be cloned, customized, and deployed to any store.

## Key Gotchas & Considerations

**Search & Filtering:**
- Facet queries return only top 10 most-populated values if auto-faceting enabled
- Filter fields per query limited to 10 (user-selectable)
- Searchable/filterable attribute limits are per-store and require support lift to increase

**Pricing:**
- Multiple active price books per product require careful configuration
- Buyer group pricing is evaluated at cart calculation time, not at browse
- Promotions are coupon-based or rule-based (both supported, different flows)
- Strikethrough pricing requires separate price book entry

**Inventory:**
- Default Salesforce inventory model uses `ProductConsumptionSchedule` (historical); Inventory object is custom
- Real-time inventory sync from external WMS requires Extensions or polling
- Backorder/pre-order workflows require custom logic

**Cart Lifecycle:**
- Multiple active carts per buyer requires buyer selection of primary cart
- Delivery group splitting is available but requires explicit configuration in cart
- Cart abandonment workflows are not built-in (require Process Builder or Flows)

**Checkout Flow:**
- Four-step accordion (Contact → Address → Shipping → Payment) is not customizable via configuration
- Custom checkout layouts require LWC component replacement, not just styling
- Payment gateways must be registered and tested per org

**Shipping:**
- TBD (to-be-determined) shipping costs require deferred calculation or fulfillment-provider assignment
- Multiple carrier integrations require separate adapter implementations
- International shipping rules are not built-in; require custom logic

## Relationships & Cross-References

**Related Platforms:**
- [[salesforce-lwc|Lightning Web Components & Experience Cloud]] — Underlying technology for all UI
- [[merchtank|MerchTank]] — Legacy merchandise ordering system (legacy context for BBC migration)

**Integrations:**
- [[oracle-erp-integration|Oracle ERP Integration]] — Financial budget and invoice sync
- [[vendor-fulfillment|Vendor Fulfillment Integration]] — Third-party fulfillment provider coordination
- [[sso-authentication|SSO & Dual Authentication]] — Corporate identity provider federation

**Entities:**
- [[boston-beer-company|Boston Beer Company]] — Pilot customer for B2B Commerce migration
- [[oracle-erp|Oracle ERP]] — Financial system for budgets and invoicing
- [[tradewearables|TradeWearables]] — Product catalog vendor integration

## Notes

- The Commerce Experience Builder template is the **recommended starting point** for B2B stores; generic LWR template is rarely appropriate for commerce use cases
- Data model is **mostly standard** Salesforce objects; customizations are minimal for basic use cases but grow quickly for complex pricing, inventory, or fulfillment workflows
- Extension framework is actively developed; Integrations framework is legacy and may be deprecated in future releases
- Performance considerations: Store data limits allow for millions of orders and 100k+ products per store, but real-time inventory sync from WMS can introduce latency if not architected carefully
- The platform assumes a **batch or event-driven integration** architecture; real-time bidirectional sync requires careful design to avoid performance issues
