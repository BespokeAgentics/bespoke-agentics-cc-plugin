---
type: feature
client: boston-beer-company
status: draft
category: fulfillment
decision: custom
effort: L
priority: P0
created: 2026-04-06
updated: 2026-04-06
sources:
  - /sessions/sweet-trusting-ride/mnt/Vendale-Agentics/BostonBeerCompany/meetings/04-fulfillment-demo/analysis/gap-analysis-boston-beer-company-fulfillment-demo.md
  - /sessions/sweet-trusting-ride/mnt/Vendale-Agentics/BostonBeerCompany/meetings/04-fulfillment-demo/analysis/feature-inventory-boston-beer-company-fulfillment-demo.md
  - client-email-merchtank-feeder-systems-2026-04-06
tags:
  - fulfillment
  - order-management
  - warehouse-operations
  - email
---

# Order Queue and Fulfillment Dashboard

## Description

Fulfillment operators at BBC breweries use a daily order queue to track merchandise orders awaiting fulfillment. The queue displays orders batched from the upstream ordering system, typically arriving after 5:00 PM daily. The operator reviews orders, picks/packs/ships products, and records shipment tracking information. A dedicated fulfillment dashboard replaces a manual Excel spreadsheet that is currently maintained in parallel with MerchTank.

## Current Implementation

**User Workflow (Dogfish Head Milton Brewery):**
1. Operator logs in each morning via Brew Hub
2. Navigates to Fulfillment Queue in MerchTank
3. Manually sets date range and vendor filters, clicks "Search Now"
4. Unprocessed orders appear at top with red status indicator; shipped orders show green
5. No saved views or "open orders only" quick filter
6. Operator manually clicks each order to review address and items
7. Transcribes key information into personal Excel spreadsheet (shadow system)
8. Physically picks/packs products
9. Creates UPS shipping label
10. Returns to MerchTank Shipments tab, selects shipping method, pastes tracking number (in two separate fields), clicks Save/Ship
11. Records tracking number and ship date in Excel spreadsheet
12. Repeats for each order

**Business Rules:**
- Orders filtered by Fulfillment Location (brewery), date range, status
- Three status values: Entered → Open → Shipped
- "Need by" dates buried in free-text Special Instructions field
- Same requestor may have multiple orders to different addresses
- Operator does not mark order as "Shipped" until package is physically sealed
- 18 shipping method options available (FRN, UPS, USPS carriers)
- Tracking number must be entered in both "Tracking #" and "Shipment ID" fields (redundant)

**Current Pain Points:**
1. **Shadow System Dependency (CRITICAL):** Excel spreadsheet maintains full parallel tracking system — 100% data duplication rate
2. **UPS Integration Gap (CRITICAL):** Manual copy-paste of tracking numbers; 3 copy-paste operations per order
3. **Batch Delay (HIGH):** Orders arrive after 5:00 PM; operator (leaves 4:15 PM) doesn't see them until next morning — 16+ hour delay
4. **No Priority Visibility (HIGH):** Need-by dates buried in free text; operator must open each order to assess urgency
5. **Multi-destination Opacity (MEDIUM):** Queue shows requestor name but not ship-to address; requires opening each order to verify destination

**Current Technical Implementation:**
- MerchTank fulfillment queue with date range + vendor filters
- Order detail page shows two-column address layout (ship-from, ship-to)
- Shipments tab with form for carrier selection, tracking number entry
- Status indicators (red/green squares) in list view
- Email notification on status change

**Systems Involved:**
- MerchTank (order queue, detail view, shipment recording), UPS shipping app (manual), Microsoft Excel (shadow system), Brew Hub (intranet portal)
- **Vendor Portals (various)** — Creative Team and Co-ops pull approved order details from MerchTank and enter into vendor portals to process and ship POS materials. Also used to obtain tracking info when requested by sales reps; tracking recorded back in MerchTank for documentation.
- **Outlook** — Used to request quotes from approved vendors (Kirkwood, Six Strings, etc.) for specific MerchTank orders. Quote info entered into MT for sales rep review/approval.

## Target Implementation

Salesforce Order Management provides FulfillmentOrder and Shipment objects, but a complete custom Fulfillment Dashboard LWC is needed to replace the Excel spreadsheet and provide operator-friendly queue management.

**Proposed Salesforce Architecture:**

1. **Custom Objects/Fields:**
   - Add to Order:
     - `Need_By_Date__c` (structured date field, parsed from Special Instructions or entered directly)
     - `Fulfillment_Location__c` (brewery/warehouse location)
     - `Priority__c` (auto-calculated: Expedited < 3 days, Rush 3-7 days, Standard)
   - Use standard Shipment object for tracking information
   - Single `TrackingNumber` field (eliminate redundant Shipment ID)

2. **Custom Fulfillment Dashboard LWC:**
   - **KPI Cards Section:**
     - Open Orders (count)
     - Due Today (count with urgent badge)
     - Overdue (count with red alert)
     - Shipped Today (count)
   - **Queue Section:**
     - Pre-filtered list view: "My Open Orders" sorted by Need By Date
     - Columns: Order#, Requestor, Ship-To City/State, Need By Date, Priority (color-coded), Status
     - Color-coded urgency badges: Red (overdue), Amber (due within 3 days), Green (on-track)
     - Inline actions: View Details, Mark as Shipped
   - **Recent Shipments Section:**
     - Last 10 orders shipped today, with tracking links
   - **Saved Views (pinned):**
     - "Open Orders" (pre-filtered by location + status)
     - "Today's Exports" (pre-filtered by ship date = today)
     - "All Orders" (unrestricted view for admin)

3. **Order Detail Page:**
   - Two-column address layout (ship-from left, ship-to right)
   - Highlighted "Need By Date" field
   - Path component showing status: Entered > Open > Shipped > Closed
   - Line items table with columns: SKU, Description, Qty, Price, Qty Open, Qty Shipped
   - Inline quantity editing for partial fulfillment (edit qty shipped)
   - Related Shipments section

4. **Shipment Entry LWC:**
   - Single "Ship Order" action from Order detail
   - Form captures:
     - Carrier (dependent picklist: Carrier > Service Level)
     - Single TrackingNumber field (not two)
     - Package weight/dimensions (pre-populated from Product2 reference data)
     - Optional Special Handling notes
   - "Ship" button creates Shipment, updates Order status to "Shipped", triggers notification
   - Phase 2: UPS API integration auto-populates tracking number

5. **Automation:**
   - Record-Triggered Flow: When OrderItem is created
     - Parse Special Instructions for "Need by [DATE]" pattern
     - Populate structured Need_By_Date__c field if found
   - Scheduled Flow: Daily at 8:00 AM
     - Recalculates Priority__c for all open orders based on Need_By_Date vs. today
   - Record-Triggered Flow: When Order.Status = "Shipped"
     - Creates Shipment record if not already created
     - Sends notification email with tracking link to requestor
     - Updates FulfillmentOrder status

6. **Formula Fields (for display/sorting):**
   - `Days_Until_Due__c` = Need_By_Date__c - TODAY()
   - `Is_Overdue__c` = Days_Until_Due__c < 0
   - `Ship_To_Summary__c` = ShippingCity & ', ' & ShippingState
   - `Has_Multiple_Open_Orders__c` = COUNTIFS(...) > 1 (for same requestor)

## Gaps & Risks

**Gap OQF-G1: No Fulfillment Dashboard in B2B Commerce**
- Severity: High
- Description: Order Management provides basic order views, not a fulfillment-operator-focused dashboard
- Impact: Without specialized dashboard, operator would recreate Excel spreadsheet
- Resolution: Custom Fulfillment Dashboard LWC as described above
- Effort: L (3-4 weeks for full dashboard + related features)
- Risk: If dashboard doesn't replicate every Excel feature, operator may resist migration

**Gap OQF-G2: Structured Need By Date**
- Severity: High
- Description: Currently buried in free-text Special Instructions; not sortable or reportable
- Impact: Operator loses visibility into priority; cannot see urgent orders at a glance
- Resolution: Custom Need_By_Date__c field with parsing Flow to extract from Special Instructions
- Effort: M (parsing logic, validation)

**Gap OQF-G3: Redundant Shipment ID Field**
- Severity: Medium
- Description: Current system requires tracking number in two fields (Tracking # and Shipment ID) with no business differentiation
- Impact: Duplication creates data entry errors and confusion
- Resolution: Eliminate Shipment ID; use single TrackingNumber field (standard Salesforce)
- Effort: Quick win (S)

**Gap OQF-G4: Multi-Destination Visibility**
- Severity: Medium
- Description: Queue shows requestor name but not ship-to address; operator must open each order for same requestor with multiple destinations
- Impact: Potential for shipping to wrong address; requires manual double-checking
- Resolution: Add Ship_To_Summary__c formula field to queue list view; add "Multiple Destinations" warning badge
- Effort: S

**Gap OQF-G5: Real-Time Order Visibility**
- Severity: Medium
- Description: Upstream batch arrives after 5:00 PM; operator (leaves 4:15 PM) doesn't see orders until next morning — 16+ hour delay
- Impact: Operators can't plan for urgent next-day shipments
- Resolution: Architecture decision: Move to micro-batching (every 30 minutes) or near real-time event-driven intake
- Effort: High (depends on upstream system capabilities)

**Gap OQF-G6: UPS Carrier Integration**
- Severity: High
- Description: Manual copy-paste of tracking numbers from UPS app; no API integration
- Impact: Most time-consuming manual step; error-prone
- Resolution: Phase 1 - Single tracking # field (manual entry). Phase 2 - AppExchange connector (Zenkraft) for auto-population
- Effort: Phase 1 (S), Phase 2 (High)

**Gap OQF-G7: Dual Shipping Notifications**
- Severity: Low
- Description: Both MerchTank and UPS send independent notification emails to requestor
- Impact: Requestor receives duplicate shipping emails
- Resolution: Consolidate into single notification from Salesforce; suppress UPS email if possible
- Effort: S

## Dependencies

- [[order-data-model|Order Data Model]] with custom Need_By_Date__c field
- [[shipment-recording|Shipment Recording]] feature
- [[salesforce-order-management|Salesforce Order Management]] (FulfillmentOrder/Shipment objects)
- UPS API integration (Phase 2)
- Upstream batch system or event integration for near real-time order visibility

## Open Questions

1. Can the upstream batch system be modified to push orders more frequently (every 30 min vs. once daily)?
2. Are there other fulfillment locations (breweries) with different workflows, or is Milton representative?
3. What is the target page size for the fulfillment queue? (Currently shows 4-6 per page)
4. Should fulfillment location be auto-assigned based on operator login, or manually selected?
5. Are there fulfillment SLAs (e.g., all orders must ship within X hours of arrival)?
6. How should "Overdue" be calculated? Based on Need By Date or on days since order arrival?
7. Should the dashboard support filtering by product category or brand?

## Evidence

**Meeting 4 (Fulfillment Demo):**
- "The operator logs into MerchTank via Brew Hub each morning, manually configures date range and fulfillment location filters, and clicks 'Search Now' to view orders that batched overnight."
- "The operator reads the details, notes any 'need by' dates from the Special Instructions free-text field, and manually transcribes key information (order number, name, ship-to, quantities, need-by date) into their personal Excel spreadsheet."
- "Orders are batched upstream and delivered to MerchTank once daily after 5:00 PM. The operator (who leaves at 4:15 PM) does not see new orders until the following morning — a minimum 16-hour delay."
- "The personal Excel spreadsheet maintains a full parallel tracking system because MerchTank lacks a consolidated fulfillment dashboard, priority queuing, multi-destination visibility, and historical timeline views. Every order is entered in both MerchTank and Excel — a 100% data duplication rate."
- "The single highest-value outcome of the migration" is "Eliminating this shadow system"
