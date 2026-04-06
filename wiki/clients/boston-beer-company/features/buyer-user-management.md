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
  - user-management
  - permissions
  - authentication
  - email
---

# Buyer User Management

## Description

Salesforce Experience Cloud provides comprehensive user lifecycle management for Buyer Accounts. Users are associated with a Buyer Account and inherit account-level entitlements, pricing, and visibility. User permissions determine access to storefront features such as ordering capabilities, order history, and approval routing. MerchTank has multiple user roles (Sales Reps, Procurement, Brand Teams, Admins, Creative Operations, Finance) but no formal role-to-permission-set mapping or automated provisioning. Migration requires defining role segmentation and establishing user provisioning workflows (manual vs. SSO sync).

## Current Implementation

**MerchTank User Roles:**
- Sales Reps (largest group, primary buyers)
- Procurement (place orders on behalf of reps, manage programs)
- Brand Teams (manage product catalog)
- Creative Operations (design fulfillment)
- Finance (reporting and reconciliation)
- Admin/IT (system administration)

**User Management:**
- Azure AD SSO for @bostonbeer.com internal users
- Registration gated by "shared Registration Password" issued by sales reps
- No formal role segmentation or permission sets
- External/distributor users use custom hashed credentials (SSO extension unknown)
- No automated role assignment or approval workflows

**Business Rules:**
- Users assigned to Virtual Warehouses (VWs) on 1:1 basis (typically)
- Some users have multiple VWs
- Spend limits (coworker approval thresholds) set by company governance, live in **Sam Central** — BBC's legacy coworker database
- Sam Central also contains: organizational hierarchy, sales geography hierarchy, coworker-to-distributor mappings
- **Cost center hierarchy** generated daily by merging org hierarchy + sales geography + coworker-distributor mappings → determines which coworkers have access to which distributors
- Automated manager approval on orders when spend limits exceeded (thresholds looked up directly from Sam Central at order time)

## Target Implementation

**Proposed Salesforce Architecture:**

1. **Role-to-Permission-Set Mapping:**
   - Define 6 Permission Sets (one per role observed)
   - Sales Rep: Standard B2B Commerce buyer permissions, limited approval authority
   - Procurement: Extended permissions (place orders for others), budget management, program management
   - Brand Team: Catalog admin access, product creation/edit, limited ordering
   - Creative Operations: Custom request fulfillment permissions
   - Finance: Read-only access to orders/invoices, reporting access
   - Admin: Full org access

2. **User Provisioning Workflow:**
   - Internal users (@bostonbeer.com): Auto-provision via Azure AD SSO sync or manual
   - External users: Manual provision with password assignment or SSO extension
   - Role assignment: Manual or based on AD group membership

3. **Self-Registration (B2B):**
   - Standard B2B Commerce self-registration flow (if desired)
   - Optionally auto-assign profiles/permission sets based on user type
   - Admin approval before activation

4. **Buyer Group Assignment:**
   - Users inherit Buyer Group membership from their Account
   - Determines product visibility, pricing, approval workflows

5. **Sam Central Integration:**
   - Spend limit data from Sam Central must be accessible for approval threshold enforcement
   - API integration or periodic sync required

## Gaps & Risks

**Gap BUM-G1: No Role-to-Permission-Set Mapping**
- Severity: High
- Description: MerchTank has 6+ user types but no formal role-to-permission mapping
- Impact: Without clear permission sets, users could have incorrect access levels
- Resolution: Define role matrix and create Permission Sets per role
- Effort: M (2-3 weeks)

**Gap BUM-G2: Automated User Provisioning**
- Severity: High
- Description: Currently manual via registration password; no automated sync
- Impact: Slow onboarding, manual overhead
- Resolution: Azure AD SSO sync for internal users; manual for external
- Effort: M (SSO integration dependency)

**Gap BUM-G3: External User Authentication**
- Severity: High
- Description: External/distributor users currently use custom hashed credentials; SSO extension unknown
- Impact: If SSO is not extended to external users, must support dual auth model (SSO + local)
- Resolution: Confirm with BBC IT whether external users will use SSO or local Salesforce credentials
- Effort: M (if local auth required)

**Gap BUM-G4: Sam Central Integration for Spend Limits & Cost Center Hierarchy**
- Severity: High
- Description: Sam Central is BBC's legacy coworker database (per client email 2026-04-06). Contains org hierarchy, sales geography hierarchy, approval thresholds, and distributor mappings. Cost center hierarchy updated daily. Approval thresholds looked up in real-time at order time.
- Impact: Approval workflows AND user-to-distributor access control depend on Sam Central data
- Resolution: Determine Sam Central API availability; implement sync for cost center hierarchy (daily) and real-time callout for approval thresholds
- Effort: M-L (integration dependency — more complex than originally assumed due to dual data needs: hierarchy + thresholds)

**Gap BUM-G5: Role Segmentation Strategy**
- Severity: Medium
- Description: 6+ roles observed but role boundaries not clearly defined
- Impact: Permission set definitions could be incorrect
- Resolution: Clarify role definitions with BBC organizational structure

## Dependencies

- [[buyer-account-model|Buyer Account Model]] (accounts for user assignment)
- [[azure-ad-sso|Azure AD SSO Integration]] (authentication)
- [[sam-central-integration|Sam Central Integration]] (spend limits)
- [[approval-workflows|Approval Workflows]] (role-based approval routing)

## Open Questions

1. Will external/distributor users authenticate via SSO or local Salesforce credentials?
2. Are the 6 roles definitive, or are there additional roles?
3. How should role assignment be triggered? AD group membership? Manual? Account-based?
4. What are the specific permissions for each role? (Need detailed matrix)
5. Are there approval workflows tied to specific roles?
6. How frequently are users added/removed? Is automation critical?

## Evidence

**Batch 3 - My Account:**
- "User roles observed: Sales Reps, Procurement, Brand Teams, Admins, Creative Operations, Finance"
- "Azure AD groups dictate permissions — no Salesforce-native role management observed"
- "Critical Req #22: Automated manager approval on orders placed when spend limits are exceeded. Spend limits are set by company governance and live in Sam Central."
- "Define role-to-permission-set mapping for all 6+ identified user types."
- "Establish user provisioning workflow (manual vs automated via SSO sync)."
