---
type: gap
client: boston-beer-company
status: open
severity: high
category: user-management
related-feature: "[User Onboarding]([[feature|user-onboarding]])"
resolution-approach: custom-dev
created: 2026-04-06
updated: 2026-04-06
sources:
  - "[[meeting|04-fulfillment-demo]] Batch 3: Account Structure, Gap #5"
tags: request-access, approval-workflow, case-management, user-provisioning
---

# Gap: Request Access Flow

## Description

Currently, BBC has no formal "request access" mechanism. Access is granted manually by sales reps who issue a shared "Registration Password" to external users (distributors, wholesalers).

The target state requires a formalized request access flow where unauthenticated users can submit access requests, submit business justification, and route to appropriate approval (likely Procurement or Sales). This applies primarily to external/distributor users; internal users have [[gap|self-registration-with-dual-auth]].

## Current State

**MerchTank Access Model:**
- No formal request access flow
- Sales reps share registration password via email or phone
- No self-service mechanism for external users
- No approval workflow
- No audit trail of who requested access and who approved

## Target State

**Salesforce Request Access Architecture:**
- Custom LWC `c-request-access-form`:
  - Accessible from login page "Not a member?" link
  - Form fields: Name, Email, Company, Department, Requested Role, Business Justification
  - Validation: Required fields, email format, company name lookup
  - Submit creates Case or Lead record

- Case/Lead Routing:
  - New record routes to Procurement or Sales queue based on company/region
  - Auto-assignment logic: Route to account manager if company exists, else to Procurement queue
  - Status: "New" → "Pending Approval" → "Approved" or "Rejected"

- Approval Workflow:
  - Approver receives notification (Chatter, email, or custom dashboard)
  - Approver reviews justification and company affiliation
  - Approver approves/rejects via Case chatter or custom action
  - On approval: Auto-create Salesforce user account with temporary password
  - Send welcome email with credentials and login link

- Request Access Page (Experience Cloud):
  - Unauthenticated page with request form
  - Confirmation message after submission: "Thank you. Your request has been submitted and will be reviewed within [X business days]."

## Gap Analysis

### What Salesforce Lacks

Standard Salesforce Experience Cloud login page has a "Not a member?" link, but it does not provide:
- Custom request form with business justification
- Multi-auth model (internal SSO vs. external local auth)
- Automatic user creation on approval
- Integration with approval workflows
- Company-based routing logic

### Root Cause

This is a specialized flow unique to BBC's multi-tenant external user model. Standard Salesforce assumes a single auth model and does not provide role-based request routing or automated user provisioning on approval.

### Impact

**Without Resolution:**
- No self-service mechanism for external users → Manual, unscalable process remains
- No audit trail → Cannot track who requested access or who approved
- No approval workflow → Informal approval process with delays
- Distributor onboarding bottleneck → New partners face friction

## Resolution Options

### Option 1: Custom Request Form + Case-Based Approval (RECOMMENDED)

**Approach:**
1. Create custom LWC `c-request-access-form`:
   - Fields: Name, Email, Company, Department, Requested Role (picklist), Justification (LongTextArea)
   - Validation: Required fields, email format
   - On submit: Create Case record with request details
2. Case creation logic:
   - Auto-lookup Account by company name
   - If Account found: Set Case Owner to Account Owner (sales rep)
   - If Account not found: Route to Procurement queue
   - Case Status: "New Request"
3. Case notification:
   - Auto-email Case Owner with approval link
   - Provide approve/reject quick action on Case
4. On approval:
   - Flow/Process triggered by Case Status change to "Approved"
   - Auto-create Contact and User records
   - Assign Permission Set based on Requested Role
   - Send welcome email with temporary password
5. On rejection:
   - Send rejection email with reason (from Case Owner comment)

**Effort:** M (Medium) — 2-3 weeks
- Week 1: Request form LWC, Case creation logic
- Week 2: Approval workflow (auto user creation), email templates
- Week 3: Testing, edge case handling

**Advantages:**
- Clear audit trail: Request, approval, and user creation logged
- Scalable: No manual user creation by admin
- Company-based routing: Request goes to correct approver
- Automatic user provisioning: On approval, user is immediately activated

**Risks/Dependencies:**
- Case routing logic: Auto-assignment may route to wrong owner if Account data is stale
- User creation: Must handle errors if password generation fails
- Email delivery: Welcome email must be reliably delivered

**Trade-offs:**
- Requires Case-based workflow (some orgs prefer Approvals)
- User creation automation adds complexity
- Permission Set assignment must be configurable

---

### Option 2: Approval Process + Custom Approval Action

**Approach:**
- Same request form and Case creation
- Use Salesforce Approval Process (not Case Status automation)
- Submit Case to approval process
- Approver uses standard Approval action (Approve/Reject)
- On approval completion: Flow triggered to create user

**Effort:** M (Medium) — 2-3 weeks

**Advantages:**
- Standard Salesforce Approval Process (familiar to some)
- Clear approval tracking in Approval History

**Risks/Dependencies:**
- Approval Process governance: One approval process per Case type (less flexible)
- User creation automation still required
- May not support complex routing (e.g., regional manager for company X)

**Trade-offs:**
- Less flexible routing than Case-based approach
- Approval Process may not align with BBC's approval needs

---

### Option 3: Lead-Based Request (Simpler Alternative)

**Approach:**
- Same request form, but creates Lead instead of Case
- Sales team converts Lead to Account/Contact on approval
- Manual user creation (admin creates after Lead conversion)

**Effort:** S (Small) — 1-2 weeks

**Advantages:**
- Simpler implementation
- Leverages standard Lead management

**Risks/Dependencies:**
- **Manual user creation:** No automation; admin must create user (slower, more error-prone)
- **No formal approval workflow:** Approval is informal (Lead owner decides)
- **Not scalable:** Manual process doesn't scale

**Trade-offs:**
- Not a true solution; keeps manual overhead
- No automated user provisioning

---

## Recommended Approach

**Option 1 (Custom Form + Case-Based Approval)** is recommended because:

1. **Scalability:** Automatic user creation eliminates manual overhead
2. **Audit Trail:** Full record of request, approval, and user creation
3. **Flexibility:** Case routing can be customized per company/region
4. **Self-Service:** Reduces friction for new partner onboarding

## Effort Estimate

**Option 1:** Medium (M)
- Effort: 2-3 weeks (80-120 hours)
- Confidence: High (standard Salesforce patterns; risks are well-known)
- Unknowns: Company lookup accuracy; user creation complexity; email delivery SLA

**Option 2:** Medium (M)
- Effort: 2-3 weeks (80-120 hours)
- Confidence: Medium (Approval Process routing may be inflexible)

**Option 3:** Small (S)
- Effort: 1-2 weeks (40-80 hours)
- Confidence: High (simple implementation)
- Unknowns: None

## Dependencies

### Must Happen Before
- [[decision|External-User-Onboarding-Process]] — Approval workflow must be finalized

### Must Happen Alongside
- [[gap|self-registration-with-dual-auth]] — Internal user registration (different flow)
- [[feature|user-provisioning]] — Auto user creation on approval

### Blocks
- [[feature|storefront-access]] — External users need a way to request access

## Evidence

### Meeting 4: Fulfillment Demo (Batch 3 Analysis)
**Feature #5: Request Access Flow**
- Current State: "No formal request access flow exists — access is granted manually by sales reps who share a registration password."
- Target State: "The Request Access flow provides a mechanism for unauthenticated users to request storefront access...The form creates a Case or Lead record that triggers an approval workflow."
- Decision: NEW BUILD (custom LWC required)
- Challenge: "BBC's multi-auth model (internal SSO + external credentials) and approval requirements exceed standard capabilities. A custom LWC request form with Case-based routing is recommended."

## Open Questions

1. **Approval Authority:** Who approves external user requests? (Account owner/sales rep, Procurement team, specific manager)
   - *Impact if answered wrong:* Case routing logic changes
   - *Owner:* BBC Sales/Procurement

2. **Approval SLA:** Target response time for approval? (Same day, 24 hours, 2 business days)
   - *Impact if answered wrong:* Follow-up/escalation workflow needed
   - *Owner:* BBC IT/Sales

3. **Company Lookup:** Should users select company from dropdown or type it in?
   - *Impact if answered wrong:* Form UX changes; Account lookup logic changes
   - *Owner:* BBC Procurement

4. **Role Options:** What roles can be requested? (Buyer, Approver, Admin, Distributor, Wholesaler)
   - *Impact if answered wrong:* Permission Set assignment logic changes
   - *Owner:* BBC Procurement

## Related Gaps

- [[gap|self-registration-with-dual-auth]] — Internal user registration (different flow, but same landing page)

## Status & Next Steps

**Status:** Open (design phase)

**Next Steps:**
1. Confirm approval authority and SLA with BBC Sales/Procurement
2. Define company lookup approach and available role options
3. Design Case routing logic
4. Build request form LWC
5. Design approval workflow (Case status + Flow automation)
6. Design user creation and welcome email
