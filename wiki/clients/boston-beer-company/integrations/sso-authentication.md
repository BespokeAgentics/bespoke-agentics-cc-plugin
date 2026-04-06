---
type: integration
client: boston-beer-company
status: planned
system-name: sso-authentication
direction: bidirectional
frequency: real-time
auth-method: saml-2.0
created: 2026-04-06
updated: 2026-04-06
sources:
  - "BostonBeerCompany/meetings/02-virtual-warehouse-walkthrough/analysis/integration-assessment-vw-walkthrough.md"
  - "BostonBeerCompany/meetings/03-custom-requests/analysis/integration-assessment-custom-requests-meeting.md"
tags:
  - authentication
  - identity-management
  - azure-ad
  - phase-1
  - planned
---

# Integration: Single Sign-On (SSO) & Dual Authentication

## Overview

Boston Beer Company uses **Microsoft Azure Active Directory (Entra ID)** as the corporate identity provider. All employees (@bostonbeer.com domain) authenticate via Azure AD with SAML 2.0.

This integration connects [[salesforce-b2b-commerce|Salesforce B2B Commerce]] to Azure AD, enabling:

- **Single Sign-On (SSO)** — Users click "Sign In" and are federated through Azure AD (no separate Salesforce password)
- **Automatic User Provisioning** — Azure AD groups map to Salesforce roles (Brand Manager, Procurement, Finance)
- **Seamless Experience** — One corporate identity across all systems (Salesforce, MerchTank, Teams, OneDrive, etc.)
- **Centralized Access Control** — IT can disable user access by removing from Azure AD group

**Business Drivers:**
- Eliminate separate Salesforce password management
- Reduce IT effort on user onboarding/offboarding
- Enforce corporate security policies (MFA, password complexity)
- Audit trail of access (who logged in, when, from where)

**Target Users:**
- All BBC employees (procurement, brand, creative, finance, field sales)
- Estimated 500-2000 users

## Current State (MerchTank)

**Authentication Method:** SAML 2.0 with Azure AD
- Tenant ID: `10b5935c-12ea-4fb2-8b54-004af395bf75`
- User identity confirmed: `shelby.seymour@bostonbeer.com`, `jason.kruk@bostonbeer.com`
- All @bostonbeer.com domain users federated
- Session timeout observed (forces re-auth during workflow; not standard 24-hour timeout)

**Role Mapping:** Azure AD groups → MerchTank roles
- Not visible in MerchTank UI
- Likely managed within MerchTank application logic
- Roles: Admin, Designer, Requestor, Approver (inferred from creative request workflow)

**Known Issues:**
- Session timeout too short (forces mid-workflow re-authentication)
- No fine-grained SAML attribute mapping visible
- Role mapping not transparent (manual setup suspected)

## Target Architecture (Salesforce)

### SAML 2.0 Configuration

**1. Salesforce as Service Provider (SP)**

```
Salesforce Setup → Feature Settings → Authentication Services → SAML Single Sign-On
  |
  1. Download Salesforce Metadata (SAML SP metadata)
  2. Provide metadata to BBC IT / Azure AD administrator
  3. Exchange metadata with Azure AD (SAML IdP metadata)
  4. Configure Assertion Consumer Service URL (ACS)
     - Org ID-based: https://mycompany.my.salesforce.com/services/saml/consumer/myorgid
     - Custom domain: https://bcorp.salesforce.com/services/saml/consumer/
  5. Set up SAML request signing (optional but recommended)
  6. Enable SAML assertion encryption (optional but recommended)
```

**2. Azure AD as Identity Provider (IdP)**

```
Azure Portal → Enterprise Applications → New Application
  1. Create SAML application for Salesforce
  2. Upload Salesforce SP metadata (or enter URLs manually)
  3. Configure SAML claims:
     - Name ID: user.mail (email as unique identifier)
     - email: user.mail
     - firstname: user.givenName
     - lastname: user.surname
     - group: user.memberOf (Azure AD group memberships)
  4. Test SAML login (use test user)
  5. Assign Azure AD users/groups to app
  6. Publish application
```

**3. User Identity Attributes Passed in SAML Assertion**

```xml
<saml:Assertion>
  <saml:Subject>
    <saml:NameID Format="emailAddress">shelby.seymour@bostonbeer.com</saml:NameID>
  </saml:Subject>
  <saml:AttributeStatement>
    <saml:Attribute Name="email" NameFormat="urn:oasis:names:tc:SAML:2.0:attrname-format:basic">
      <saml:AttributeValue>shelby.seymour@bostonbeer.com</saml:AttributeValue>
    </saml:Attribute>
    <saml:Attribute Name="firstname">
      <saml:AttributeValue>Shelby</saml:AttributeValue>
    </saml:Attribute>
    <saml:Attribute Name="lastname">
      <saml:AttributeValue>Seymour</saml:AttributeValue>
    </saml:Attribute>
    <saml:Attribute Name="group">
      <saml:AttributeValue>SalesGroup-Procurement</saml:AttributeValue>
      <saml:AttributeValue>Distribution-MerchandiseTeam</saml:AttributeValue>
    </saml:Attribute>
  </saml:AttributeStatement>
</saml:Assertion>
```

**4. Salesforce User Provisioning (Just-In-Time or Pre-Populated)**

```
Option A: Just-In-Time (JIT) Provisioning
  - User logs in via Azure AD SAML
  - Salesforce checks if user exists (by email)
  - If not found, auto-create Salesforce user with SAML attributes
  - Assign role based on Azure AD group membership
  - Benefit: Zero manual user creation; scales automatically
  - Risk: Default role if group mapping fails

Option B: Pre-Populated Users (SCIM or Manual)
  - BBC IT runs SCIM sync (System for Cross-domain Identity Management)
  - Syncs Azure AD users → Salesforce User objects
  - Update frequency: Real-time or hourly
  - Benefit: Full control; users created before first login
  - Complexity: Requires SCIM setup in Salesforce

Recommended: Hybrid approach
  - Pre-create users via SCIM (for known employees)
  - Enable JIT for contractors, new hires (just-in-time)
```

### Role-Based Access Control

**1. Azure AD Groups**

```
Procurement-Admins
  - Can approve large orders, release to vendors
  - Members: 5-10 procurement leaders

Brand-Managers
  - Can view/edit brand budgets, see order history
  - Members: 20-30 brand managers (Samuel Adams, Twisted Tea, etc.)

Finance-Team
  - Can view financial reconciliation, invoices, budget reports
  - Members: 10-15 finance staff

Creative-Designers
  - Can upload designs, view creative requests
  - Members: 5-10 creative designers

All-Users
  - Can place merchandise orders, view own orders
  - Members: All employees
```

**2. Salesforce Permission Sets (Mapped from Azure AD Groups)**

```
Permission Set: Procurement Admin
  - Can create/edit/delete orders
  - Can release orders to vendors
  - Can view all budgets
  - Read/Write on Vendor__c, Budget__c objects

Permission Set: Brand Manager
  - Can view brand budget
  - Can place orders against brand
  - Read-only on Budget__c (own brand only)

Permission Set: Finance User
  - Can view financial reports
  - Read-only on Order, Invoice, Budget records
  - Can export data for reconciliation

Permission Set: Creative Designer
  - Can view creative requests
  - Can upload design files
  - Can update request status

Permission Set: Standard User (All Employees)
  - Can browse products, add to cart, place orders
  - Can view own order history
  - Standard B2B Commerce user features
```

**3. Salesforce Group Assignment Flow**

```
Azure AD Group Change
  - User added to "Procurement-Admins" group
  |
  v
SCIM Sync (Real-time or Hourly)
  - User.groups updated in Salesforce
  |
  v
Salesforce Flow (Trigger on User Update)
  - Detect group membership change
  - Assign matching Permission Set
  - Log assignment in audit trail
  |
  v
Salesforce User Record Updated
  - Permission Set "Procurement Admin" assigned
  - User can now see vendor management features
```

## Data Flow

### Login Flow

```
1. User navigates to Salesforce B2B Commerce site
2. Clicks "Sign In"
3. Redirected to Azure AD login page
4. User enters Azure AD credentials (email + password)
5. Azure AD validates credentials
   - Optional: Enforce MFA (mobile authenticator, Windows Hello, etc.)
6. User approves Salesforce access (if first time)
7. Azure AD generates SAML assertion (includes user identity, groups)
8. Azure AD redirects back to Salesforce with SAML assertion
9. Salesforce validates SAML signature and assertions
10. Salesforce creates session for user
11. User logged into B2B Commerce site
12. Salesforce creates/updates Salesforce User record (if not exists)
13. Assigns Permission Sets based on Azure AD groups
```

### Session Management

```
Session Duration: 24 hours (standard Salesforce)
Session Timeout: 15-30 minutes of inactivity (configurable)
On Session Timeout:
  - User redirected to SAML login
  - If Azure AD session still active: Auto-login (seamless)
  - If Azure AD session expired: User must re-authenticate

Single Logout (SLO):
  - User clicks "Logout" in Salesforce
  - Salesforce terminates session
  - Redirects to Azure AD logout endpoint (optional)
  - Azure AD terminates session (if configured)
```

## Security Considerations

**SAML Security:**
- **Assertion Signature:** Azure AD signs SAML assertion; Salesforce validates signature
- **Assertion Encryption:** Optional but recommended (encrypt assertion in transit)
- **Certificate Pinning:** Salesforce can pin Azure AD certificate (prevent MITM)
- **Assertion Lifetime:** Keep short (5 minutes) to prevent replay attacks

**Credential Management:**
- **No Passwords Stored in Salesforce:** All authentication delegated to Azure AD
- **Credential Rotation:** Azure AD handles password updates, MFA, etc.
- **Audit Trail:** Azure AD logs all authentication events (available in Azure logs)

**Access Control:**
- **Least Privilege:** Assign minimum Permission Sets per user
- **Group-Based Assignment:** Don't assign individual permissions (use groups)
- **Regular Access Reviews:** Quarterly review of user roles (IT + Finance)
- **Offboarding Automation:** Remove user from Azure AD groups → auto-revoke Salesforce access

## Implementation Timeline (Phase 1)

| Week | Activity | Deliverable |
|------|----------|-------------|
| 1 | Discovery & Planning | SAML requirements doc, Azure AD group list |
| 2 | Salesforce Setup | Download SAML metadata, configure SSO settings |
| 3 | Azure AD Configuration | Create Salesforce app, configure SAML claims |
| 4 | Testing (Dev Environment) | Test SAML login with test users |
| 5 | Permission Set Mapping | Create Permission Sets for each role |
| 6 | SCIM Setup (Optional) | Configure real-time user sync |
| 7 | UAT & Training | User testing, IT documentation |
| 8 | Go-Live | Enable SAML in production Salesforce |

**Total Effort:** 8 weeks (Phase 1, concurrent with core B2B Commerce setup)

## Known Issues & Mitigations

| Issue | Severity | Mitigation |
|-------|----------|-----------|
| Session timeout too short (observed in MerchTank) | Medium | Increase timeout to 30 min inactivity; educate users |
| SAML assertion rejected (clock skew) | Low | Sync system clocks; allow 5-min clock skew tolerance |
| User gets wrong role (group mapping misconfiguration) | Medium | Test extensively in UAT; audit trial of role assignments |
| Cannot login (Azure AD down) | High | Implement backup authentication method (API token); contact Azure support SLA |
| Performance impact (SAML validation overhead) | Low | Negligible; Salesforce optimized for SAML |

## Open Questions

1. **Azure AD MFA Requirement:** Is MFA mandatory for all employees or optional?
2. **Guest Access:** Should external contractors/partners have SSO access?
3. **Conditional Access Policies:** Does Azure AD have IP restrictions (VPN required)?
4. **SLA on Azure AD Uptime:** What's BBC's acceptable downtime? (If Azure AD down, can users still access Salesforce?)
5. **Audit Logging:** What audit logging is required? (Salesforce login history, permission changes)

## Related Pages

**Platforms:**
- [[salesforce-b2b-commerce|Salesforce B2B Commerce]] — Target platform
- [[merchtank|MerchTank]] — Current system (already using SAML SSO)

**Integrations:**
- [[oracle-erp-integration|Oracle ERP Integration]] — May require separate SSO
- [[vendor-fulfillment|Vendor Fulfillment Integration]] — No SSO needed (API-based)

**Entities:**
- [[boston-beer-company|Boston Beer Company]] — Operator of Azure AD

## Notes

- SAML SSO is **Phase 1 priority** (critical for user onboarding and experience)
- Recommend **early coordination with BBC IT** (they own Azure AD and can expedite setup)
- The **session timeout issue in MerchTank is worth investigating** — may indicate incorrect token lifetime configuration
- **Backup authentication method recommended** (API token) in case Azure AD is unavailable
- SCIM user provisioning is **optional** if JIT provisioning is sufficient (recommended: start with JIT, add SCIM later if needed)
