# Boston Beer Company Feature Wiki Index

**Status:** Initial bootstrap complete — 19 feature pages created from gap analysis files
**Date:** 2026-04-06
**Sources:** 5 gap analysis documents + 2 feature inventory documents
**Total Features Identified:** 19 distinct major features (with many sub-features within each)

---

## Feature Categories

### Ordering & Shopping (6 features)

1. **[[program-based-ordering-windows]]** — Time-bound merchandise ordering campaigns with start/end dates
   - Decision: Custom (M effort)
   - Critical for procurement workflow; controls campaign timing

2. **[[product-catalog-and-browse]]** — Two-dimensional product navigation (Programs × Brands)
   - Decision: Config (M effort)
   - Maps well to Salesforce B2B Commerce; tile navigation is the main customization

3. **[[shopping-cart-with-budget]]** — Brand-grouped cart with real-time budget enforcement
   - Decision: Custom (L effort)
   - Most business-logic-dense screen; pack-based quantities and brand grouping are custom

4. **[[pack-based-ordering-model]]** — All quantities/pricing in packout units (not individual items)
   - Decision: Custom (M effort)
   - Pervasive across all ordering touchpoints; threading concern

5. **[[proxy-ordering]]** — Procurement staff can place orders on behalf of Sales Reps
   - Decision: Custom (M effort)
   - Core procurement workflow; no B2B Commerce equivalent

6. **[[approval-workflows]]** — Automated manager approval for orders exceeding spend limits
   - Decision: Custom (M effort)
   - Dependent on Sam Central integration for spend limit data

### Catalog & Inventory (4 features)

7. **[[virtual-warehouse-model]]** — Per-user inventory allocation (95 VWs currently)
   - Decision: Custom (XL effort)
   - Architectural foundation; largest single effort in migration
   - Critical decision: Retain full model or simplify to budget-only?

8. **[[virtual-warehouse-transfers]]** — Admin workflow to redistribute inventory between VWs
   - Decision: Custom (L effort)
   - Secondary feature; lower priority than VW model itself

9. **[[brand-budget-tracking]]** — Per-brand, per-wholesaler budget allocation and enforcement
   - Decision: Custom (L effort)
   - Core financial control; affects every transaction
   - Critical decision: Hard stop or soft warning enforcement?

10. **[[address-book-management]]** — Multiple shipping addresses with validation and multi-ship support
    - Decision: Custom (M effort)
    - Address validation integration needed; multi-ship adds complexity

### Custom Requests (2 features)

11. **[[custom-item-design-submission]]** — Two-panel form for custom POS merchandise request submission
    - Decision: Custom (XL effort)
    - Unique to BBC; largest development effort
    - Includes: request form, designer assignment, file uploads, approval workflow

12. **[[digital-file-delivery]]** — Automated workflow replacing manual multi-app digital file delivery
    - Decision: Custom (M effort)
    - Currently spans 4 systems (MerchTank, Illustrator, OneDrive, Outlook)
    - Automation opportunity: highest ROI workflow improvement

### Account & User Management (3 features)

13. **[[buyer-account-model]]** — Hierarchical account structure for B2B Commerce
    - Decision: Custom (M effort)
    - Consolidates 95 flat VWs into managed hierarchy
    - Critical decision: Target hierarchy structure (regional? by org?)

14. **[[buyer-user-management]]** — Role-to-permission-set mapping for 6+ user types
    - Decision: Custom (M effort)
    - Role segmentation and provisioning workflows
    - Dependent on Azure AD SSO integration

### Fulfillment (3 features)

15. **[[order-queue-and-fulfillment]]** — Operator-focused fulfillment dashboard replacing Excel shadow system
    - Decision: Custom (L effort)
    - Shadow system elimination: highest-value migration outcome
    - Consolidates: queue, priority queuing, multi-destination visibility, KPI cards

16. **[[shipment-recording]]** — Recording shipment tracking information and order status transition
    - Decision: Custom (M effort)
    - Includes: carrier selection, tracking number entry, UPS integration opportunity (Phase 2)

### Reporting & Analytics (1 feature)

17. **[[order-history-and-analytics]]** — Order history, budget/spend dashboard, co-op billable reporting
    - Decision: Custom (M effort)
    - Finance team requires specialized co-op/billable reporting with cost center data

### Integrations (2 features)

18. **[[rootstock-eap-integration]]** — Order sync to Rootstock ERP for fulfillment and invoicing
    - Decision: Custom (L effort)
    - Critical for order-to-cash workflow
    - Invoice retrieval and co-op split billing dependent on API

---

## Decision Summary

| Decision | Count | Total Effort |
|----------|-------|--------------|
| **CONFIGURATION** (no code required) | 1 | S |
| **CUSTOM** (code/objects required) | 18 | L×6 + M×7 + XL×2 + L-M×1 + M-L×1 + M×1 |
| **THIRD-PARTY** (AppExchange/external) | 0 | — |
| **TBD** (architecture decision needed) | 3 | Pending |

### High-Effort Features (XL/L effort)

1. **Virtual Warehouse Model (XL, 6-8 weeks)** — Architectural foundation; largest single effort
2. **Custom Item Design Submission (XL, 4-6 weeks)** — Multi-panel form, approval workflow, file uploads
3. **Order Queue & Fulfillment Dashboard (L, 3-4 weeks)** — Shadow system replacement; highest ROI
4. **Shopping Cart with Budget (L, 3-4 weeks)** — Pack-based display, budget enforcement
5. **Brand Budget Tracking (L, 3-4 weeks)** — Custom objects, cart validation, dashboard
6. **Rootstock Integration (L, 2-3 weeks)** — Order sync, invoice retrieval

### Critical Decisions Required Before Design

1. **Retain full Virtual Warehouse model, or simplify to budget-only allocation?**
   - Determines 30% of custom development effort
   - Architectural decision with major scope implications

2. **Budget enforcement: hard stop or soft warning with approval?**
   - Affects checkout validation architecture
   - Requires clear business rules

3. **Account hierarchy target structure?**
   - How should 95 VWs consolidate into Buyer Accounts?
   - Regional? By brand? By org?

4. **Sam Central integration scope and API contract?**
   - Spend limit data critical for approval workflows
   - API contract unknown; blocks estimation

5. **UPS API integration for shipment tracking?**
   - Phase 1: manual entry. Phase 2: automation
   - Reduces operator manual work significantly

---

## Coverage by Business Domain

### Catalog Management
- Product catalog and browse (✓ Covered)
- Program-based ordering windows (✓ Covered)
- Pack-based ordering model (✓ Covered)

### Order Management
- Shopping cart with budget (✓ Covered)
- Proxy ordering (✓ Covered)
- Checkout & shipping (Partially — see Address Book)
- Approval workflows (✓ Covered)
- Order history (✓ Covered)

### Inventory Management
- Virtual warehouse model (✓ Covered)
- Virtual warehouse transfers (✓ Covered)
- Brand budget tracking (✓ Covered)

### Custom Requests / Creative Workflow
- Custom item design submission (✓ Covered)
- Digital file delivery (✓ Covered)

### Fulfillment Operations
- Order queue & fulfillment (✓ Covered)
- Shipment recording (✓ Covered)

### Account & Permissions
- Buyer account model (✓ Covered)
- Buyer user management (✓ Covered)
- Address book (✓ Covered)

### Integrations
- Rootstock ERP integration (✓ Covered)

### Reporting & Analytics
- Order history & analytics (✓ Covered)

---

## Features Not Yet Documented

Based on gap analysis review, the following areas may require additional features:

- **Self-Registration & Request Access Flow** (from Batch 3) — User provisioning workflows
- **Commerce My Profile APIs** — User profile management (may be standard config)
- **Password Management & Authentication** — SSO, MFA, local credentials
- **Platform Events & CDC Integration** — Real-time integration patterns
- **Order Data Model (detailed)** — Custom objects for fulfillment vendors, co-op tracking
- **Reporting & Excel Exports** — Automated report generation, scheduled exports
- **External Vendor Integration** — TradeWearables, Strand Shop, BAM deep integration
- **Fulfillment Vendor Management** — 20+ vendor assignments, batch processing
- **Invoice Access Integration** — Rootstock invoice display and download
- **UPS Carrier Integration (Phase 2)** — AppExchange connectors or custom APIs
- **Sam Central Integration** — Spend limit data sync

---

## Recommended Phasing

### Phase 1 (Weeks 1-6): Foundation & Core Catalog
- Product catalog migration
- Buyer account & user provisioning
- Basic authentication (Azure AD SSO)
- Tile navigation dashboard

### Phase 2 (Weeks 4-10): Core Ordering
- Shopping cart with pack-based pricing
- Brand budget enforcement
- Proxy ordering context
- Checkout with address management
- Program window management

### Phase 3 (Weeks 8-16): Virtual Warehouse & Fulfillment
- Virtual warehouse model (if retained)
- VW transfers
- Order queue & fulfillment dashboard
- Shipment recording
- Order history & analytics

### Phase 4 (Weeks 12-20): Advanced Features
- Custom item design & proofing workflow
- Digital file delivery automation
- Co-op billing & reporting
- Rootstock ERP integration
- Approval workflows with Sam Central

### Phase 5 (Weeks 18+): Polish & Launch
- User acceptance testing
- Data migration (full historical orders)
- Training & change management
- Go-live

---

## Legend

- **✓ Covered** — Wiki page created
- **Partially** — Some aspects covered, may need additional pages
- **TBD** — Not yet documented; additional research needed

---

**Next Steps:**

1. Use these feature pages as input to technical design & architecture
2. Conduct workshop on Virtual Warehouse model (critical decision)
3. Validate account hierarchy target structure
4. Get Sam Central API contract from BBC IT
5. Create ADRs for high-effort/risky features
6. Develop proof-of-concept for budget enforcement and pack-based cart
