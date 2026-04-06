---
type: feature
client: boston-beer-company
status: draft
category: reporting
decision: custom
effort: M
priority: P1
created: 2026-04-06
updated: 2026-04-06
sources:
  - /sessions/sweet-trusting-ride/mnt/Vendale-Agentics/BostonBeerCompany/gap-analysis-batch-3-my-account.md
  - /sessions/sweet-trusting-ride/mnt/Vendale-Agentics/BostonBeerCompany/meetings/01-merchtank-overview/analysis/gap-analysis-sample-bbc-merchtank.md
tags:
  - order-history
  - reporting
  - analytics
---

# Order History and Analytics

## Description

Users require visibility into order history, status, and spending. MerchTank displays historical orders with filtering, sorting, and export to Excel. Finance team requires specialized co-op/billable reporting showing ship date, cost center, SKU, description, billable amount, and quantity ordered. Critical requirements include visibility into total budget, what was spent, and what was shipped.

## Current Implementation

**Order History View:**
- List of past orders filtered by wholesaler
- Status tracking: Pending vs. Shipped
- Order detail view with order information
- Ability to duplicate orders
- Ability to edit unshipped orders

**Reporting:**
- Built-in MerchTank reports (order usage, item sales summary)
- Automated Excel exports for procurement
- SQL Server reporting (VPN-dependent, observed failing)

**Critical Requirements:**
- Req #7: Visibility into total budget, what was spent, and what was shipped (once shipped, moves to spend column)
- Req #21: Historical spend and order status
- Req #31: Order history/status reporting for Finance
- Req #26: Co-op/Billable Reporting with: ship date, cost center, SKU, description, billable amount, QTY of POS ordered

## Target Implementation

1. **Order History LWC:**
   - Display all OrderSummary records for current buyer
   - Columns: Order Number, Date, Status, Total, Ship Date (if shipped)
   - Filtering: Date range, status, brand
   - Sorting: Default by date (newest first)
   - Pagination and lazy loading for performance

2. **Budget/Spend Dashboard:**
   - Custom LWC displaying budget summary:
     - Total Budget Allocated (by brand)
     - Amount Spent (sum of shipped orders)
     - Amount Not Yet Shipped (sum of open orders)
     - Remaining Balance
   - Visualization: Stacked bar chart or progress bars

3. **Order Detail with Reorder:**
   - Standard Order Detail page
   - Custom "Reorder" action to duplicate order
   - Edit capability for unshipped orders

4. **Finance Reporting:**
   - Custom report object `Order_Billing_View__c` (or query OrderItemSummary with related data)
   - Report fields: Order Number, Ship Date, Cost Center (from Account), SKU, Description, Billable Amount (including co-op), QTY Ordered, QTY Shipped, Co-op Status
   - Export to CSV/Excel via scheduled report

## Gaps & Risks

**Gap OHA-G1: Custom Budget/Spend Columns**
- Severity: High
- Description: Standard Order History doesn't show budget data; must be custom
- Impact: Users lose visibility into spending vs. allocation
- Resolution: Custom LWC with budget summary and spend calculations
- Effort: M

**Gap OHA-G2: Co-op/Billable Reporting**
- Severity: High
- Description: Finance requires specialized reporting that doesn't exist in standard Salesforce
- Impact: Finance team cannot reconcile co-op billing
- Resolution: Custom report type or Salesforce CRM Analytics dashboard
- Effort: M

**Gap OHA-G3: Reorder Functionality**
- Severity: Medium
- Description: Users can quickly duplicate past orders; requires custom LWC action
- Impact: Reorder is a convenience feature; not blocking but valuable for UX
- Resolution: Custom LWC action on Order Detail
- Effort: M

**Gap OHA-G4: Performance with Large Order Histories**
- Severity: Medium
- Description: Buyers with years of order history could create performance issues
- Impact: Loading all orders on page load is inefficient
- Resolution: Pagination, lazy loading, date range pre-filtering
- Effort: Bundled with OHA-G1

## Dependencies

- [[order-data-model|Order Data Model]] (OrderSummary)
- [[brand-budget-tracking|Brand Budget Tracking]] (spend calculations)
- [[rootstock-eap-integration|Rootstock Integration]] (invoice data for co-op reporting)

## Open Questions

1. What is the default sort order for order history? Most recent first?
2. How far back should order history go? Last 1 year? All time?
3. Should reorder ability be restricted to shipped orders only?
4. Are there additional report columns beyond the co-op/billable fields listed?
5. How frequently is the Finance report needed? Daily? Weekly? On-demand?

## Evidence

**Meeting 1 (MerchTank Overview):**
- "Users view past orders filtered by wholesaler, with status tracking (pending vs shipped)"
- "Users can view order details, duplicate orders, and edit unshipped orders"
- "Procurement relies on automated reports delivered as Excel exports"

**Batch 3 - My Account:**
- "Critical Req #7: Visibility into total budget, what was spent, and what was shipped. Once an order has been confirmed shipped, it moves to the spend column."
- "Critical Req #21: Historical spend and order status in MerchTank"
- "Critical Req #26: Co-Op/Billable Reporting for Accounting — must include: ship date, cost center, SKU info, description, billable amount, QTY of POS ordered"
- "Critical Req #31: Order history/status reporting for Finance"
