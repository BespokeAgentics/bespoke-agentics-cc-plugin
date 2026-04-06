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
  - client-email-merchtank-feeder-systems-2026-04-06
tags:
  - account-structure
  - buyer-groups
  - account-hierarchy
  - email
---

# Buyer Account Model

## Description

Salesforce B2B Commerce requires a Buyer Account structure to represent purchasing entities on the storefront. MerchTank currently uses a flat model with 95 Virtual Warehouses assigned to individual users, but no formal account hierarchy. Salesforce's buyer account model supports multi-level hierarchies (parent/child relationships), role-based permissions, delegated administrators, and entitlement policies. The migration requires defining a target account hierarchy to replace the flat VW structure.

## Current Implementation

**MerchTank Structure:**
- 95 Virtual Warehouses with 1:1 user assignment
- Each user sees only their allocated inventory and product assortment
- VW bundles buyer identity, product visibility, and available stock
- No formal account hierarchy in MerchTank itself
- No parent/child relationships, no regional grouping in MerchTank
- Proxy ordering allows managers to order on behalf of other users
- **However:** Sam Central maintains a **cost center hierarchy** generated daily by merging organizational hierarchy + sales geography hierarchy + coworker-to-distributor mappings. This hierarchy determines which coworkers have access to which distributors. This is the closest BBC has to an account hierarchy today — it lives outside MerchTank in Sam Central.

**User Roles Observed:**
- Sales Reps (primary users, multiple per org)
- Procurement (manages orders for sales reps)
- Brand Teams (manage product catalog)
- Creative Operations
- Finance
- Admin (IT)

## Target Implementation

**Proposed Salesforce Buyer Account Hierarchy:**

1. **Account Model:**
   - Parent Account: Major distributor or brand entity (e.g., "East Region", "Massachusetts")
   - Child Accounts: Individual sales rep or location-based accounts
   - Each account linked to Buyer Group for entitlements
   - Target: Consolidate 95 VWs into 10-20 manageable Buyer Accounts

2. **Buyer Account Fields:**
   - Account Name, Industry (Beverage), Type (Customer)
   - Billing/Shipping addresses
   - Account Owner (Buyer Manager)
   - Custom fields: VW_Lot_Number__c (cross-reference to legacy VW), Region__c, Cost_Center__c
   - Hierarchy: Parent Account ID

3. **Account Hierarchy Workshop Required:**
   - Determine target structure (regional? by brand? by sales org?)
   - Map 95 VWs to consolidated account structure
   - Identify parent/child relationships
   - Plan migration/consolidation strategy

4. **Buyer Group Entitlements:**
   - Each account assigned to Buyer Group(s)
   - Buyer Groups control:
     - Product catalog visibility (which products this account can see/order)
     - Price books (account-specific pricing)
     - Approval workflows
     - Order templates

## Gaps & Risks

**Gap BAM-G1: Flat VW Structure vs. Hierarchical Accounts**
- Severity: High
- Description: MerchTank has no account hierarchy; Salesforce requires structured hierarchy
- Impact: Consolidation strategy not yet defined; scope unclear
- Resolution: Account hierarchy workshop with BBC
- Effort: M (depends on workshop outcomes)

**Gap BAM-G2: Multi-Level vs. Single-Level**
- Severity: Medium
- Description: Should accounts support 2+ levels of hierarchy, or stay flat?
- Impact: Multi-level enables regional/divisional structures but adds complexity
- Resolution: Confirm target structure with BBC stakeholders

**Gap BAM-G3: VW-to-Account Mapping**
- Severity: High
- Description: How should 95 VWs map to new Buyer Accounts? 1:1, many:1, or mixed?
- Impact: Consolidation strategy affects implementation effort and user adoption
- Resolution: Define mapping during account hierarchy workshop

**Gap BAM-G4: Proxy Ordering Scope**
- Severity: Medium
- Description: Proxy ordering may need to function differently in hierarchical structure
- Impact: Parent account proxy to child account, or sibling proxy?
- Resolution: Clarify proxy authorization model in hierarchical context

## Dependencies

- [[proxy-ordering|Proxy Ordering]] (authorization in hierarchical context)
- [[buyer-group-entitlements|Buyer Group Entitlements]] (product visibility)
- Account hierarchy workshop with BBC

## Open Questions

1. What is the target account hierarchy? Regional? By brand? By organization?
2. Should accounts support 2+ levels of hierarchy?
3. How should 95 VWs be consolidated? What is the mapping strategy?
4. Are there any accounts that should NOT be consolidated?
5. What is the timeline for account hierarchy definition?

## Evidence

**Batch 3 - My Account:**
- "MerchTank uses 95 Virtual Warehouses (VWs) with 1:1 user assignment — each user sees only their allocated inventory and product assortment."
- "No formal account hierarchy exists — no parent/child relationships, no regional grouping, no cost center alignment."
- "Critical Req #33: Make POS available to an exclusive group or list of coworkers."
- "Critical Req #34: Supplier setup (source and fulfillment)."
- Recommended Next Step: "Define target account hierarchy model (Parent/Child) to replace flat VW structure. Conduct account hierarchy workshop — determine consolidation strategy for 95 VWs into manageable Buyer Account structure."
