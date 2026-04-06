---
type: feature
client: boston-beer-company
status: draft
category: fulfillment
decision: custom
effort: M
priority: P0
created: 2026-04-06
updated: 2026-04-06
sources:
  - /sessions/sweet-trusting-ride/mnt/Vendale-Agentics/BostonBeerCompany/meetings/04-fulfillment-demo/analysis/gap-analysis-boston-beer-company-fulfillment-demo.md
tags:
  - fulfillment
  - shipping
  - order-status
---

# Shipment Recording

## Description

After physically picking and packing merchandise, fulfillment operators record shipment details in MerchTank. This includes selecting the carrier/shipping method from a dropdown of 18 options, entering the UPS tracking number, and saving the shipment. The workflow marks the order as "Shipped" and triggers email notifications to the requestor. Currently, tracking numbers must be entered in two redundant fields (Tracking # and Shipment ID), and there is no UPS API integration — tracking numbers are manually copy-pasted from the UPS application.

## Current Implementation

**User Workflow:**
1. After physical pick/pack, operator generates UPS shipping label
2. Navigates to Order Shipments tab in MerchTank
3. Selects carrier/shipping method from dropdown (18 options: FRN, UPS, USPS)
4. Enters tracking number (copied from UPS app)
5. Enters the same number again in "Shipment ID" field (redundant)
6. Clicks Save/Ship button
7. Order status changes to "Shipped"
8. Email notification sent to requestor with tracking info

**Business Rules:**
- Tracking # and Shipment ID must both be populated (no business differentiation)
- 18 shipping method options: FRN (6), UPS (10), USPS (2)
- Operator only marks as shipped after package is physically sealed and ready for UPS
- Status change triggers automatic notification
- No integration with UPS API; manual copy-paste required

**Current Technical Implementation:**
- Shipment form with carrier dropdown, tracking fields
- Form submission transitions Order status to "Shipped"
- Email notification triggered on status change

**Systems Involved:**
- MerchTank shipment recording, UPS application (manual), email notification system

## Target Implementation

Salesforce Order Management provides Shipment and FulfillmentOrder objects. Shipment recording can be streamlined with a custom LWC, and UPS integration can be added via AppExchange connectors or custom Apex.

**Proposed Salesforce Architecture:**

1. **Shipment Entry LWC: `c-shipment-entry`**
   - Single "Ship Order" action from Order detail page
   - Form fields:
     - Carrier (dependent picklist: FRN/UPS/USPS)
     - Service Level (dependent on carrier selection)
     - Single TrackingNumber field (eliminates Shipment ID redundancy)
     - Package weight/dimensions (optional, pre-populated from Product2 reference data)
     - Special handling notes (optional)
   - "Ship" button creates Shipment record, updates Order status, triggers notification

2. **Shipping Method Configuration:**
   - Custom Metadata Type `Shipping_Method__mdt` OR dependent picklist on Shipment object
   - Carrier values: FRN, UPS, USPS
   - Service levels per carrier:
     - FRN: Any Scenario, Best Day Air, 2nd Day Air, Mega Air, Priority Overnight, Priority Overnight Plus TC
     - UPS: Ground (default), 2nd Day Air, 2 Day Air AM, 3 Day Select, Intl Economy, International, Next Day Air, Next Day Air Early AM, Next Day Air Saver, Worldwide
     - USPS: First Class, Priority

3. **Apex Service: `ShipmentService`**
   - Atomically: Create Shipment, update Order status, trigger notification
   - Uses savepoint for transactional integrity
   - Validates tracking number format (if required)

4. **Automation:**
   - Record-Triggered Flow: When Shipment is created
     - Update Order.Status = "Shipped"
     - Create Activity/Task for order history
   - Record-Triggered Flow: When Order.Status = "Shipped"
     - Send email notification to requestor with tracking link
     - Optional: Update FulfillmentOrder status if Order Management is licensed

5. **UPS Integration (Phase 2):**
   - Phase 1: Manual tracking entry (single field)
   - Phase 2: AppExchange connector (e.g., Zenkraft Multi-Carrier) auto-populates tracking number and generates label

## Gaps & Risks

**Gap SR-G1: Redundant Shipment ID Field**
- Severity: Medium
- Description: System requires tracking number in two fields with no business differentiation
- Impact: Data entry errors, confusion
- Resolution: Eliminate Shipment ID; use single TrackingNumber field
- Effort: S (Quick Win) — Standard Salesforce implementation

**Gap SR-G2: No UPS API Integration**
- Severity: High
- Description: Manual copy-paste of tracking numbers from UPS app; most time-consuming manual step
- Impact: Operator error, inefficiency
- Resolution: Phase 1 - Single field (manual). Phase 2 - AppExchange connector
- Effort: Phase 1 (S), Phase 2 (High)

**Gap SR-G3: Shipping Method Dropdown Options**
- Severity: Low
- Description: 18 carrier/service combinations must be available
- Impact: User must navigate dropdown accurately
- Resolution: Dependent picklist or Custom Metadata Type
- Effort: S

**Gap SR-G4: Package Reference Data**
- Severity: Low
- Description: Weight/dimensions are tribal knowledge, not stored in any system
- Impact: Operator estimates package weight; may affect shipping cost
- Resolution: Add Weight__c and Dimensions__c fields to Product2; Flow auto-populates Shipment
- Effort: M (data enrichment + logic)

**Gap SR-G5: Transactional Integrity**
- Severity: Medium
- Description: If Shipment creation succeeds but notification fails, order is marked shipped but requestor doesn't know
- Impact: Customer service issue
- Resolution: Apex service with savepoint; ensure all operations succeed together
- Effort: Bundled with SR-G1

## Dependencies

- [[order-status-lifecycle|Order Status Lifecycle]] (Shipped status)
- [[salesforce-order-management|Salesforce Order Management]] (Shipment object)
- [[email-notifications|Email Notifications]] framework
- UPS API (Phase 2)

## Open Questions

1. Is tracking number format validated (e.g., length, format)? Or any alphanumeric accepted?
2. Should operator be able to edit shipment after creation?
3. Are there additional shipment fields required beyond carrier/service/tracking?
4. Should the system track package weight/dimensions for shipping cost reconciliation?

## Evidence

**Meeting 4 (Fulfillment Demo):**
- "After physically packing and generating a UPS label, the operator navigates to the Shipments tab. They select a shipping method from a dropdown of 18 carrier/service options (default: UPS Ground), paste the tracking number from the UPS application, enter the same tracking number in a separate 'Shipment ID' field, and click Save/Ship."
- "Tracking number must be entered in both Tracking # and Shipment ID fields (redundant)"
- "Manual copy-paste from UPS app. Operator uncertain about exact button label ('I think there's a save... it may say ship')"
- "Zero Shipping Integration (Critical): There is no API or automated data transfer between MerchTank and the UPS shipping application."
