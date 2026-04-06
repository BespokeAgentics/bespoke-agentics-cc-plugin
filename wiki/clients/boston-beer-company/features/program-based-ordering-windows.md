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
  - /sessions/sweet-trusting-ride/mnt/Vendale-Agentics/BostonBeerCompany/meetings/01-merchtank-overview/analysis/gap-analysis-sample-bbc-merchtank.md
  - /sessions/sweet-trusting-ride/mnt/Vendale-Agentics/BostonBeerCompany/meetings/02-virtual-warehouse-walkthrough/analysis/gap-analysis-bbc-vw-walkthrough.md
tags:
  - catalog
  - program-management
  - time-gating
---

# Program-Based Ordering Windows

## Description

MerchTank supports time-bound merchandise ordering campaigns called "programs." Each program has defined start and end dates during which specific products are available for ordering. Outside the program window, users cannot order those items. Programs are separate from the "Everyday" catalog which is always available. This feature enables BBC to control campaign timing, manage seasonal promotions, and coordinate inventory planning around specific marketing initiatives.

## Current Implementation

**User Workflow:**
- Users navigate from the dashboard tile grid which shows "Company Programs" (e.g., EVERYDAY, CUSTOM DESIGN, HOT DEALS, ITEMS FROM SCRATCH, PPE, PROGRAM SAMPLES)
- A yellow alert banner announces when a program order window is open: "Program Order Window is NOW OPEN -- Click here..."
- Clicking navigates to a filtered catalog view for that program
- Products assigned to a program are only browsable during the program's open window
- Outside the window, the program catalog is inaccessible

**Business Rules:**
- Programs have clear start and end dates
- Products belong to exactly one program at a time (or to the Everyday catalog)
- Admin can manage program windows via "Need By Calendar Management" interface
- Alert banner visibility is admin-configurable ("Edit Attention..." link)
- Procurement team uses programs to control pre-orders that sit pending until program items are all received from vendors

**Current Technical Implementation:**
- Program metadata stored in MerchTank database (program name, dates, catalog ID)
- Catalog visibility controlled by date checks on the backend
- Alert banner is a static/configurable HTML element on the dashboard

**Systems Involved:**
- MerchTank catalog management, dashboard, admin settings

## Target Implementation

Salesforce B2B Commerce does not natively support time-gated catalog availability. This feature requires custom Salesforce objects and automation to replicate the current behavior.

**Proposed Salesforce Architecture:**

1. **Custom Metadata Type: `Program_Window__mdt`**
   - Fields: Program_Name, Start_Date, End_Date, Is_Active, Program_Category
   - Serves as configuration source for program windows

2. **Product Assignment:**
   - Add custom field `Program__c` (lookup to custom object or metadata) on Product2
   - Existing category-based assignment maps to Programs and Brands

3. **Entitlement Policy Automation:**
   - Create a Buyer Group entitlement per program
   - Scheduled Flow runs daily (or on-demand) to activate/deactivate entitlements based on window dates
   - Use Entitlement Policy to control product visibility per program

4. **Dashboard Alert Banner:**
   - Custom LWC component pulls active programs from `Program_Window__mdt`
   - Displays alert banner with current/upcoming windows
   - Editable via custom metadata configuration (no code change required)

**User Experience:**
- Same two-step navigation: dashboard tile grid → filtered catalog view
- Products appear/disappear automatically based on window dates
- Alert banner updates automatically

## Gaps & Risks

**Gap PBW-G1: No Native Time-Based Catalog Entitlement**
- Salesforce B2B Commerce entitlements are account/role-based, not date-based
- Resolution: Custom Scheduled Flow to toggle entitlements nightly based on `Program_Window__mdt` dates
- Risk: Flow must run reliably; missed executions could leave a program open/closed incorrectly

**Gap PBW-G2: Assumption Validation**
- Assumption: Programs have non-overlapping, non-null date ranges
- Risk: If programs can overlap or have variable windows, implementation becomes more complex
- Resolution: Validate program window business rules with BBC before design

**Gap PBW-G3: Performance at Scale**
- With many programs and products, entitlement toggling could be slow
- Risk: Nightly Flow processing time increases with scale
- Mitigation: Cache entitlements at the Buyer Group level; consider batch API instead of DML

## Dependencies

- [[product-catalog-and-browse|Product Catalog]] must be defined first
- [[buyer-group-entitlements|Buyer Group Entitlements]] configuration
- Scheduled Flow capability (standard Salesforce)
- Custom Metadata Type support

## Open Questions

1. Can programs overlap in their date ranges, or are they mutually exclusive?
2. Do all users see the same program windows, or can visibility be account-specific?
3. What is the frequency of window updates — static per year or frequently adjusted?
4. Should procurement pre-orders be time-locked until the procurement team manually releases them?

## Evidence

**Meeting 1 (MerchTank Overview):**
- "MerchTank has 'program windows' — time-bound campaigns where items are available for ordering for a few weeks, with fulfillment months later."
- "Procurement team's primary workflow for tent-pole campaigns would not function" without program windows
- Programs observed: EVERYDAY, CUSTOM DESIGN, HOT DEALS, ITEMS FROM SCRATCH, PPE, PROGRAM SAMPLES
- Yellow alert banner: "Program Order Window is NOW OPEN -- Click here..."

**Meeting 2 (Virtual Warehouse Walkthrough):**
- Alert banner configuration: "Edit Attention..." link visible
- "Need By Calendar Management" admin screen controls window dates
