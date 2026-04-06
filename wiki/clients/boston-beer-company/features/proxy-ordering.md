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
  - /sessions/sweet-trusting-ride/mnt/Vendale-Agentics/BostonBeerCompany/meetings/02-virtual-warehouse-walkthrough/analysis/gap-analysis-bbc-vw-walkthrough.md
  - /sessions/sweet-trusting-ride/mnt/Vendale-Agentics/BostonBeerCompany/meetings/03-custom-requests/analysis/gap-analysis-bbc-custom-requests-meeting.md
  - /sessions/sweet-trusting-ride/mnt/Vendale-Agentics/BostonBeerCompany/gap-analysis-batch-3-my-account.md
tags:
  - ordering
  - delegation
  - permissions
---

# Proxy / Delegate Ordering

## Description

MerchTank allows authorized users (typically Procurement staff) to place orders on behalf of other users. When a Procurement user creates an order in proxy mode, the order is attributed to the original user's Virtual Warehouse and budget allocation, not the Procurement user's budget. This is a core workflow for BBC's Procurement team, who routinely place bulk orders for multiple sales reps. The proxy context is visually indicated with a green header banner showing the VW owner's information.

## Current Implementation

**User Workflow:**
1. Procurement user logs into MerchTank
2. Selects a Virtual Warehouse (VW owner) they are authorized to order for
3. Browses products and adds items to cart
4. Cart displays green header: "VW (Sandra Paterson) | Paterson, Sandra"
5. Budget validation checks the selected VW owner's budget, not the logged-in user's budget
6. Checkout attributes the order to the VW owner
7. VW owner receives order confirmation and shipping notifications

**Business Rules:**
- Proxy ordering is role-based: Procurement staff can order for any VW owner
- Order is attributed to VW owner's budget, not to Procurement user
- Procurement user can initiate the full checkout on behalf of VW owner
- Authorization model: unclear if it's "all sales reps" or a specific list per Procurement user

**Current Technical Implementation:**
- Proxy mode triggered by VW selection in Procurement interface
- Session/context variable tracks the "proxy user" (VW owner)
- Budget calculations use proxy user's allocations
- Order creation: Assigned to proxy user, not logged-in user

**Systems Involved:**
- MerchTank user/VW management, order creation logic, budget lookups

## Target Implementation

Salesforce B2B Commerce does not natively support "order on behalf of" for internal users within the same org. This must be built as a custom feature.

**Proposed Salesforce Architecture:**

1. **Custom Proxy Context:**
   - Add fields to WebCart:
     - `Proxy_User__c` (lookup to User) — indicates who the order is actually for
     - `Proxy_Created_By__c` (lookup to User) — audit trail of who created it
     - `VW_Context__c` (lookup to Virtual_Warehouse__c) — the specific VW being ordered from
   - Set these fields when Procurement user selects a VW to order for

2. **VW Selector LWC: `c-vw-proxy-selector`**
   - Displayed prominently on the home page for Procurement/Admin users
   - Dropdown of all VWs they are authorized to order for (or all VWs if admin)
   - Selection updates the current cart context
   - Displays green banner showing selected VW: "VW ([Owner Name]) | [Owner Name]"
   - Can be changed at any time (clears cart if user confirms)

3. **Sharing Rules:**
   - Grant Procurement users read/write access to all VWs and related budget records
   - Implement via Salesforce sharing rules or custom sharing logic

4. **Budget Calculation:**
   - Cart budget validation (from [[shopping-cart-with-budget]]) uses Proxy_User__c if set
   - Otherwise uses current user
   - Budget availability calculated against proxy user's allocation

5. **Order Attribution:**
   - When WebCart is converted to Order, use Proxy_User__c as the order's Account/Owner
   - Order notifications sent to proxy user (VW owner), not to Procurement user

6. **Audit Trail:**
   - Proxy_Created_By__c field provides audit trail
   - Order record shows who actually placed it vs. who it was for

## Gaps & Risks

**Gap PO-G1: No Native "Order On Behalf Of" in B2B Commerce**
- Severity: Critical
- Description: Salesforce B2B Commerce doesn't support proxy ordering for internal users
- Impact: Procurement team cannot perform their core function
- Resolution: Custom proxy context as described above
- Effort: M (2-3 weeks)

**Gap PO-G2: Authorization Model Unclear**
- Severity: High
- Description: Is proxy authorization "all VWs" (admin feature) or "specific VWs per Procurement user"?
- Impact: If per-user, must implement authorization rules
- Resolution: Clarify with BBC; implement Permission Set or custom authorization object if needed
- Effort: M (if per-user authorization required)

**Gap PO-G3: Concurrent Ordering**
- Severity: Medium
- Description: Multiple Procurement users could place orders for same VW simultaneously
- Impact: Could cause race conditions in budget consumption
- Resolution: Pessimistic locking at VW level during order submission, or optimistic conflict detection
- Effort: Bundled with PO-G1

**Gap PO-G4: Proxy Ordering Duration**
- Severity: Low
- Description: Does Procurement user stay in proxy mode for entire session, or must they re-select per order?
- Impact: UX feedback; longer session = more efficient
- Resolution: Maintain proxy context in session until explicitly changed
- Effort: Bundled with PO-G1

## Dependencies

- [[virtual-warehouse-model|Virtual Warehouse Model]] (VW context)
- [[brand-budget-tracking|Brand Budget Tracking]] (proxy user's budget)
- [[shopping-cart-with-budget|Shopping Cart with Budget Enforcement]] (budget validation for proxy)
- [[buyer-account-model|Buyer Account Model]] (user/account hierarchy)
- Salesforce sharing rules or custom authorization

## Open Questions

1. Is proxy ordering "all VWs" (system admin feature) or role-based (Procurement-specific)?
2. If role-based, is each Procurement user authorized for a specific set of VWs, or all VWs?
3. Should out-of-office proxy (delegating approval authority) be handled here, or separately?
4. Are there audit/approval requirements for proxy orders? Or are they treated the same as regular orders?
5. Can Procurement users modify orders after they're placed by VW owner?

## Evidence

**Meeting 2 (Virtual Warehouse Walkthrough):**
- "Procurement staff can order on behalf of other users. The proxy context appears as a green header: 'VW (Sandra Paterson) | Paterson, Sandra'."
- "Orders are attributed to the VW owner's budget."
- "Without proxy ordering, Procurement cannot perform their core function. This is a go-live blocker for the Procurement team."

**Meeting 3 (Batch 3 - My Account):**
- **Critical Req #9**: "Out of Office Proxy — admin access to change approver. This requires the ability for a Buyer Manager to reassign approval authority during absence."
- Proxy ordering is implied as an existing capability that must be preserved

**Critical Requirements Coverage:**
- #9: Out of Office Proxy — related to Buyer Manager role and approval routing
