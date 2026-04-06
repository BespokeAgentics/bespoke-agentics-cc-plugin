---
type: gap
client: boston-beer-company
status: open
severity: medium
category: user-management
related-feature: "[User Onboarding]([[feature|user-onboarding]])"
resolution-approach: custom-dev
created: 2026-04-06
updated: 2026-04-06
sources:
  - "[[meeting|04-fulfillment-demo]] Batch 3: Account Structure, Gap #4"
tags: self-registration, sso, azure-ad, dual-auth, user-provisioning
---

# Gap: Self-Registration with Dual Auth (SSO + Local)

## Description

BBC requires user registration that supports two authentication models:
1. **Internal Users (BBC employees):** Azure AD SSO (confirmed in Batch 1 decision)
2. **External Users (distributors, wholesalers):** Local Salesforce credentials (custom hash-based in current MerchTank)

Salesforce B2B Commerce self-registration supports auto-assignment of Profiles and Permission Sets, but the dual-auth model (SSO for internal, local for external) requires custom design. Currently, external users use a shared "Registration Password" issued by sales reps — no self-service mechanism exists.

## Current State

**MerchTank User Registration:**
- Internal users (@bostonbeer.com): Azure AD SSO authenticated
- External/distributor users: Custom hashed credentials (no SSO support)
- Registration is manual: Sales reps issue shared registration password to distributors
- No self-service registration flow for external users
- No formal onboarding workflow

**Critical Business Requirements:**
- [[meeting|04-fulfillment-demo]] Critical Req #33: "POS available to an exclusive group or list of coworkers"
- [[meeting|04-fulfillment-demo]] Critical Req #34: "Supplier setup (source and fulfillment)"

## Target State

**Salesforce Dual Auth Self-Registration:**
- **Path 1: Internal User (Azure AD):**
  1. User navigates to storefront login page
  2. Clicks "Not a member? Request Access"
  3. Lands on custom request form
  4. Form captures: Name, Email (@bostonbeer.com), Department, Manager (optional)
  5. System auto-verifies email against Azure AD
  6. If verified, creates user record and auto-assigns Profile/Permission Set (Buyer User)
  7. User is auto-activated (no admin approval needed for verified internal users)
  8. User logs in with Azure AD credentials

- **Path 2: External User (Local Auth):**
  1. User (distributor/wholesaler) navigates to login page
  2. Clicks "Not a member? Request Access"
  3. Lands on custom request form (different flow or conditional UI)
  4. Form captures: Name, Email, Company, Requested Role, Business Justification
  5. System creates Case or Lead record for admin review
  6. Admin (Procurement/Sales) approves/rejects request
  7. On approval, admin creates local Salesforce user with temporary password
  8. User receives email with credentials and password reset link
  9. User logs in with Salesforce credentials

**Custom LWC `c-self-registration-form`:**
- Conditional logic: Show different form fields based on user email domain
- If @bostonbeer.com: Auto-verify against Azure AD; auto-activate
- If external: Route to approval workflow
- Integration with Azure AD API for email verification
- Case/Lead creation for external user approval

**Permission Set Assignment:**
- Internal users: Default "Buyer User" profile (configurable)
- External users: Role-based assignment on approval (e.g., "Distributor" role, "Wholesaler" role)

**Integration with [[gap|request-access-flow]]:**
- This gap focuses on self-registration form design
- [[gap|request-access-flow]] focuses on the approval workflow and case routing

## Gap Analysis

### What Salesforce Lacks

Standard Salesforce B2B Commerce self-registration does not support:
- Conditional authentication (SSO vs. local) based on user identity
- Azure AD email verification
- Multi-path registration (different flows for internal vs. external)
- Automatic user activation for SSO users
- Custom approval workflows for local auth users

### Root Cause

B2B Commerce self-registration is designed for a single authentication model (usually SSO for all users). BBC's dual-auth model (internal SSO + external local) is a hybrid requiring custom logic to route users to the correct authentication path.

### Impact

**Without Resolution:**
- External users cannot self-register → Manual process remains bottleneck
- No distinction between internal and external auth → Users confused about login method
- External users see the same form as internal → Bad UX
- Approval workflow for external users is unclear

## Resolution Options

### Option 1: Custom Dual-Path Registration Form + Azure AD Integration (RECOMMENDED)

**Approach:**
1. Build custom LWC `c-self-registration-form`:
   - Initial field: Email (required)
   - On email blur: Check domain
     - If @bostonbeer.com: Show internal registration path
     - If external: Show external registration path
   - Internal path fields: Name, Department, Manager lookup
   - External path fields: Name, Company, Role, Justification
2. Integrate with Azure AD API:
   - Custom Apex callout to verify @bostonbeer.com email exists in Azure AD
   - If verified, auto-create Contact/User with Profile = Buyer User
   - If not verified, display error and suggest contacting admin
3. For external users:
   - Create Case record for approval routing
   - Auto-assign to Procurement/Sales team based on company/region
   - Include justification in Case notes
4. Approval workflow (handled separately in [[gap|request-access-flow]]):
   - Admin receives Case notification
   - Admin approves/rejects via Case chatter or custom action
   - On approval, auto-create local Salesforce user with temp password
   - Send welcome email with login link

**Effort:** M-L (Medium-Large) — 3-4 weeks
- Week 1: LWC dual-path form design, email validation
- Week 2: Azure AD API integration, internal path user creation
- Week 3: External path Case creation, approval workflow integration
- Week 4: Testing, error handling, documentation

**Advantages:**
- Seamless UX: Form adapts based on user identity
- Internal users auto-activated: No admin overhead
- External users go through approval: Control and visibility
- Scalable: Separate paths for different user types

**Risks/Dependencies:**
- Azure AD API: Requires valid credentials and API access (confirm with BBC IT)
- Email verification: If Azure AD is unavailable, internal user registration fails
- Case routing: Auto-assignment must be reliable
- Data quality: External company/role data may be incomplete; requires validation

**Trade-offs:**
- Depends on Azure AD API availability and performance
- Requires Case/approval workflow integration (separate gap)
- More complex UX (conditional logic)

---

### Option 2: Simplified: Single Form + Manual Internal User Creation

**Approach:**
- Single self-registration form for all users (no conditional logic)
- Users submit request regardless of internal/external
- All requests go to Case/approval workflow
- Admin manually approves and:
  - For internal users: Creates Salesforce user with SSO profile (sync with Azure AD)
  - For external users: Creates Salesforce user with local credentials
- No Azure AD integration; manual email verification by admin

**Effort:** M (Medium) — 2-3 weeks
- Week 1: Simple registration form
- Week 2-3: Case creation and approval workflow

**Advantages:**
- Simpler implementation (no Azure AD API)
- All users go through approval (more control)
- No dependency on Azure AD API availability

**Risks/Dependencies:**
- **All users require admin approval:** Slows internal user onboarding (every internal user waits for approval)
- No auto-activation: Internal users don't get immediate access
- Higher admin overhead: Every user creation is manual

**Trade-offs:**
- Defeats self-service for internal users
- Not scalable if many internal users need onboarding
- Slower user activation

---

### Option 3: Use Standard Salesforce B2B Self-Registration + Manual External User Setup

**Approach:**
- Use standard Salesforce Experience Cloud self-registration for internal users (SSO-only)
- External users request access via email to sales rep
- Sales rep manually creates external users in Salesforce admin console

**Effort:** S (Small) — 1-2 weeks (configuration only)

**Advantages:**
- Minimal custom development
- Leverages standard Salesforce features

**Risks/Dependencies:**
- **No self-service for external users:** Keeps manual process in place
- **No distinction in UI:** Users don't know which path to take
- **Poor UX for external users:** Directed to email or phone, not a self-service form
- **Not scalable:** Manual process doesn't scale with growing distributor base

**Trade-offs:**
- Doesn't solve the external user self-registration problem
- Not a true solution; only handles internal users

---

## Recommended Approach

**Option 1 (Dual-Path Registration + Azure AD)** is recommended because:

1. **Self-Service:** Both internal and external users have self-service paths
2. **Efficiency:** Internal users auto-activated; no admin approval needed
3. **Control:** External users go through approval workflow for security
4. **UX:** Form adapts to user identity; clear guidance on next steps
5. **Scalability:** Supports growing user base (internal and external)

**Option 2** is a fallback if BBC wants all users to go through approval (more control, but slower)

## Effort Estimate

**Option 1:** Medium-Large (M-L)
- Effort: 3-4 weeks (120-160 hours)
- Confidence: Medium (Azure AD API integration is the main risk)
- Unknowns: Azure AD API availability; email verification performance; Case auto-assignment logic

**Option 2:** Medium (M)
- Effort: 2-3 weeks (80-120 hours)
- Confidence: High (straightforward form + approval workflow)
- Unknowns: Approval workflow SLA requirements

**Option 3:** Small (S)
- Effort: 1-2 weeks (40-80 hours)
- Confidence: High (configuration only)
- Unknowns: None

## Dependencies

### Must Happen Before
- [[decision|User-Authentication-Architecture]] — Dual auth model must be finalized (SSO for internal, local for external)
- [[decision|Buyer-User-Profiles-and-Roles]] — Permission Sets must be defined for auto-assignment

### Must Happen Alongside
- [[gap|request-access-flow]] — Approval workflow for external user requests
- [[feature|user-provisioning]] — User creation must integrate with registration

### Blocks
- [[feature|storefront-access]] — Users cannot access storefront without successful registration

## Evidence

### Meeting 4: Fulfillment Demo (Batch 3 Analysis)
**Feature #4: Self-Registration (B2B)**
- Current State: "Registration is gated by a shared 'Registration Password' issued by BBC sales reps — no self-service registration exists"
- Target State: "Salesforce B2B Commerce supports self-registration flows that allow prospective buyers to request access to the storefront. The flow collects user details, validates against business rules, and routes for admin approval before granting access."
- Decision: CUSTOM (requires custom LWC for dual-auth model)
- Critical Req #33: "POS available to an exclusive group or list of coworkers"
- Critical Req #34: "Supplier setup (source and fulfillment)"

## Validation Notes

SFCC Validation Report confirms:
- "Standard B2B Commerce self-registration supports custom fields and approval workflows"
- "Azure AD SSO integration is standard and reliable"
- "Custom form for conditional auth paths is feasible with LWC"

## Open Questions

1. **Azure AD API Access:** Does BBC IT have Azure AD Graph API access available for email verification?
   - *Impact if answered wrong:* Azure AD integration may not be possible; fallback to manual verification
   - *Owner:* BBC IT

2. **External User Approval Workflow:** What is the approval process? Who approves (Procurement, Sales, specific manager)?
   - *Impact if answered wrong:* Case routing and approver assignment logic changes
   - *Owner:* BBC Procurement/Sales

3. **External User Types:** Are there multiple types of external users (distributors, wholesalers, agencies)? Do they need different roles?
   - *Impact if answered wrong:* Permission Set assignment logic becomes more complex
   - *Owner:* BBC Procurement

4. **User Onboarding SLA:** What is the target activation time? (Same day, 24 hours, next business day)
   - *Impact if answered wrong:* Approval workflow SLA and automation requirements change
   - *Owner:* BBC IT/HR

## Related Gaps

- [[gap|request-access-flow]] — Formal request process for external users
- [[gap|buyer-user-management]] — Role and permission set management post-registration

## Status & Next Steps

**Status:** Open (design phase)

**Next Steps:**
1. Confirm Azure AD API availability with BBC IT
2. Confirm external user approval workflow (who, what SLA)
3. Define external user types and required roles
4. Finalize dual-path form design
5. Begin LWC implementation
6. Design Case routing for external user approval
