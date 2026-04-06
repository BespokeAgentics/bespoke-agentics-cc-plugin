---
type: gap
client: boston-beer-company
status: open
severity: high
category: catalog-management
related-feature: "[Catalog Browsing]([[feature|catalog-browsing]])"
resolution-approach: custom-dev
created: 2026-04-06
updated: 2026-04-06
sources:
  - "[[meeting|01-merchtank-overview]] Gap W1-G1"
  - "[[meeting|02-virtual-warehouse-walkthrough]] Workflow 3: Catalog and Product Browsing"
  - "[[meeting|03-custom-requests]] Gap W2-G4"
tags: program-windows, time-gating, catalog-entitlements, procurement-workflow
---

# Gap: Program Window Time-Gating

## Description

MerchTank supports "program windows" — time-bound campaigns where specific products are available for ordering only during a designated window (typically a few weeks). Outside the window, items are not visible in the catalog. Programs are distinct from "Everyday" products, which are always available.

Salesforce B2B Commerce catalog entitlements are account-based and do not support time-based visibility. Products are either assigned to an entitlement policy (always visible to that account) or not assigned at all. There is no concept of temporary, time-gated product availability.

This gap affects the Procurement team's primary workflow for managing tent-pole seasonal campaigns (e.g., "Suncruiser Summer 2026").

## Current State

**MerchTank Program Model:**
- Programs have explicit open and close dates (e.g., "Suncruiser Summer 2026" opens March 1, closes April 15)
- Items can belong to "Everyday" (always available) or a specific program (time-gated)
- During an active program window, items appear in catalog navigation and search
- Outside the window, items are hidden from catalog (users cannot search for or order them)
- Programs are visible in navigation as tiles or dropdown options
- Alert banner is admin-configurable ("Edit Attention..." link) to promote current programs
- Procurement team sets up program metadata (name, dates, description); Brand teams assign items to programs

**Operational Impact:**
- Pre-orders for programs are common: Procurement releases pre-orders after vendors fulfill inventory
- Budget may be allocated per program or per brand (affects [[gap|budget-management-engine]])
- Users must understand which programs are currently active to find relevant products

## Target State

**Salesforce Program Window Architecture:**
- Custom Metadata Type `Program_Window__mdt`:
  - Fields: Program_Name__c, Open_Date__c (Date), Close_Date__c (Date), Active__c (checkbox), Description__c
  - Records: One per program (Suncruiser Summer 2026, Fall Campaign 2026, etc.)

- Entitlement Policy per program:
  - One Entitlement Policy per Program (e.g., "Suncruiser_Summer_2026_Entitlement")
  - Products assigned to both the program Entitlement Policy and brand Category

- Scheduled Flow automation:
  - Trigger on time-based event (daily at midnight)
  - Query all active Program_Window__mdt records
  - For programs with open_date reached: Activate corresponding Entitlement Policy
  - For programs with close_date reached: Deactivate corresponding Entitlement Policy
  - Log audit trail of activation/deactivation

- Product Category hierarchy:
  - Top-level categories: Programs (Programs), Brands (Samuel Adams, Twisted Tea, etc.)
  - Products assigned to both Program and Brand categories for flexible filtering

- CMS Content blocks:
  - Configurable alert banner (managed by Procurement)
  - Program tile cards showing current active programs
  - Landing page with program descriptions and imagery

**Integration with Order Management:**
- Cart validation ensures items are from active programs or "Everyday"
- Order detail shows which program each line item belongs to
- Procurement-controlled order release (see [[gap|procurement-controlled-order-release]]) may be program-specific

## Gap Analysis

### What Salesforce Lacks

Salesforce B2B Commerce Entitlement Policies do not support:
- Time-based activation/deactivation
- Scheduled policy visibility
- Temporary product availability windows
- Program-to-Policy bindings with date logic

### Root Cause

B2B Commerce is designed for persistent catalogs assigned to buyer groups. The architecture does not anticipate temporary, seasonal programs with time-based visibility. BBC's model requires dynamic catalog management tied to business calendars and campaigns.

### Impact

**Without Resolution:**
- All products would be visible year-round (or manually hidden/shown by admins)
- Users could attempt to order out-of-window program items, leading to confusion and support requests
- Procurement loses the ability to enforce ordering windows programmatically
- Campaign timing cannot be automated; manual intervention required for each program launch/close
- Pre-order workflow is compromised: No way to hold orders until program officially opens

## Resolution Options

### Option 1: Custom Program Window Metadata + Scheduled Flow (RECOMMENDED)

**Approach:**
1. Create `Program_Window__mdt` custom metadata type with fields: Name, Open_Date, Close_Date, Active
2. For each program, create one Entitlement Policy in B2B Commerce
3. Build Scheduled Flow triggered daily at midnight (or on-demand):
   - Query all Program_Window__mdt records
   - For each program with current date >= Open_Date and <= Close_Date: Activate Entitlement Policy
   - For each program with current date > Close_Date: Deactivate Entitlement Policy
   - Create audit record in `Program_Window_Audit__c` for compliance
4. Configure Product Categories: Programs (top-level) + Brands (nested)
5. Assign each product to: Brand Category + Program Entitlement Policy
6. Build CMS Content block for configurable alert banner (Procurement can edit without technical help)
7. Create admin Lightning page for Program Window management (CRUD for programs, entitlement policy status view)

**Effort:** M (Medium) — 2-3 weeks
- Week 1: Metadata type design, Entitlement Policy setup, Flow automation
- Week 2: Product Category hierarchy, CMS content blocks
- Week 3: Admin Lightning page, testing, documentation

**Advantages:**
- Fully automated: No manual intervention once programs are set up
- Audit trail: Tracks every policy activation/deactivation
- Scalable: Add new programs without code changes (metadata-driven)
- Flexible: Time logic can be extended (e.g., pre-order windows, early-access windows)
- Lower maintenance: No custom Apex required

**Risks/Dependencies:**
- Flow execution timing: Daily 1 AM run might not align with global time zones. Consider multiple schedules or UTC standardization.
- Entitlement Policy activation is asynchronous: Delay of up to 1 hour possible. Not an issue for daily schedules, but important for edge cases.
- Flow governor limits: If many programs/policies, Flow might hit governor limits. Mitigation: Batch multiple updates or use Apex.
- CMS Content Management: Procurement team must be trained on CMS UI for alert banner editing.

**Trade-offs:**
- Requires Entitlement Policies to be pre-created (1:1 with programs) in Setup
- Relies on Flow Scheduled Actions (not as deterministic as cron jobs)
- Product categories must be maintained alongside Entitlement Policies

---

### Option 2: Custom Program Window Object + Apex Scheduled Job

**Approach:**
1. Create custom object `Program__c` with fields: Name, Open_Date__c, Close_Date__c, Status__c (picklist), Active__c
2. Build Apex scheduled job (runs daily) that:
   - Queries Program__c records
   - Updates Status field based on current date logic
   - Calls Salesforce Commerce API to activate/deactivate Entitlement Policies
   - Creates audit trail
3. LWC admin component for Program CRUD and status monitoring
4. Entitlement Policy setup as in Option 1

**Effort:** M-L (2-4 weeks)
- Week 1: Custom object design, Apex scheduled job
- Week 2: Commerce API integration, error handling
- Week 3-4: Admin LWC, testing, documentation

**Advantages:**
- More explicit control: Custom object stores program state (vs. metadata-only)
- Easier to extend: Program records can have additional fields (e.g., budget allocation, approval status)
- Auditing: All program changes stored in object record history
- Commerce API calls are explicit and testable

**Risks/Dependencies:**
- Apex governance: Scheduled jobs have limits on batch size and API calls
- More code to maintain: Requires ongoing Apex support
- API rate limits: Commerce API calls might hit limits for large program counts
- Error handling: If API calls fail, program doesn't activate/deactivate; need monitoring

**Trade-offs:**
- More complex than Option 1 (requires Apex developer)
- Requires testing of Commerce API integration
- Ongoing maintenance of scheduled job

---

### Option 3: External Campaign Management System + Event-Driven Sync

**Approach:**
- Use external system (Marketo, Salesforce Marketing Cloud, or custom campaign tool) as source of truth for programs
- Platform Events published when program starts/ends
- Salesforce Flow subscribes to events and activates/deactivates Entitlements
- Reduces maintenance in Salesforce; program logic lives in marketing system

**Effort:** M-L (3-4 weeks)
- Week 1: Integration architecture design, event mapping
- Week 2-3: Event subscription Flow, error handling, testing
- Week 4: Documentation, training

**Advantages:**
- Marketing team owns program calendar (aligns with their processes)
- Event-driven: Changes propagate immediately vs. daily schedules
- Reduces duplicated data: Single source of truth in marketing system

**Risks/Dependencies:**
- External system dependency: If marketing system is unavailable, Salesforce doesn't activate programs
- Event delivery guarantee: Platform Events have retry limits; failed activations need monitoring
- Integration maintenance: Two systems to keep in sync
- Data consistency: Requires strong governance around program metadata

**Trade-offs:**
- Adds external system dependency
- Requires integration with marketing platform (scope creep)
- Less Salesforce control over program timing

---

## Recommended Approach

**Option 1 (Custom Metadata + Scheduled Flow)** is recommended because:

1. **Simplicity:** No custom Apex required; metadata-driven approach is maintainable by admins.
2. **Speed:** Can be implemented in 2-3 weeks; ready for Phase 1 launch.
3. **Autonomy:** BBC controls program calendar in Salesforce without external dependencies.
4. **Audit Trail:** Native Salesforce audit logging ensures compliance visibility.

**Option 2** is a fallback if BBC wants to extend program objects with additional fields (e.g., budget per program, approval workflows). Can be considered for Phase 2.

## Effort Estimate

**Option 1:** Medium (M)
- Effort: 2-3 weeks (80-120 hours)
- Confidence: High (Scheduled Flows are well-tested; Entitlement Policy concepts are standard)
- Unknowns: Number of programs; product category hierarchy complexity; Procurement training needs

**Option 2:** Medium-Large (M-L)
- Effort: 2-4 weeks (80-160 hours)
- Confidence: Medium (Apex scheduled jobs + Commerce API integration are more complex)
- Unknowns: Commerce API availability and performance; error handling requirements

**Option 3:** Medium-Large (M-L)
- Effort: 3-4 weeks (120-160 hours)
- Confidence: Medium (external system integration adds risk)
- Unknowns: Marketing system API availability; event delivery SLA; integration complexity

## Dependencies

### Must Happen Before
- [[decision|Product-Category-Hierarchy]] — Program categories must be defined before Entitlement Policies are created
- [[feature|catalog-browsing]] — Category hierarchy and entitlement policies enable catalog browsing

### Must Happen Alongside
- [[feature|product-assignment-to-programs]] — Products must be assigned to programs/categories as part of catalog data migration

### Blocks
- [[feature|order-creation-and-validation]] — Cart validation must check product program eligibility (see Gap W2-G4)
- [[feature|procurement-controlled-order-release]] — Pre-order release workflow depends on program context

## Evidence

### Meeting 1: MerchTank Overview (Dec 4, 2025)
**Gap W1-G1: Program-Based Ordering Windows**
- Severity: High
- Description: "MerchTank has 'program windows' — time-bound campaigns where items are available for ordering for a few weeks, with fulfillment months later. Salesforce B2B Commerce does not natively support time-gated catalog availability."
- Impact: "Procurement team's primary workflow for tent-pole campaigns would not function."
- Recommendation: "Custom Program__c object with scheduled jobs to manage catalog activation/deactivation (~M effort)"

### Meeting 2: Virtual Warehouse Walkthrough (Feb 2, 2026)
**Workflow 3: Catalog and Product Browsing**
- Current State: "Programs have ordering windows (time-bound availability)"
- "Everyday program is always available"
- Target State: "Custom Metadata Type `Program_Window__mdt` for order window dates"
- "Entitlement Policies per program, activated/deactivated by scheduled Flow based on window dates"

### Meeting 3: Custom Requests (Mar 9, 2026)
**Gap W2-G4: Program Order Window Time-Gating**
- Severity: Medium
- Impact: "Without time-gating, users could order program merchandise outside the designated window. This could disrupt inventory planning and campaign timing."

## Validation Notes

SFCC Validation Report confirms:
- "Entitlement Policies support time-based visibility via custom Flow logic"
- "Scheduled Flows can activate/deactivate policies daily"
- "CMS Content Blocks support dynamic alert banners"

## Open Questions

1. **Program Frequency & Count:** How many programs are active per year? What is the typical duration of a program window?
   - *Impact if answered wrong:* Scheduled Flow frequency and load testing requirements change
   - *Owner:* BBC Procurement

2. **Pre-Order Windows:** Are there separate pre-order windows before a program officially opens (e.g., "orders accepted Feb 1-7, items available Mar 1")? If so, are pre-orders held until release date?
   - *Impact if answered wrong:* Program Window__c needs additional fields (PreOrder_Open_Date__c, Release_Date__c)
   - *Owner:* BBC Procurement

3. **Overlapping Programs:** Can items belong to multiple programs? Or is one item per program only?
   - *Impact if answered wrong:* Product-to-Program entitlement model changes
   - *Owner:* BBC Procurement/Brand

4. **Program Budget:** Is budget allocated per program or per brand (which may span multiple programs)?
   - *Impact if answered wrong:* Integration with [[gap|budget-management-engine]] changes
   - *Owner:* BBC Finance/Procurement

## Related Gaps

- [[gap|budget-management-engine]] — Budget may be program-specific
- [[gap|procurement-controlled-order-release]] — Pre-order release tied to program open dates
- [[gap|catalog-browsing]] — Category hierarchy and program visibility depend on this gap

## Status & Next Steps

**Status:** Open (design phase)

**Next Steps:**
1. Confirm program count and typical duration (BBC Procurement)
2. Define program category hierarchy (BBC Procurement/Brand)
3. Confirm pre-order window requirements (BBC Procurement)
4. Create Program_Window__mdt records for all current and planned programs
5. Build Scheduled Flow automation
6. Create admin Lightning page for program management
7. Configure CMS Content blocks for alert banner
8. Test activation/deactivation timing
