---
type: meeting
client: Boston Beer Company
meeting-date: 2025-12-04
attendees: Jen Berger
recording-path: meetings/01-merchtank-overview/source/
transcript-path: meetings/01-merchtank-overview/analysis/
pipeline-outputs: gap-analysis-sample-bbc-merchtank.md
created: 2026-03-16
updated: 2026-03-16
sources:
  - meetings/01-merchtank-overview/analysis/gap-analysis-sample-bbc-merchtank.md
tags:
  - merchtank
  - overview
  - early-analysis
---

# Meeting: MerchTank End-to-End Overview

## Summary

Initial walkthrough of Boston Beer Company's MerchTank platform covering core commerce workflows, budget management, custom item design/proofing, and order lifecycle. This meeting established the foundational understanding of BBC's merchandise ordering requirements and identified critical gaps between MerchTank capabilities and Salesforce B2B Commerce out-of-the-box features. Early analysis identified 18 features across 8 workflows with multiple critical gaps requiring custom development.

## Key Topics Covered

- **MerchTank Platform Architecture:** Custom .NET web application serving 200-500 internal users across Procurement, Sales, Creative Operations, Brand Teams, Finance, and IT
- **Core Commerce Workflows:** Sales rep product ordering, budget tracking, cart management, checkout with co-op billing, order history with procurement-controlled release
- **Custom Features:** Custom item design submission, creative operations approval, design proofing workflow
- **Integration Points:** TradeWearables (Parsons Kellogg), Strand Shop, BAM (digital asset management), SQL Server reporting (bbsqlrep01)
- **Brand Portfolio:** 12+ brands including Samuel Adams, Twisted Tea, Angry Orchard, Truly, Dogfish Head
- **Program Model:** 6 ordering programs (Everyday, Custom Design, Hot Deals, Items From Scratch, PPE, Program Samples) with time-gated availability
- **Virtual Warehouse Model:** 95 per-person inventory allocations with brand-based budget tracking per wholesaler

## Features Discovered / Updated

- [[product-ordering|Product Ordering]]: Sales rep catalog browsing by brand/program with quantity-limited purchasing
- [[budget-management|Budget Management]]: Per-brand family budget tracking with per-wholesaler allocation and annual rollover
- [[program-windows|Program-Based Ordering Windows]]: Time-bound catalog availability with procurement-controlled release workflows
- [[proxy-ordering|Proxy Ordering]]: Procurement staff ordering on behalf of sales representatives
- [[custom-item-design|Custom Item Design Submission]]: Multi-field form with file uploads (doc, docx, xls, xlsx, ppt, pptx, png, jpg, psd, ai, eps, pdf up to 50MB)
- [[design-proofing-workflow|Design Proofing Workflow]]: Designer assignment, proof upload, approval chain, email-based approval
- [[cart-management|Shopping Cart]]: Multi-step cart with address management, shipping method selection, manager notification option
- [[co-op-billing|Co-op Billing]]: Cost-sharing arrangements where wholesalers pay portion of item costs
- [[order-history|Order History]]: Past order viewing with status tracking (pending vs shipped), order duplication capability
- [[need-by-date|Need-By Date Management]]: Per-line-item delivery date calculation with delivery method impact
- [[catalog-entitlements|Catalog Entitlements]]: Product visibility scoped by wholesaler assignment and program membership
- [[reporting|Reporting & Analytics]]: Built-in reports, automated Excel exports, SQL Server reporting with VPN dependency

## Gaps Identified

- [[gap-program-windows|Gap: Program-Based Ordering Windows]]: No native time-gating in B2B Commerce; requires custom date-gated catalog entitlements
- [[gap-brand-budget-enforcement|Gap: Brand Budget Enforcement]]: Zero out-of-box budget management; complete custom build required with hard stop vs warning behavior TBD
- [[gap-custom-item-design|Gap: Custom Item Design Workflow]]: No equivalent to multi-field customization form, file uploads, proof approval chain; represents largest development effort
- [[gap-co-op-billing|Gap: Co-op Billing]]: No native cost-sharing model; requires custom object + checkout extension
- [[gap-proxy-ordering|Gap: Proxy/Delegate Ordering]]: B2B Commerce lacks native "order-on-behalf-of" for internal users with context switching
- [[gap-pack-based-ordering|Gap: Pack-Based Ordering Model]]: All quantities/pricing in packout units (1-50 items per pack); must thread through catalog, cart, checkout, fulfillment
- [[gap-procurement-order-release|Gap: Procurement-Controlled Order Release]]: Pre-orders held pending until procurement releases batch; requires custom order status workflow
- [[gap-sql-server-reporting|Gap: SQL Server Report Migration]]: Current SQL Server reporting is VPN-dependent; migration eliminates dependency but requires report replication

## Decisions Made

- **Target Platform Confirmed:** Salesforce B2B Commerce on Experience Cloud with Lightning Web Components and custom Apex
- **Phased Approach:** Recommend 4-phase implementation: Foundation → Core Custom Development → Advanced Features → Validation & Launch
- **Budget Management Priority:** Budget system identified as critical first priority due to impact on every transaction
- **Custom Item Proofing:** Recommend on-platform custom LWC approach over external tool integration for unified system management

## Open Questions

- **P1 (Design Blockers):**
  - [[q-budget-rules|Q: Budget Rules Complexity]] - Are budget rules limited to annual allocation with simple decrement, or are there more complex accrual/rollover rules?
  - [[q-program-window-events|Q: Program Window Triggering]] - Are program windows always calendar-based or are there event-driven activation scenarios?
  - [[q-coop-agreements|Q: Co-op Agreement Model]] - Are co-op agreements pre-established and stable, or negotiated per-order?
  - [[q-external-vendor-integration|Q: Vendor Integration Depth]] - Should TradeWearables, Strand Shop, and BAM integrations be deepened (SSO, data sharing) or maintained as simple links?
  - [[q-order-history-migration|Q: Order History Scope]] - Is historical order migration required, and if so, how far back?
  - [[q-mobile-access|Q: Mobile Access Requirement]] - Is mobile access needed at launch?
  - [[q-creative-proofing|Q: Creative Proofing Workflow]] - Should custom design proofing remain as human workflow or support automated approval?

- **P2 (Estimate Refinement):**
  - [[q-user-count|Q: User Count & Breakdown]] - Total users and role distribution?
  - [[q-critical-reports|Q: Critical Reports]] - Which automated reports are business-critical vs nice-to-have?
  - [[q-timeline|Q: Go-Live Timeline]] - Desired launch timeline?

## Action Items

- **[Project Sponsor]:** Clarify whether co-op agreements are pre-established and stable for custom object design - Due [Week 1]
- **[Finance Team]:** Document complete budget rules including accrual, rollover, and period management - Due [Week 2]
- **[Procurement Team]:** Validate whether program windows are calendar-based or require event-driven activation - Due [Week 2]
- **[Creative Operations]:** Confirm scope of custom item design workflow for Phase 1 vs Phase 3 - Due [Week 2]
- **[IT]:** Identify total user count by role (Sales Reps, Procurement, Brand Teams, Creative Ops, Finance, Admin) - Due [Week 1]
- **[IT]:** Catalog all current automated reports and their usage frequency - Due [Week 3]
- **[Business Sponsor]:** Confirm desired go-live timeline and phasing strategy - Due [Week 1]

## Raw Artifacts

- **Gap Analysis:** meetings/01-merchtank-overview/analysis/gap-analysis-sample-bbc-merchtank.md
- **Recording:** meetings/01-merchtank-overview/source/ (early frame analysis, screen catalog, architecture map)
- **Status:** DRAFT — Partial analysis with early frame analysis and screen catalog; full pipeline output pending
