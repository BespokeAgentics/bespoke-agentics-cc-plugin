---
type: question
client: Boston Beer Company
status: open
priority: P2
category: assumption-confirmation
owner: Procurement / Operations
created: 2026-03-16
updated: 2026-03-16
sources:
  - meetings/02-virtual-warehouse-walkthrough/analysis/gap-analysis-bbc-vw-walkthrough.md
  - meetings/03-custom-requests/analysis/gap-analysis-bbc-custom-requests-meeting.md
tags:
  - virtual-warehouse
  - inventory-management
  - scope-decision
---

# Question: Are Virtual Warehouses Actively Used?

## Question

**How actively are the 95 Virtual Warehouses currently used in production?**

Specifically:
1. How many of the 95 VWs contain active inventory (non-zero item counts)?
2. Which VWs are used regularly for ordering and inventory management?
3. What percentage of merchandise orders involve VW inventory allocation?
4. How critical is the VW model to BBC's operational workflow?
5. If VWs were simplified or eliminated, what business processes would break?

## Context

**Critical Observation from [[meeting-02-virtual-warehouse|Meeting 02 - Virtual Warehouse Walkthrough]]:**

> "Notably, all observed VWs had zero inventory instances."

This observation raises a significant question: **Is the VW feature actively used and necessary, or is it legacy functionality maintained for historical reasons?**

**Why This Matters For Design:**

The Virtual Warehouse model requires substantial custom development effort:

| Implementation Approach | Effort | Scope |
|------------------------|--------|-------|
| **Option 1: Full Custom Build** | XL (6-8 weeks) | Custom objects (Virtual_Warehouse__c, VW_Inventory_Instance__c, Unit__c), 4-5 LWC components, validation triggers, audit trail |
| **Option 2: Simplified to Budget-Only** | M (2-3 weeks) | Eliminate per-item inventory tracking; use only dollar budget allocations |
| **Option 3: Map to Accounts** | L (3-4 weeks) | Use standard Salesforce Account structure instead of custom VW objects; lose some BBC-specific semantics |
| **Option 4: Defer to Phase 2** | S (0 weeks now) | Implement other core features (ordering, budget, fulfillment) in Phase 1; validate VW necessity before custom build |

**The Zero-Inventory Observation:**

All VWs observed during the demo had zero inventory instances, which could mean:

A) **VWs are inactive/legacy** - Feature exists but isn't used; would not impact migration if deprioritized
B) **Demo timing** - VW inventory fluctuates; the demo happened during a low-inventory period
C) **VW used for other purpose** - VWs are used for budget allocation/authorization framework but inventory is managed elsewhere
D) **Inventory stored elsewhere** - Actual inventory is in a WMS/supply chain system; VWs are just an allocation container

## Impact if Unanswered

1. **Cannot Finalize Scope:** VW custom development could consume 2-3 weeks of the 6-9 month timeline. If feature is unnecessary, this is wasted effort.
2. **Resource Allocation Error:** Assigning senior developer to VW build when other features might be higher priority
3. **Timeline Risk:** If VWs turn out to be actively used after deciding to defer, Phase 2 implementation blocks fulfillment operations
4. **Architecture Complexity:** VW concept permeates proxy ordering, budget enforcement, and fulfillment routing. Uncertainty about necessity creates design ambiguity.

## Proposed Answer (if any)

**Hypothesis: VWs Are Partially Active but Not Critical for Phase 1**

**Rationale:**
- Observation of zero inventory suggests limited active use
- Proxy ordering (procurement ordering for sales reps) can be implemented using standard Salesforce Account relationships instead of VW objects
- Budget enforcement (per-brand, per-user) can be decoupled from VW concept and implemented on user/account basis
- VW could be deferred to Phase 2 pending validation of actual usage

**Alternative: VWs Are Critical for Authorization & Budget Tracking**

**Rationale:**
- VW 1:1 constraint with organizational Units suggests they serve as a primary identity/authorization framework
- Proxy ordering context depends on VW assignment
- Budget allocation might be VW-per-brand (not just user-per-brand)

**Confidence: Low** — Cannot determine without production data analysis and stakeholder interviews

## Related Features

- [[virtual-warehouse|Virtual Warehouse]]: The core feature being questioned
- [[proxy-ordering|Proxy/Delegate Ordering]]: Depends on VW context switching for determining which budget/inventory to consume
- [[budget-management|Budget Management]]: Might be organized by VW (per-VW per-brand budget)
- [[fulfillment-queue|Fulfillment Queue]]: Might organize orders by VW ownership

## Related Gaps

- [[gap-vw-concept|Gap W3-G1: Virtual Warehouse Concept Has No Salesforce Equivalent]]: Explicitly calls out that validation is needed before proceeding

## Related Assumptions

- **A-10:** All 95 Virtual Warehouses are actively used and need migration (assumption to be validated)
- **A-12:** Distributors are ship-to destinations only, not separate VW entities

## Resolution

**Status:** Open - Awaiting Procurement/Operations validation

**When resolved, document:**
- Count of active VWs (with non-zero inventory or recent activity)
- Usage patterns: ordering frequency, inventory turnover
- How VWs interact with proxy ordering and budget enforcement
- Whether VWs can be simplified or deferred without operational impact
- Link to production VW usage metrics or database query results

**Owner:** Procurement / Operations

---

## Validation Methodology

**Recommended approach:**

1. **Database Query:** Run query against MerchTank database:
   ```
   SELECT VW_ID, Owner, Lot_Number, Inventory_Count, Last_Order_Date, Last_Transfer_Date
   FROM Virtual_Warehouses
   WHERE Active = 1
   ORDER BY Inventory_Count DESC, Last_Order_Date DESC
   ```

2. **Usage Report:** Procurement team generates report of VW usage over past 12 months (inventory movement, orders placed by VW)

3. **Stakeholder Interview:** Meet with Procurement Lead to understand whether VW concept is essential or could be replaced with simpler account-based structure

**Deliverable:** Usage analysis document with:
- Count of active VWs (>0 inventory or activity in past 90 days)
- Top 10 VWs by activity
- Business process description: how are VWs used?
- Recommendation: essential (build Option 1) or can defer (Option 4)
