---
type: index
title: Boston Beer Company — Gap Analysis Index
client: boston-beer-company
status: published
created: 2026-04-06
---

# Boston Beer Company — Gap Analysis Index

This index catalogs all identified gaps between MerchTank and Salesforce B2B Commerce as documented across four discovery meetings (Dec 2025 - Mar 2026).

## Gap Summary

**Total Gaps Identified:** 13 distinct gaps across 5 gap analysis documents
**Critical Gaps:** 4 (budget engine, virtual warehouse, custom POS, co-op billing)
**High-Severity Gaps:** 5
**Medium-Severity Gaps:** 4

---

## Critical Gaps (Severity: Critical)

These gaps are **blockers** for core business functions and must be resolved in Phase 1.

### 1. Budget Management Engine
**File:** `budget-management-engine.md`
**Source:** Meetings 1, 3, 4 | Gap ID: W2-G1, W2-G2
**Impact:** Core to every order; no budget validation or spending visibility
**Resolution Approach:** Custom budget object suite (`Budget__c`, `BudgetAllocation__c`, `BudgetTransaction__c`) with Apex triggers and LWC dashboard
**Effort:** L (3-4 weeks)
**Status:** Open (design phase)
**Decision Pending:**
- Budget rules complexity (annual only or more complex)
- Budget amount at order vs. shipment
- Co-op split impact on budget

**Related Gaps:**
- [[gap|co-op-billing]] — Co-op amounts must respect budget
- [[gap|checkout-flow-budget-validation]] — Budget enforced at checkout

---

### 2. Virtual Warehouse Inventory Model
**File:** `virtual-warehouse-inventory-model.md`
**Source:** Meeting 2 | Gap ID: VW-G1
**Impact:** Architectural foundation; without this, ordering, budgeting, proxy workflows fail
**Resolution Approach:** Custom `Virtual_Warehouse__c` + `VW_Inventory_Instance__c` objects with Apex trigger for 1:1 constraint, LWC management console, audit trail
**Effort:** XL (5-6 weeks)
**Status:** Open (design phase)
**Decision Pending:**
- VW archive/deactivation lifecycle
- Multi-VW ordering support
- Packout unit variation by product

**Related Gaps:**
- [[gap|virtual-warehouse-inventory-transfers]] — Transfer workflow depends on VW model
- [[gap|proxy-delegate-ordering]] — Proxy ordering requires VW ownership context
- [[gap|budget-management-engine]] — Budget per VW/user

---

### 3. Custom Item Design and Proofing Workflow
**File:** `custom-item-design-and-proofing.md`
**Source:** Meeting 1, 3 | Gap ID: W3-G1, W3-G2
**Impact:** Core value proposition; custom POS workflow unavailable without this
**Resolution Approach:** Custom `CustomizationRequest__c` object, multi-step LWC form with file uploads, Apex date calculation service, Approval Process, status dashboard
**Effort:** XL (4-6 weeks)
**Status:** Open (design phase)
**Decision Pending:**
- Feasibility calculation rules (simple or complex)
- Designer assignment logic
- Design request number format
- Design history migration scope

**Related Gaps:**
- [[gap|need-by-date-feasibility-calculation]] — Part of customization workflow
- [[gap|proof-approval-override]] — Bypass approval with confirmation

---

### 4. Co-op Billing / Cost Sharing with Wholesaler
**File:** `co-op-billing.md`
**Source:** Meeting 1, 3, 4 | Gap ID: W4-G1, W4-G3, W4-G23
**Impact:** Financial impact; co-op is significant part of distributor relationships
**Resolution Approach:** Custom `CoopAgreement__c` + `OrderCoopAllocation__c` objects, checkout extension, Rootstock integration for invoicing, Finance reporting LWC
**Effort:** L (3-4 weeks)
**Status:** Open (design phase)
**Decision Pending:**
- Budget impact (full amount vs. BBC portion)
- CoopAgreement count and stability
- Wholesaler invoicing workflow
- Approval required for co-op orders

**Related Gaps:**
- [[gap|budget-management-engine]] — Co-op amounts affect budget
- [[gap|invoice-access-and-sync]] — Separate invoices for BBC and wholesaler

---

## High-Severity Gaps (Severity: High)

These gaps affect core workflows but are not immediate blockers if Phase 1 MVP excludes the workflow.

### 5. Program Window Time-Gating
**File:** `program-window-time-gating.md`
**Source:** Meeting 1, 2, 3 | Gap ID: W1-G1, W2-G4
**Impact:** Procurement's primary workflow for tent-pole campaigns
**Resolution Approach:** Custom Metadata Type `Program_Window__mdt`, Scheduled Flow for daily activation/deactivation, CMS Content blocks, admin Lightning page
**Effort:** M (2-3 weeks)
**Status:** Open (design phase)
**Decision Pending:**
- Program frequency and count
- Pre-order window requirements
- Overlapping programs support
- Program-specific budgets

**Related Gaps:**
- [[gap|budget-management-engine]] — Budget may be program-specific
- [[gap|procurement-controlled-order-release]] — Pre-order release tied to program dates

---

### 6. Proxy / Delegate Ordering
**File:** `proxy-delegate-ordering.md`
**Source:** Meeting 3, 4 | Gap ID: W2-G3
**Impact:** Procurement team cannot execute core function without this
**Resolution Approach:** Custom `OrderingContext__c` + `ApprovalDelegation__c` objects, Proxy Console LWC, Approval Process with context-aware routing
**Effort:** M (2-3 weeks)
**Status:** Open (design phase)
**Decision Pending:**
- Proxy authorization model (which users can proxy)
- Proxy scope (any rep or specific mappings)
- Temporary vs. permanent delegations

**Related Gaps:**
- [[gap|virtual-warehouse-inventory-model]] — Proxy ordering depends on VW
- [[gap|budget-management-engine]] — Proxy must consume from Acting_As_User budget

---

### 7. Procurement-Controlled Order Release
**File:** `procurement-controlled-order-release.md`
**Source:** Meeting 1 | Gap ID: W5-G1
**Impact:** Program pre-order workflow; orders stuck if not released
**Resolution Approach:** Custom `OrderReleaseBatch__c` + `OrderReleaseMap__c` objects, Release Console LWC with bulk actions, Flow-based bulk status update, vendor notification
**Effort:** M (2-3 weeks)
**Status:** Open (design phase)
**Decision Pending:**
- Release frequency and batch size
- Release criteria (inventory confirmation, date-based, etc.)
- Approval required

**Related Gaps:**
- [[gap|program-window-time-gating]] — Program windows create pre-order periods
- [[gap|batch-order-upload]] — Bulk processing may accompany release

---

### 8. Virtual Warehouse Inventory Transfers
**File:** `virtual-warehouse-inventory-transfers.md`
**Source:** Meeting 2 | Gap ID: VW-TR-G1, VW-TR-G2
**Impact:** Procurement cannot rebalance inventory across users
**Resolution Approach:** Custom `VW_Transfer__c` + `VW_Transfer_Line__c` objects, single-page LWC state machine, Apex Service with pessimistic locking, audit trail
**Effort:** L (3-4 weeks)
**Status:** Open (design phase, dependent on VW model)
**Decision Pending:**
- Transfer frequency and typical size
- Approval required for transfers
- Archive strategy for old transfers

**Related Gaps:**
- [[gap|virtual-warehouse-inventory-model]] — Transfers depend on VW objects

---

## Medium-Severity Gaps (Severity: Medium)

These gaps affect important workflows but can be deferred to Phase 2 or have workarounds.

### 9. Self-Registration with Dual Auth (SSO + Local)
**File:** `self-registration-with-dual-auth.md`
**Source:** Meeting 4 (Batch 3) | Feature #4
**Impact:** User onboarding; external users stuck with manual registration password
**Resolution Approach:** Custom dual-path registration form, Azure AD API integration for internal users, Case creation for external users, auto user creation on approval
**Effort:** M-L (3-4 weeks)
**Status:** Open (design phase)
**Decision Pending:**
- Azure AD API availability
- External user approval workflow
- External user types and roles
- Onboarding SLA

**Related Gaps:**
- [[gap|request-access-flow]] — Formal request process for external users
- [[gap|buyer-user-management]] — Role and permission set assignment

---

### 10. Request Access Flow
**File:** `request-access-flow.md`
**Source:** Meeting 4 (Batch 3) | Feature #5
**Impact:** External user onboarding; no self-service mechanism
**Resolution Approach:** Custom request form LWC, Case-based approval routing, auto user creation on approval, welcome email
**Effort:** M (2-3 weeks)
**Status:** Open (design phase)
**Decision Pending:**
- Approval authority (sales rep, Procurement, etc.)
- Approval SLA
- Company lookup approach
- Role options

**Related Gaps:**
- [[gap|self-registration-with-dual-auth]] — Different flow for internal vs. external

---

### 11. Brand-Based Navigation with Wholesaler Context
**File:** Not yet created (low priority, mentioned in template)
**Source:** Meeting 1 | Gap ID: W1-G2
**Impact:** Sales reps managing multiple wholesalers need context switching
**Resolution Approach:** Custom LWC account switcher or landing page (low complexity)
**Effort:** S-M (1-2 weeks)
**Status:** Pending

---

### 12. Need-By Date Feasibility Calculation
**File:** Not yet created (part of custom POS workflow)
**Source:** Meeting 1 | Gap ID: W3-G2
**Impact:** Users may request unrealistic delivery dates
**Resolution Approach:** Apex service class with date calculation logic, integrated with customization form
**Effort:** S (small, bundled with customization form)
**Status:** Pending (part of Gap #3)

---

### 13. Automated Report Generation and Migration
**File:** Not yet created (low priority)
**Source:** Meeting 1 | Gap ID: W7-G1
**Impact:** Procurement relies on automated Excel exports
**Resolution Approach:** Salesforce scheduled reports with CSV/Excel export, custom report types for commerce data
**Effort:** M (2-3 weeks)
**Status:** Pending

---

## Low-Severity Gaps (Severity: Low)

These gaps affect minor workflows or have easy workarounds.

- **Manager Notification Option** (W4-G3): Low effort, standard Flow email action
- **Order Duplication** (W5-G2): Low effort, custom LWC button on order detail
- **Address Validation Integration** (W6-G2): Low effort, third-party service or Data.com
- **External Vendor Integration Depth** (W8-G1): Low effort, replicate as navigation links
- **Bar Chart Visualization on Dashboard** (W1-G4): Low effort, Chart.js in LWC
- **Proof Approval Override** (W1-G3): Low effort, custom action with confirmation

---

## Gap Resolution Timeline

### Phase 1: Foundation + Core Commerce (Weeks 1-10)
**Must-Have Gaps:**
- [[gap|virtual-warehouse-inventory-model]] (VW setup)
- [[gap|budget-management-engine]] (budget objects and checkout integration)
- [[gap|co-op-billing]] (co-op configuration and checkout extension)
- [[gap|program-window-time-gating]] (metadata and scheduled flows)
- [[gap|proxy-delegate-ordering]] (ordering context)
- [[gap|self-registration-with-dual-auth]] (internal user registration)

**Expected Effort:** 20-24 weeks of concurrent development

### Phase 2: Advanced Features (Weeks 10-18)
**Should-Have Gaps:**
- [[gap|custom-item-design-and-proofing]] (custom POS workflow)
- [[gap|virtual-warehouse-inventory-transfers]] (rebalancing)
- [[gap|procurement-controlled-order-release]] (batch release)
- [[gap|request-access-flow]] (external user onboarding)
- [[gap|automated-report-generation]] (reporting)

**Expected Effort:** 14-16 weeks of concurrent development

### Phase 3: Polish and Optimization
**Nice-to-Have Gaps:**
- Low-severity gaps (manager notification, order duplication, address validation, etc.)

---

## Decision Matrix

| Gap | Critical? | Phase | Effort | Risk | Dependency |
|-----|-----------|-------|--------|------|------------|
| Budget Engine | Yes | 1 | L | M | Co-op, Checkout |
| Virtual Warehouse | Yes | 1 | XL | M | Proxy, Transfer, Budget |
| Custom POS Design | Yes | 1/2 | XL | M | None |
| Co-op Billing | Yes | 1 | L | M | Budget |
| Program Windows | Yes | 1 | M | L | Budget |
| Proxy Ordering | Yes | 1 | M | M | VW, Budget |
| Order Release | Yes | 1 | M | L | Program Windows |
| VW Transfers | Yes | 1/2 | L | M | VW |
| Self-Registration | High | 1 | M-L | M | None |
| Request Access | High | 1 | M | L | None |
| Reporting | Medium | 2 | M | L | None |
| Other | Low | 2/3 | S | L | None |

---

## Cross-Gap Dependencies

### Foundation (VW + Budget) → All Features

```
Virtual Warehouse Model (VW-G1)
├── VW Transfers (VW-TR-G1)
├── Proxy Ordering (W2-G3) → Budget (W2-G1)
└── Budget Management (W2-G1)
    ├── Co-op Billing (W4-G1)
    ├── Program Windows (W1-G1)
    └── Order Release (W5-G1)
```

### Ordering & Checkout → Financial

```
Order Management
├── Budget Validation (W4-G2)
├── Co-op Split (W4-G1) → Invoicing
└── Program Window Check (W2-G4)
```

### User Management → Operational

```
Self-Registration (Batch 3, #4)
├── Request Access (Batch 3, #5)
└── Proxy Ordering (W2-G3)
    └── Approval Delegation (Req #9)
```

---

## Known Unknowns

### High-Impact Unknowns (Must Answer)

1. **Budget Rules:** Are rules annual-only, or more complex (quarterly, regional)?
   - Owner: BBC Finance
   - Impact: Budget object schema design

2. **VW Archive Strategy:** How are VWs handled when users leave?
   - Owner: BBC Procurement/IT
   - Impact: VW lifecycle design

3. **Design Request Complexity:** Are feasibility calculations simple (fixed dates) or complex (capacity-based)?
   - Owner: BBC Creative Ops
   - Impact: Custom POS effort +1 week if complex

4. **Co-op Budget Impact:** Full amount or BBC-only portion affects budget?
   - Owner: BBC Finance
   - Impact: Budget and co-op integration design

5. **Azure AD API Availability:** Can BBC IT provide AD Graph API access?
   - Owner: BBC IT
   - Impact: Self-registration design (fallback if not available)

### Medium-Impact Unknowns (Should Know)

- Program frequency and overlapping rules
- Transfer frequency and typical size
- Order release approval required
- External user types and roles
- Approval authority for external user requests

---

## Estimation Summary

| Phase | Critical Gaps | High Gaps | Effort | Risk | Timeline |
|-------|---------------|-----------|--------|------|----------|
| Phase 1 | 4-5 | 2-3 | 20-24 weeks | Medium | 10-12 weeks (concurrent) |
| Phase 2 | 1 | 3-4 | 14-16 weeks | Medium | 8-10 weeks (concurrent) |
| Phase 3 | 0 | 0 | 3-5 weeks | Low | 2-3 weeks |
| **Total** | **5** | **5-7** | **37-45 weeks** | **Medium** | **20-25 weeks (concurrent)** |

---

## Status Dashboard

| Gap | Status | Owner | Next Step | Target Date |
|-----|--------|-------|-----------|-------------|
| [[gap|budget-management-engine]] | Open | TBD | Workshop on budget rules | Week 2 Apr |
| [[gap|virtual-warehouse-inventory-model]] | Open | TBD | VW design workshop | Week 2 Apr |
| [[gap|custom-item-design-and-proofing]] | Open | TBD | Feasibility calc workshop | Week 3 Apr |
| [[gap|co-op-billing]] | Open | TBD | Co-op rules workshop | Week 2 Apr |
| [[gap|program-window-time-gating]] | Open | TBD | Program frequency review | Week 2 Apr |
| [[gap|proxy-delegate-ordering]] | Open | TBD | Proxy auth model decision | Week 2 Apr |
| [[gap|procurement-controlled-order-release]] | Open | TBD | Release criteria workshop | Week 3 Apr |
| [[gap|virtual-warehouse-inventory-transfers]] | Open | TBD | Transfer frequency review | Week 3 Apr |
| [[gap|self-registration-with-dual-auth]] | Open | TBD | Azure AD API validation | Week 2 Apr |
| [[gap|request-access-flow]] | Open | TBD | Approval authority decision | Week 2 Apr |

---

## Related Pages

- [[meeting|01-merchtank-overview]] — Executive summary and gap W1-W8
- [[meeting|02-virtual-warehouse-walkthrough]] — VW deep dive
- [[meeting|03-custom-requests]] — Custom request workflow and design
- [[meeting|04-fulfillment-demo]] — Fulfillment, order lifecycle, batch processing
- [[gap|budget-management-engine]] — First gap to design and build
- [[gap|virtual-warehouse-inventory-model]] — Architectural foundation
