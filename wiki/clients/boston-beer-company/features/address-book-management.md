---
type: feature
client: boston-beer-company
status: draft
category: account
decision: custom
effort: M
priority: P1
created: 2026-04-06
updated: 2026-04-06
sources:
  - /sessions/sweet-trusting-ride/mnt/Vendale-Agentics/BostonBeerCompany/gap-analysis-batch-3-my-account.md
tags:
  - address-management
  - shipping
  - checkout
---

# Address Book Management

## Description

Buyers manage multiple shipping and billing addresses in MerchTank. Addresses can be saved and reused for rapid checkout, supporting multi-location orders. The system allows quick entry of new shipping addresses but currently causes errors. Critical requirements include: automated quick entry, ability to ship to multiple locations in a single order, and address validation integration.

## Current Implementation

**User Workflow:**
- Users view and manage addresses in "My Account" address book
- Can set default shipping and billing addresses
- Multiple addresses per buyer account
- Address selection during checkout

**Business Rules:**
- Multi-ship support: Single order can go to multiple addresses
- Default address flagging
- Address validation not currently integrated (source of errors)

**Critical Requirements:**
- Req #15: Ability to create and use address books for group orders (multi-ship)
- Req #35: Automated quick entry of new shipping addresses (current system is slow and error-prone)

## Target Implementation

1. **Address Management LWC:**
   - List of all saved addresses with default indicators
   - Add/Edit/Delete address modals
   - Address validation integration (Google Places or SmartyStreets)

2. **Address Validation Service:**
   - Integrated third-party service (e.g., Google Places API, SmartyStreets)
   - Auto-complete and validation on address entry

3. **Multi-Ship Checkout:**
   - Ability to assign different addresses to line items or groups of line items
   - Aggregate shipping calculations per destination

## Gaps & Risks

**Gap AM-G1: Address Validation Integration**
- Severity: High
- Description: Current system causes errors; no validation service integrated
- Impact: Shipping errors, customer service issues
- Resolution: Third-party address validation API
- Effort: M

**Gap AM-G2: Multi-Ship Complexity**
- Severity: Medium
- Description: Requires custom checkout logic to handle multiple destinations
- Impact: Line items must be grouped by address for shipping calculation
- Resolution: Custom checkout step for address allocation
- Effort: L-M

## Dependencies

- [[checkout-apis|Checkout APIs]] (multi-ship integration)
- Third-party address validation service

## Open Questions

1. Which address validation service does BBC prefer?
2. Are there address format restrictions by country/region?
3. Should the system support address aliases (e.g., "Boston Office", "Miami Warehouse")?

## Evidence

**Batch 3 - My Account:**
- "Critical Req #15: Ability to create and use address books for group orders — ability to ship to multiple locations."
- "Critical Req #35: Automated quick entry of new shipping addresses — current system does this but not quickly and causes errors."
