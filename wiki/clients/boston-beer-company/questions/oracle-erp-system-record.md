---
type: question
client: Boston Beer Company
status: open
priority: P1
category: business-rule
owner: Finance / IT
created: 2026-03-16
updated: 2026-04-06
sources:
  - meetings/02-virtual-warehouse-walkthrough/analysis/gap-analysis-bbc-vw-walkthrough.md
  - meetings/03-custom-requests/analysis/gap-analysis-bbc-custom-requests-meeting.md
  - client-email-merchtank-feeder-systems-2026-04-06
tags:
  - budget-management
  - erp-integration
  - oracle
  - anaplan
  - data-architecture
  - email
---

# Question: Is Oracle ERP the System of Record for Budgets?

## Question

1. **Is Oracle Financials/ERP Cloud the system of record for brand-level budget allocations?**
2. **How are budgets initially loaded into MerchTank?** (Manual upload, API sync from Oracle, automated nightly job?)
3. **Who manages budget allocations and period management?** (Finance team in Oracle, IT in MerchTank, shared?)
4. **If budgets are synced from Oracle, what is the refresh cadence?** (Real-time, daily, monthly?)
5. **Does MerchTank ever write budget data back to Oracle?** (Co-op splits, consumed amounts, invoicing?)

## Context

This question directly impacts the [[gap-brand-budget-enforcement|budget enforcement architecture]] design decision:

**Observation from meetings:**
- Oracle was visible in IT team browser tabs during [[meeting-03-custom-requests|Meeting 03]]
- Co-op billing logic was mentioned as complex (finance team involvement)
- Budget rules unconfirmed (simple annual decrement vs complex accruals)
- Budget sync with Oracle mentioned as critical integration need in [[meeting-04-fulfillment|Meeting 04]]

**Why This Matters:**

- **If Oracle is system of record:** Salesforce B2B Commerce requires inbound API integration to sync budgets daily/hourly, validate consumption against Oracle amounts, and potentially write back co-op splits or consumed amounts. **Integration effort: 6+ weeks (MuleSoft + Oracle connector + testing)**
- **If MerchTank is system of record:** Budgets are managed in MerchTank SQL Server, migrated to Salesforce as initial load, and manually adjusted. **Simpler approach; effort: 2-3 weeks**
- **If hybrid:** Portions of budget logic in Oracle, portions in MerchTank, requires understanding the boundary

**Impact on Architecture:**

| Scenario | Budget Data Source | Salesforce Approach | Integration Effort | Risk |
|----------|-------------------|--------------------|--------------------|------|
| Oracle system of record | Oracle Financials | Inbound API sync + validation | 6+ weeks | High - Oracle API complexity |
| MerchTank system of record | SQL Server | Data migration + manual refresh | 2-3 weeks | Low - known data source |
| Hybrid (Oracle allocations, MerchTank tracking) | Both | Sync allocations from Oracle, track consumption in Salesforce | 4-5 weeks | Medium - dual reconciliation |

## Impact if Unanswered

1. **Budget Object Model Design Blocked:** Whether to build custom Budget__c objects with Oracle sync, or simple denormalized budget fields depends on data source
2. **Integration Architecture Blocked:** Oracle integration is one of the highest-effort integration workstreams (estimated 20-35 weeks total for all integrations)
3. **Co-op Billing Logic Unclear:** Co-op splits (wholesaler pays X%, BBC pays Y%) may be calculated/stored in Oracle or in Salesforce
4. **Reconciliation Strategy Undefined:** How do we validate that Salesforce budget consumption matches Oracle records?
5. **Invoice Generation Path Blocked:** Invoicing to wholesalers (co-op portion) likely requires Oracle ERP; unclear if that's in-scope

## Partial Resolution — 2026-04-06

**Answer (from client email, Finance department):**

**Anaplan is the system of record for OPEX/brand budgets — NOT Oracle, NOT SAP.**

Client states: "Anaplan — This is our BBC financial reporting system and is a widely used enterprise solution. We do NOT maintain our budgets for OPEX in SAP, it lives here. Brand budgets get pulled from Anaplan and loaded into a template. This template gets fed to MT to populate the budgets. Reporting on budget usage gets pulled from MT during our LE cycles (about 5x per year) and Anaplan gets updated."

**Budget flow**: Anaplan → template → MerchTank (allocations inbound); MerchTank → Anaplan (usage reporting ~5x/year during LE cycles)

**Remaining unknowns:**
1. What is the template format? (CSV, manual, API?)
2. Does Oracle ERP still play a role in budget reconciliation, GL posting, or invoice matching?
3. What are "LE cycles" and what triggers them?
4. Does Anaplan expose APIs for integration with Salesforce?

**Confidence: High** — Direct client statement from Finance department

**Source**: client-email-merchtank-feeder-systems-2026-04-06

---

## Previous Proposed Answer (SUPERSEDED)

~~**Most Likely: Oracle is System of Record**~~

~~**Rationale:**~~
~~- Standard enterprise practice: Finance systems (Oracle) are system of record for budget allocations~~
~~- Oracle visible in IT environment suggests it's already integrated with MerchTank~~
~~- Co-op billing complexity suggests finance system involvement~~
~~- Budget period management (annual rollover) typically in ERP systems~~

~~**Confidence: Medium** — Oracle presence + budget complexity suggest this, but requires confirmation~~

**This proposed answer was incorrect.** The client has confirmed Anaplan is the budget SOR.

## Related Features

- [[budget-management|Brand-Level Budget Enforcement]]: Depends on knowing where budgets originate
- [[co-op-billing|Co-op Billing]]: Likely involves Oracle for invoice generation and wholesaler tracking
- [[order-history|Order History]]: May need to sync completed order data back to Oracle for financial reconciliation

## Related Gaps

- [[gap-oracle-integration|Gap: Oracle ERP Integration]]: Severity High - Cannot finalize integration architecture until budget sync direction is confirmed

## Related Decisions

- **Decision: Build Custom Budget Objects vs Simple Fields** - System of record determines data architecture
- **Decision: MuleSoft Implementation Timeline** - Oracle integration timing depends on this question

## Resolution

**Status:** Open - Awaiting Finance/IT confirmation

**When resolved, document:**
- Whether Oracle Financials is system of record for budgets
- Current data sync mechanism (if any) between Oracle and MerchTank
- Budget period structure (annual, quarterly, rolling) and management process
- Co-op split calculation logic (where does it occur?)
- Invoice generation process and system of record
- Required budget fields for Salesforce migration
- Link to Oracle technical documentation for budget modules

**Owner:** Finance Team (primary) with IT / ERP Team supporting

---

## Related Questions

- [[q-oracle-identity|Oracle ERP System Confirmation]]: Confirm Oracle is the ERP; explore SAP/NetSuite/custom alternatives
- [[q-coop-split-logic|Co-op Split Logic]]: How are wholesaler cost shares calculated?
- [[q-mulesoft-license|MuleSoft Licensing]]: Is MuleSoft available for Oracle integration?
