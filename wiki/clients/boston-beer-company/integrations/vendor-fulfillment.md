---
type: integration
client: boston-beer-company
status: planned
system-name: vendor-fulfillment
direction: outbound
frequency: on-demand
auth-method: varies
created: 2026-04-06
updated: 2026-04-06
sources:
  - "BostonBeerCompany/meetings/02-virtual-warehouse-walkthrough/analysis/integration-assessment-vw-walkthrough.md"
  - "BostonBeerCompany/meetings/04-fulfillment-demo/analysis/integration-assessment-fulfillment-demo.md"
  - client-email-merchtank-feeder-systems-2026-04-06
tags:
  - fulfillment
  - vendor-management
  - supply-chain
  - phase-2
  - planned
  - email
---

# Integration: Multi-Vendor Fulfillment Coordination

## Overview

Boston Beer Company uses 20+ third-party fulfillment vendors (merchandise suppliers, drop-ship partners, contract manufacturers) to fulfill merchandise orders. Currently, order transmission to vendors is **entirely manual** — procurement team manually releases orders via email or vendor portal uploads.

This integration automates order transmission to vendors, tracks fulfillment status, and provides real-time visibility into order processing across the vendor ecosystem.

**Business Drivers:**
- Manual order release is time-consuming (3+ hours/week procurement labor)
- No vendor fulfillment status feedback (operators manually track across 20+ systems)
- Inconsistent vendor communication (email, portal, phone)
- Order delays due to manual coordination

**Target Users:**
- Procurement team (automated order release, status tracking)
- Fulfillment vendors (structured order data, tracking visibility)
- Field users (can see when order ships)

## Data Flow

### Outbound Flow (Salesforce → Vendors)

**Order Transmission:**

```
Salesforce Order Created
  - Order number, order date, customer, delivery address
  - Line items: SKU, quantity, unit price, extended amount
  - Delivery instructions, preferred carrier, ship-by date
  |
  v
Auto-Assign Vendor (Based on Rules)
  - Product category → Vendor mapping (apparel → TradeWearables, drinkware → vendor X)
  - Vendor capacity and lead time evaluation
  - Cost optimization (if multiple vendors can fulfill)
  |
  v
Vendor Order Message
  - Translate to vendor format (EDI, JSON, CSV, XML)
  - Include delivery address, special instructions, carrier preferences
  - Payload includes: Order #, Line items (SKU, qty), Ship date, Delivery address
  |
  v
Transmission to Vendor (Multiple Options)
  - EDI over SFTP/AS2 (traditional retail, TradeWearables + others)
  - REST API (modern vendors)
  - Email (small vendors)
  - Vendor portal upload (for vendors with custom platforms)
  |
  v
Vendor Confirmation
  - Vendor acknowledges order receipt
  - Provides PO number or tracking
  - Optional: Provides lead time / ship date estimate
  |
  v
Salesforce Order Record Updated
  - Vendor Order ID / PO reference stored
  - Fulfillment status: Released, Confirmed, In-Fulfillment, Shipped
  - Tracking number populated (if available)
```

**Error Handling:**
- **Transmission failure:** Retry 3x; alert procurement if vendor endpoint unreachable
- **Vendor rejection:** Log reason; escalate to procurement for manual coordination
- **Missing data:** Validate order before transmission; prevent incomplete orders

### Inbound Flow (Vendors → Salesforce)

**Fulfillment Status Tracking:**

```
Vendor Fulfillment System
  - Order processing (picking, packing, labeling)
  - Shipment creation (tracking number generated)
  - Delivery updates (in-transit, delivered)
  |
  v
Vendor Status Feed (Multiple Options)
  - EDI 856 (advanced ship notice)
  - Email notification
  - API webhook (modern vendors)
  - Portal query (if no push available)
  |
  v
Salesforce Order Management
  - OrderItem fulfillment status updated
  - Tracking number and carrier recorded
  - Expected delivery date calculated
  - Customer notification triggered (optional)
  |
  v
Finance & Audit Trail
  - Fulfillment recorded for invoice matching (with Oracle ERP)
  - Historical tracking for performance metrics
```

## Current Implementation

### Current State (MerchTank)

**Order Release:**
- Procurement team manually reviews submitted orders in MerchTank
- Determines assigned vendor (based on product category or established relationship)
- Contacts vendor via email or portal upload with order details
- Vendor confirms order receipt (acknowledgment may be verbal or email)
- No formal order acknowledgment tracking

**Fulfillment Status:**
- Vendors send shipment notifications via email (when shipped)
- Procurement team manually enters tracking number into MerchTank
- Tracking copied 3x: UPS app → MerchTank order → Excel shadow system
- No automated status updates (vendor shipment data doesn't flow back)

**Issues:**
- Manual order release delays order processing (5-15 minutes per order × thousands of orders/day)
- No vendor capacity planning (potential double-booking, delays)
- Inconsistent vendor communication (no SLA)
- High error rate on manual data entry (tracking numbers mistyped)
- No automated notification to customers (they must check MerchTank)

### Known Vendor Integration Points

**Vendors with Existing Integration (Inferred):**
- [[tradewearables|TradeWearables]] — Likely EDI or web portal (apparel, drinkware)
- **Kirkwood** — Approved POS vendor (named in client email 2026-04-06; quotes requested via Outlook)
- **Six Strings** — Approved POS vendor (named in client email 2026-04-06; quotes requested via Outlook)
- 17+ other vendors (names not yet disclosed; likely regional fulfillment centers, print shops, embroiderers)

**Vendor Contact Information:**
- Stored in MerchTank CONTACTS tab
- Email addresses for order submission
- Portal URLs (for vendors with self-service platforms)
- Account managers / relationship contacts

**Vendor Quote & Order Workflow (from client email 2026-04-06):**
- Creative Team and Co-ops use **Outlook** to request quotes from approved vendors (Kirkwood, Six Strings, etc.) for specific MerchTank orders
- Once quote is received, info entered into MerchTank for sales rep review and approval
- POS proofs and supporting images attached at this stage for approval
- After approval, Creative Team/Co-ops pull order details from MerchTank and enter into **vendor portals** to process and ship POS materials
- Vendor portals also used to obtain tracking info when requested by sales reps; tracking recorded back in MerchTank

**Hard Goods Procurement (from client email 2026-04-06):**
- Procurement puts hard goods assets to bid with suppliers in **SAP Ariba**
- Pricing and setup info shared in WorkFront for Commercial Marketing to complete MerchTank item setup

## Target Architecture

### Integration Components

**1. Vendor Master Data**

```
Salesforce Custom Object: Vendor__c
  - Vendor name, address, contact info
  - Integration type (EDI, API, email, portal)
  - Endpoint URL (if API or EDI)
  - Authentication credentials (stored in Secrets)
  - Lead time (business days to fulfill)
  - Product categories assigned
  - Rate / cost (markup %)
  - Status (active, inactive)
  - SLA for order transmission and fulfillment
```

**2. Vendor Order Routing**

```
Salesforce Flow: Auto-Assign Vendor
  Input: Product category, quantity, delivery location
  Logic:
    - Look up product → vendor mapping
    - Check vendor capacity (concurrent orders, max qty)
    - Evaluate lead time vs. needed date
    - Select best vendor (cost or speed)
  Output: Assigned vendor, vendor order ID
```

**3. Order Transmission**

```
Apex Class: VendorOrderAdapter
  - Convert Salesforce Order → Vendor format (EDI 850, JSON, CSV)
  - Call vendor endpoint (REST API or SFTP)
  - Handle authentication and error cases
  - Log transmission (audit trail)
  - Update Salesforce Order with vendor confirmation

Supported Formats:
  - EDI X12 850 (Purchase Order)
  - JSON REST API (modern vendors)
  - CSV file upload (email attachment)
  - Form submission (legacy vendors)
```

**4. Fulfillment Status Tracking**

```
Salesforce: Vendor Webhook Receiver
  - Accepts POST requests from vendors
  - Parses 856 (Advanced Ship Notice) or custom payload
  - Updates OrderItem.Fulfillment_Status
  - Records tracking number and carrier
  - Triggers customer notification

Fallback: Scheduled Job (if vendor doesn't push)
  - Query vendor portal or API (hourly or daily)
  - Fetch shipment status
  - Update Salesforce Order (same as webhook)
```

### Security & Authentication

**Vendor Credentials:**
- Store in Salesforce Secrets (encrypted)
- Rotate annually
- Separate credentials per vendor
- Audit log for credential access

**API Security:**
- HTTPS with certificate pinning
- OAuth 2.0 (if vendor supports)
- API key rotation
- IP whitelisting (if vendor requires)

**EDI Security:**
- SFTP with SSH key authentication
- PGP encryption of sensitive data (optional)
- EDI transmission log (sent, received, acknowledged)

## Error Handling

| Scenario | Handling | Recovery |
|----------|----------|----------|
| Vendor API down | Retry 3x; fall back to email | Manual order release if API unavailable |
| Authentication failure | Refresh credentials; retry | Page on-call support if persistent |
| Order transmission timeout | Async transmission; queue for retry | Procurement notified; can manually release |
| Vendor rejection (invalid SKU) | Log error; alert procurement | Procurement contacts vendor; may need product master sync |
| Missing tracking number | Order marked "fulfilling" without tracking | Procurement follows up with vendor |
| Orphaned order (vendor shipped late) | Fulfillment report identifies aging orders | Procurement escalates to vendor |

## Dependencies

**Salesforce:**
- B2B Commerce storefront (Phase 1)
- Order Management module
- Custom Vendor__c object

**External:**
- Vendor API documentation and sandbox access
- Vendor credentials and authentication method
- Vendor webhook endpoint (or polling capability)
- EDI translator (if supporting multiple EDI standards)

**Organizational:**
- Procurement process change (transition from manual to automated)
- Vendor enablement (communication, testing, go-live)
- SLA negotiation (order transmission, fulfillment tracking)

## Implementation Timeline (Phase 2)

| Week | Activity | Deliverable |
|------|----------|-------------|
| 1-2 | Vendor Discovery | Integration methods, API docs, credential setup |
| 3-4 | Salesforce Data Model | Vendor__c object, product-vendor mapping |
| 5-7 | Order Transmission | Apex adapters for EDI/API/email |
| 8-10 | Fulfillment Tracking | Webhook receiver or polling job |
| 11-12 | Testing (with 2-3 pilot vendors) | End-to-end order and tracking |
| 13-14 | User Acceptance Testing | Procurement team tests workflows |
| 15-16 | Vendor Enablement | Train vendors, go-live support |

**Total Effort:** 16 weeks (Phase 2 scope, with vendor onboarding)

## Phased Rollout Strategy

**Wave 1 (Months 1-2):** Pilot with 2-3 vendors
- [[tradewearables|TradeWearables]] (apparel, likely API or EDI)
- 1 drinkware vendor
- 1 regional fulfillment center
- Focus: Validate integration, refine processes

**Wave 2 (Months 3-4):** Expand to 10 vendors
- Most volume vendors
- Similar integration methods
- Parallel run with manual process

**Wave 3 (Months 5-6):** Complete vendor ecosystem (all 20+)
- Smaller vendors (may require email fallback)
- Legacy vendors (may lack API)
- Sunset manual order release

## Open Questions

1. **Vendor API Standardization:** Do vendors support EDI, REST API, or only email/portal?
2. **Tracking Number Format:** Is tracking standardized (UPS, FedEx) or vendor-specific?
3. **Lead Time Accuracy:** Do vendors provide reliable lead time estimates?
4. **Capacity Planning:** Can vendors accept real-time demand (no forecast)?
5. **Order Cancellation:** If user cancels order in Salesforce, can vendor cancel shipment?
6. **Invoice Correlation:** How do we match vendor invoices to orders in Oracle ERP?

## Related Pages

**Integrations:**
- [[oracle-erp-integration|Oracle ERP Integration]] — Invoice matching
- [[tradewearables-api|TradeWearables API Integration]] — Detailed vendor example
- [[sso-authentication|SSO & Dual Authentication]] — Vendor portal access

**Entities:**
- [[boston-beer-company|Boston Beer Company]] — Operator
- [[tradewearables|TradeWearables]] — Sample vendor

## Notes

- This integration is **critical to Phase 2 success** — eliminates manual order release and provides fulfillment visibility
- **Recommend vendor discovery call** early in Phase 2 to understand integration capabilities (API, EDI, email)
- **Parallel run period recommended** (both MerchTank and Salesforce orders) to validate vendor integration before sunset
- Consider **phased rollout** by vendor (start with largest 2-3, expand to all 20+) to manage risk
- **Vendor enablement is significant effort** (communication, testing, go-live support) — allocate 4+ weeks
