---
type: meeting
client: Boston Beer Company
meeting-date: 2026-02-02
attendees: BBC Operations Team, Fulfillment Operator
recording-path: meetings/02-virtual-warehouse-walkthrough/source/
transcript-path: meetings/02-virtual-warehouse-walkthrough/analysis/
pipeline-outputs: gap-analysis-bbc-vw-walkthrough.md
created: 2026-03-16
updated: 2026-03-16
sources:
  - meetings/02-virtual-warehouse-walkthrough/analysis/gap-analysis-bbc-vw-walkthrough.md
  - meetings/02-virtual-warehouse-walkthrough/confluence/
tags:
  - virtual-warehouse
  - inventory
  - fulfillment
  - cart
  - checkout
  - proxy-ordering
---

# Meeting: Virtual Warehouse Walk-through

## Summary

Comprehensive walkthrough of MerchTank's Virtual Warehouse system, inventory management, catalog browsing, shopping cart with budget validation, and checkout workflow. This recording revealed the foundational role of the Virtual Warehouse concept as the organizational unit for per-person inventory allocation (95 VWs currently), brand-based budget enforcement, and proxy ordering context. The cart system integrates budget validation at the brand level with pack-based quantity model, and checkout captures multiple custom fields for delivery preferences and internal coordination. Complete gap analysis with effort estimates and critical decisions identified 22 features with 39% requiring significant custom development and multiple high-risk integration points.

## Key Topics Covered

- **Virtual Warehouse Management:** 95 per-person inventory allocations with Lot numbers, owner assignment, active/inactive status; 1:1 constraint between Unit and VW
- **VW Transfers:** Admin-level inventory transfer between VWs with packout unit quantities and concurrent locking concerns
- **Catalog & Product Browsing:** Dashboard with program/brand tile navigation, filtered catalog by program/brand, sub-type filtering, grid/list toggle
- **Product Detail:** Horizontal card layout with image carousel, variant options, key-value detail panel (SKU, Qty Packed, Ship Method, Location), pack-based quantity selection
- **Shopping Cart:** Brand-grouped line items with per-brand budget summaries, pack-based columns, Need By dates, backorder flags; budget validation prevents overspending
- **Proxy/Delegate Ordering:** Procurement staff order on behalf of VW owners with green header context banner persisting through cart/checkout
- **Checkout Flow:** Three-column layout with Ship-To address, Internal Contact Person, and carrier/delivery preferences; "Lowest Cost/Best Partner" optimization and delivery instructions
- **Program Windows:** Time-bound catalog availability with admin-controlled alert banner and Need By date calendars
- **Authentication:** Azure AD SAML 2.0 SSO with corporate email (@bostonbeer.com)

## Features Discovered / Updated

- [[virtual-warehouse|Virtual Warehouse]]: Per-person inventory allocation with unique Lot Number, owner lookup, active status, 1:1 unit constraint
- [[vw-transfer|VW Transfer Workflow]]: Admin packout-unit transfers between VWs with concurrent locking validation
- [[vw-management|VW Management UI]]: Dropdown selector, data table with search/filter/export, modal editor, "Add VW" action
- [[catalog-browsing|Catalog & Product Browsing]]: Program/Brand tile navigation, filtered catalog, sub-type filters, grid/list toggle
- [[product-card|Product Card with Inline Purchase]]: Horizontal layout with image carousel, options dropdown, detail panel, buy button
- [[pack-based-ordering|Pack-Based Ordering]]: All quantities in packout units (1-50 items per pack) with pack-based pricing
- [[shopping-cart-budget|Shopping Cart with Budget Validation]]: Brand-grouped items, per-brand budget summaries, pack-based columns, Need By dates, backorder flags
- [[checkout-workflow|Checkout Workflow]]: Three-column address/contact/shipping layout with carrier optimization and delivery instructions
- [[proxy-ordering|Proxy/Delegate Ordering]]: Procurement ordering for VW owners with green context banner
- [[program-windows|Program Order Windows]]: Time-gated catalog availability with admin-configured alert banner
- [[azure-ad-sso|Azure AD SAML 2.0 SSO]]: Microsoft Azure AD integration with corporate email
- [[order-history|Order History Management]]: Past orders with status tracking, duplication, editing for unshipped orders

## Gaps Identified

### Critical (Blocks Architecture)

- [[gap-vw-inventory-allocation|Gap VW-G1: No Per-Person Inventory Allocation]]: Severity Critical - VW model has no B2B Commerce equivalent; foundational architecture decision required. Options: (1) Full custom build (6-8 weeks), (2) Simplify to budget-only (2-3 weeks with feature loss), (3) Map to B2B Commerce Inventory Locations (4-5 weeks)
- [[gap-virtual-warehouse|Gap VW-G2: 1:1 Unit-to-VW Constraint]]: Severity Medium - Server-side validation requires Apex trigger (~1 week)

### High-Risk Integration

- [[gap-oracle-integration|Gap: Oracle ERP Budget Sync]]: Severity High - Budget data sync, co-op billing, and invoicing require MuleSoft integration (6+ weeks, high complexity)
- [[gap-fulfillment-integration|Gap: Fulfillment Provider Integration]]: Severity High - Unknown vendor protocols; potentially multiple integration approaches needed (4-6+ weeks)
- [[gap-vw-transfer-locking|Gap TR-G2: Concurrent Transfer Locking]]: Severity Medium - Pessimistic locking required to prevent simultaneous VW transfer races

### Feature Gaps

- [[gap-inventory-transfer|Gap TR-G1: No Inventory Transfer Mechanism]]: Severity High - B2B Commerce lacks transfer capability; custom Apex service needed (3-4 weeks)
- [[gap-brand-budget-tracking|Gap SC-G1: Brand-Based Budget Tracking]]: Severity Critical - Entire budget engine custom (4-5 weeks). Open: How are co-op splits calculated?
- [[gap-proxy-ordering|Gap SC-G2: Proxy/Delegate Ordering]]: Severity High - Custom LWC selector + WebCart context field + Apex validation (2-3 weeks). Risk: session management for proxy context
- [[gap-cart-brand-grouping|Gap SC-G3: Cart Brand Grouping]]: Severity High - Standard B2B Commerce uses flat list; custom cart LWC required for brand grouping
- [[gap-need-by-date|Gap SC-G4: Per-Line-Item Need By Date]]: Severity Medium - Custom CartItem field (included in cart build)
- [[gap-pack-pricing|Gap PD-G1: Pack-Based Ordering Model]]: Severity High - Threads through catalog, cart, checkout, fulfillment; custom display layer required (2 weeks)
- [[gap-product-card|Gap PD-G2: Custom Product Card Layout]]: Severity Medium - Horizontal layout with detail panel non-standard; 1 week custom LWC
- [[gap-checkout-layout|Gap CK-G1: Three-Column Checkout Layout]]: Severity Low - Recommend standard stepped checkout as UX improvement
- [[gap-internal-contact|Gap CK-G2: Internal Contact Person]]: Severity Medium - Custom Order fields + checkout LWC (1 week)
- [[gap-carrier-optimization|Gap CK-G3: Carrier Optimization]]: Severity Medium - "Lowest Cost/Best Partner" logic unclear (fulfillment-provider vs platform-managed)
- [[gap-authorization-sso|Gap AU-G1: Role Mapping from Azure AD]]: Severity Medium - Map Azure AD groups to Permission Set Groups (1 week)

### Architectural Decisions Required

| # | Decision | Impact | Blocks |
|---|----------|--------|--------|
| D1 | Retain Virtual Warehouse model or simplify to budget-only? | 30% development scope reduction if simplified | Foundational architecture |
| D2 | Is Oracle ERP the system of record for budgets? | Determines integration direction | Budget data architecture |
| D3 | Simplify pack-based ordering to standard unit quantities? | Impacts every touchpoint | Cart, checkout, fulfillment design |
| D4 | Which fulfillment vendors and their integration protocols? | Determines integration architecture | Integration design |
| D5 | Are unobserved modules (HISTORY, BUDGETS, APPROVALS, BAM, FULFILLMENT, REPORTING, CONTACTS, LINKS) in Phase 1 scope? | Could double effort estimate | Scope definition |
| D6 | MuleSoft middleware vs direct Apex callouts vs alternative iPaaS? | Affects architecture, licensing, maintainability | Integration implementation |

## Decisions Made

- **Investigation Approach:** Comprehensive workflow-based gap analysis with effort estimates and risk scoring
- **Phasing Strategy:** 4-phase approach recommended (Foundation 1-10 weeks, VW+Budget 6-18 weeks, Cart+Checkout 12-22 weeks, Reporting+Migration 18-26 weeks) with 6-9 months estimated timeline for 3-person dev team
- **POC Recommendations:** Build POCs for budget enforcement, item customization, and program window management before full development commitment
- **VW Architecture:** Recommended full custom build (Option 1) pending validation that VW feature is actively used

## Open Questions

### P1 - Blocks Design (Must Answer Before Design Phase)

- [[q-vw-system-record|Q1: System of Record for Inventory]] - Is MerchTank the inventory system of record, or does it sync from WMS/supply chain? (Architecture impact)
- [[q-oracle-budget-system|Q2: Budget System of Record]] - Is Oracle ERP the system of record for brand budgets? How are budgets initially loaded? (Data architecture)
- [[q-coop-split-logic|Q3: Co-op Billing Splits]] - What is the co-op split logic for wholesaler invoicing? (Budget model + Oracle integration)
- [[q-fulfillment-vendors|Q4: Fulfillment Vendor Capabilities]] - Names, integration protocols (API, EDI, email, portal) (Integration architecture)
- [[q-vw-simplification|Q5: Virtual Warehouse Retention]] - Retain per-person allocation or simplify to budget-only? (Foundational architecture)
- [[q-unobserved-scope|Q6: Unobserved Modules Scope]] - HISTORY, BUDGETS, APPROVALS, BAM, FULFILLMENT, REPORTING, CONTACTS, LINKS in Phase 1? (Project scope)

### P2 - Blocks Estimates

- [[q-ssrs-report-volume|Q7: SSRS Report Count & Usage]] - How many SSRS reports exist and which are actively used? (Reporting effort)
- [[q-carrier-logic|Q8: Carrier Optimization Location]] - Does "Lowest Cost/Best Partner" run in MerchTank or via fulfillment provider? (Checkout effort)
- [[q-custom-design-process|Q9: Custom Design Handling]] - Internal creative team or external vendor? Approval process? (Custom Design workflow)
- [[q-budget-period|Q10: Budget Period Structure]] - Annual? Quarterly? Rolling? Per-wholesaler? Per-region? (Budget engine)
- [[q-product-count|Q11: Product Catalog Size]] - Total products? Variants? (Data migration effort)
- [[q-order-volume|Q12: Historical Order Volume]] - Actual count? Sequential IDs? (Data migration effort)
- [[q-batch-jobs|Q13: Automated Data Feeds]] - Any feeds beyond SSRS against MerchTank DB? (Integration architecture)

### P3 - Nice to Know

- [[q-ship-send-workers|Q14: Ship/Send Workers Concept]] - Informational or system integration trigger? (Checkout field design)
- [[q-pos-reporting|Q15: POS Reporting System]] - Source system? Data consumption? (Reporting/integration)
- [[q-role-derivation|Q16: Role Derivation]] - From Azure AD groups or MerchTank-internal? (Authentication)
- [[q-email-notifications|Q17: Email Notification Triggers]] - Current triggers and conditions? (Notification design)
- [[q-coop-budget-interaction|Q18: Co-op/Budget Interaction]] - Shows full price or BBC-only portion? (Budget display)
- [[q-catalog-links|Q19: File Schedule & Wholesale Gallery]] - Purpose of these links on catalog page? (Content management)

## Action Items

- **[BBC Business Sponsor]:** Confirm Virtual Warehouse retention decision - Due [Week 1]
- **[Finance Team]:** Confirm whether Oracle ERP is budget system of record and document co-op split logic - Due [Week 2]
- **[IT]:** Identify fulfillment vendor names and integration protocol capabilities - Due [Week 2]
- **[IT]:** Clarify whether "Lowest Cost/Best Partner" carrier logic runs in MerchTank or is vendor-managed - Due [Week 2]
- **[Procurement Team]:** Catalog all SSRS reports and their usage frequency - Due [Week 3]
- **[Business Sponsor]:** Scope the unobserved modules (HISTORY, BUDGETS, APPROVALS, BAM, FULFILLMENT, REPORTING, CONTACTS, LINKS) for Phase 1 - Due [Week 1]
- **[Architecture Team]:** Design Virtual Warehouse custom object model and validate with BBC before detailed build - Due [Week 4]
- **[Architect]:** Prototype budget enforcement at checkout with hard-stop validation - Due [Week 4]

## Raw Artifacts

- **Gap Analysis:** meetings/02-virtual-warehouse-walkthrough/analysis/gap-analysis-bbc-vw-walkthrough.md
- **Feature Inventory:** meetings/02-virtual-warehouse-walkthrough/analysis/feature-inventory-*.md
- **Screen Catalog:** meetings/02-virtual-warehouse-walkthrough/analysis/screen-catalog.md
- **Confluence Export:** meetings/02-virtual-warehouse-walkthrough/confluence/gap-analysis-confluence-boston-beer-company.{html,confluence}
- **Recording:** meetings/02-virtual-warehouse-walkthrough/source/
