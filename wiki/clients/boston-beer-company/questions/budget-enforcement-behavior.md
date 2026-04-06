---
type: question
client: Boston Beer Company
status: open
priority: P1
category: feature-clarification
owner: Finance Team
created: 2026-03-16
updated: 2026-04-06
sources:
  - meetings/03-custom-requests/analysis/gap-analysis-bbc-custom-requests-meeting.md
  - meetings/02-virtual-warehouse-walkthrough/analysis/gap-analysis-bbc-vw-walkthrough.md
  - client-email-merchtank-feeder-systems-2026-04-06
tags:
  - budget-management
  - checkout
  - critical-design-decision
  - email
---

# Question: Budget Enforcement Behavior

## Question

**When a user attempts to add items to their cart that would exceed their remaining brand-level budget, does the system:**

A) **Hard stop:** Prevent the checkout and display an error message (order cannot be submitted when budget is exceeded)

OR

B) **Soft warning:** Display a warning message but allow the user to proceed with checkout (manager approval or manual override possible)

**What is the current behavior in MerchTank, and what is the desired behavior in Salesforce B2B Commerce?**

## Context

Budget enforcement is a **critical feature** that affects every merchandise order at Boston Beer Company. The [[gap-budget-enforcement|budget enforcement gap]] identified in Meeting 03 notes:

> "Severity: Critical — Hard stop vs soft warning fundamentally affects implementation (3-4 weeks vs 2-3 weeks). Business rule documentation required."

Current observations from [[meeting-02-virtual-warehouse|Meeting 02]]:

- The shopping cart displays per-brand budget tracking: "Available Budget" and "Current Total"
- Cart shows remaining balance after the cart total is calculated
- Users report the system "prevents overspending" during checkout
- The [[gap-brand-budget-enforcement|budget enforcement gap]] assumes a hard stop but notes the behavior is "unconfirmed"

From [[meeting-04-fulfillment|Meeting 04]], the fulfillment operator and finance team discussions did not clarify whether finance approvals can override budget blocks or if overspends must be prevented entirely.

This question blocks [[gap-budget-tracking-design|the entire budget object model design]] because:

- **Hard Stop:** Requires Apex cart validation (sfdc_checkout.CartValidation) that rejects cart submission if budget exceeded. Simple, strict enforcement. Estimated 3-4 weeks.
- **Soft Warning:** Requires additional Salesforce Approval Process, business rule configuration, and manager override workflow. Estimated 2-3 weeks plus ongoing approval management.
- **Hybrid (Hard Stop with Override):** Requires approval process coupled to cart validation. Most complex. Estimated 4-5 weeks.

## Impact if Unanswered

1. **Design Cannot Proceed:** The custom `Brand_Budget__c` object model and cart validation architecture depend on this decision.
2. **Scope Variance:** 1-2 weeks difference in development effort means timeline impact and resource allocation changes.
3. **Risk of Rework:** Building for hard stop when soft warning is required (or vice versa) forces redesign during development.
4. **User Experience Broken:** If enforcement behavior doesn't match business expectations, users will experience cart rejections they don't expect.
5. **Financial Control Risk:** If soft warning is implemented but hard stop is required, users could accidentally overspend brand allocations.

## Proposed Answer (if any)

Based on pattern observed in the current system, the most likely scenario is:

- **Proposed:** Hard stop enforcement at checkout (prevent submission when budget exceeded)
- **Rationale:** MerchTank description stated "prevents overspending"; cart displays remaining budget; no evidence of manager override workflows in observed workflows
- **Confidence:** Medium — Needs direct confirmation from Finance and Procurement teams

**Alternative possibility:** Hard stop with manager approval workflow (most common in enterprise procurement systems)

## Related Features

- [[budget-management|Brand-Level Budget Enforcement]]: The core feature that this question clarifies
- [[shopping-cart-budget|Shopping Cart with Budget Validation]]: Uses the enforcement behavior to validate line items
- [[checkout-workflow|Checkout Workflow]]: Cart validation occurs at checkout submission
- [[proxy-ordering|Proxy/Delegate Ordering]]: Procurement staff ordering for sales reps must respect the same budget limits
- [[program-windows|Program Order Windows]]: Time-gated catalogs may interact with budget enforcement (e.g., time-limited budget allocations)

## Related Gaps

- [[gap-brand-budget-enforcement|Gap W2-G1: Per-Wholesaler/Per-Brand Budget Tracking]]: Cannot complete resolution options without understanding enforcement behavior
- [[gap-budget-enforcement-checkout|Gap W4-G2: Budget Enforcement at Checkout]]: Blocks complete specification of validation logic

## Resolution

**Status:** Open - Awaiting client confirmation

**When resolved, document:**
- The confirmed enforcement behavior (hard stop / soft warning / hybrid)
- Any approval workflows that exist in current system
- Role-based differences (e.g., do procurement staff have different rules than sales reps?)
- Manager override capabilities and approval SLAs
- Financial audit requirements around budget overages
- Link to decision record in [[04-fulfillment-demo|Meeting 04]] or subsequent stakeholder interviews

**Owner:** Finance Team (primary) with Procurement Team and Business Sponsor review

---

**Follow-up Questions:**
- Are there cases where budget limits can be exceeded with manager approval? (If yes, soft warning + approval)
- Does the current MerchTank system allow any overages at all, or is it a hard technical block?
- Are there different enforcement rules for different user roles (e.g., procurement staff vs sales reps)?
- What happens to an order if it's submitted during a budget overage state?

## Evidence from Email: MerchTank Feeder Systems (2026-04-06)

Source: Client email — IT department notes
Date: 2026-04-06

**Relevant to approval thresholds:**
- Sam Central contains **coworker approval thresholds**
- When orders are submitted or approved, coworker approval thresholds are **looked up directly from Sam Central** (real-time, not cached)
- This confirms that approval thresholds are external to MerchTank and require integration with Sam Central
- **Note**: This is about order approval thresholds (spend limits per coworker), which may be distinct from brand budget enforcement. Both must be considered in the approval workflow design.
