---
type: entity
client: boston-beer-company
status: active
category: system
created: 2026-04-06
updated: 2026-04-06
sources:
  - client-email-merchtank-feeder-systems-2026-04-06
tags:
  - financial-system
  - budget-management
  - enterprise-planning
  - email
---

# Anaplan — Entity Record

## Overview

**Anaplan** is Boston Beer Company's financial reporting and enterprise planning system. It is the **system of record for OPEX/brand budgets** — a critical discovery that contradicts the wiki's previous assumption that Oracle ERP held this role.

Client states (Finance department, 2026-04-06): "Anaplan — This is our BBC financial reporting system and is a widely used enterprise solution. We do NOT maintain our budgets for OPEX in SAP, it lives here."

## Key Characteristics

**System Properties:**
- **Type:** Enterprise planning and financial reporting platform
- **Vendor:** Anaplan (widely used enterprise solution; cloud-based connected planning platform)
- **Purpose:** OPEX budget management, financial reporting
- **Users:** Finance team, brand management
- **Criticality:** Business-critical (source of truth for all brand budgets)
- **Status:** Active

**Data Managed:**
- Brand-level OPEX budget allocations (Samuel Adams, Twisted Tea, Angry Orchard, Dogfish Head, etc.)
- Financial reporting and planning data
- Budget usage data (updated from MerchTank ~5x/year during LE cycles)

**Budget Flow:**
```
Anaplan (Budget SOR)
  |
  v
Brand budgets pulled → loaded into template
  |
  v
Template fed to MerchTank → populates budget allocations
  |
  v
MerchTank tracks usage (ordered, shipped, remaining)
  |
  v
Budget usage reporting pulled from MerchTank during LE cycles (~5x/year)
  |
  v
Anaplan updated with actual usage data
```

## Relationships

### Integration: [[merchtank|MerchTank]]
- **Relationship:** Budget allocation source → MerchTank; Budget usage reporting ← MerchTank
- **Direction:** Bidirectional (but asymmetric — allocations down, reporting up)
- **Data Exchanged:**
  - Inbound to MT: Brand budget allocations (via template)
  - Outbound from MT: Budget usage reporting (during LE cycles ~5x/year)
- **Mechanism:** Template-based (format unknown — could be CSV, Excel, manual, or API)

### Dependency: [[brand-budget-tracking|Brand Budget Tracking Feature]]
- Anaplan is the ultimate source of the budget data that drives this feature
- Salesforce must either integrate with Anaplan or replicate the template-based load process

### Dependency: [[budget-management-engine|Budget Management Engine Gap]]
- Resolution Option 3 (External Budget System Integration) should target Anaplan, not Oracle ERP

### Relationship: [[oracle-erp|Oracle ERP]]
- Oracle ERP's role in budget management is now unclear
- Oracle may still handle GL posting, invoice matching, and co-op billing
- But brand budget allocations originate in Anaplan, not Oracle

## Salesforce Migration Considerations

**Integration Options:**
1. **Anaplan API integration** — Anaplan has REST APIs; Salesforce could pull budget allocations directly
2. **Template replication** — Replicate the current template-based load process (Anaplan → template → Salesforce)
3. **Manual sync** — Finance team manually loads budgets into Salesforce (simplest but least automated)

**Key Questions:**
1. What is the template format used to load budgets from Anaplan to MerchTank? (CSV, Excel, API?)
2. How frequently are budgets loaded? (Annual? Quarterly? On-demand?)
3. Does Anaplan expose APIs that Salesforce could consume directly?
4. What are "LE cycles"? What triggers them (~5x/year)?
5. Should Salesforce replace MerchTank's role in the Anaplan ↔ MT bidirectional flow?
6. Does the Finance team want real-time budget sync or periodic batch loading?

## Notes

- **This entity was discovered via client email on 2026-04-06** — it was not previously identified in any meeting analysis
- The discovery that Anaplan (not Oracle) is the budget SOR has significant impact on the integration architecture — see contradiction notices on [[oracle-erp-integration|Oracle ERP Integration]], [[oracle-erp|Oracle ERP entity]], and [[brand-budget-tracking|Brand Budget Tracking]]
- Anaplan is a well-known enterprise planning platform with robust APIs — this is likely easier to integrate with than Oracle ERP
- The template-based loading mechanism suggests the current integration is semi-manual, which may be an opportunity to automate in the Salesforce migration
