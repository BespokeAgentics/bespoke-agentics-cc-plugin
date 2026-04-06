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
  - legacy-system
  - coworker-database
  - approval-thresholds
  - access-control
  - email
---

# Sam Central — Entity Record

## Overview

**Sam Central** is Boston Beer Company's legacy coworker database. It is the authoritative source for organizational hierarchy, sales geography hierarchy, coworker approval thresholds, and coworker-to-distributor mappings. It plays a critical role in MerchTank's access control and order approval workflows.

Previously referenced in wiki pages as "Sam Central (unknown system)" — this entity was fully identified via client email from the IT department on 2026-04-06.

## Key Characteristics

**System Properties:**
- **Type:** Legacy coworker database
- **Purpose:** User access control, organizational hierarchy, approval thresholds
- **Technology:** Unknown (legacy system; API availability TBD)
- **Users:** IT administrators (data management); indirectly used by all MerchTank users
- **Criticality:** Business-critical (access control and approval enforcement depend on it)
- **Status:** Active; daily data refresh for cost center hierarchy

**Data Managed:**
- **Organizational hierarchy** — BBC corporate org structure
- **Sales geography hierarchy** — Regional/territory structure for sales teams
- **Coworker approval thresholds** — Per-coworker spending limits for order approval
- **Coworker-to-distributor mappings** — Maps coworkers to distributors outside their own hierarchy

**Derived Data:**
- **Cost center hierarchy** — Generated daily by merging org hierarchy + sales geography hierarchy + coworker-to-distributor mappings. Determines which coworkers have access to which distributors.

**Key Behaviors:**
- Cost center hierarchy is **updated daily** (batch process)
- Approval thresholds are **looked up directly (real-time)** when orders are submitted or approved — not cached in MerchTank
- Coworker-to-distributor mappings enable access to distributors outside a coworker's own hierarchical chain

## Relationships

### Integration: [[merchtank|MerchTank]]
- **Relationship:** Access control and approval threshold provider
- **Data Exchanged:**
  - Cost center hierarchy (daily batch) → determines which coworkers see which distributors in MerchTank
  - Approval thresholds (real-time lookup at order submit/approve) → determines if order requires manager approval
- **Direction:** Outbound (Sam Central → MerchTank)
- **Frequency:** Daily (hierarchy) + Real-time (thresholds)

### Dependency: [[approval-workflows|Approval Workflows]]
- Approval thresholds stored in Sam Central are the foundation for order approval routing
- Salesforce must either integrate with Sam Central for real-time threshold lookup or sync thresholds periodically

### Dependency: [[buyer-user-management|Buyer User Management]]
- Sam Central's org hierarchy and distributor mappings determine user access patterns
- Migration to Salesforce requires replicating this access control model (Permission Sets, Buyer Groups, or custom logic)

### Dependency: [[buyer-account-model|Buyer Account Model]]
- The cost center hierarchy in Sam Central is the closest BBC has to an account hierarchy today
- This hierarchy should inform the Salesforce Buyer Account structure design

## Salesforce Migration Considerations

**Integration Required:**
1. **Cost center hierarchy sync** — Daily batch from Sam Central to Salesforce (determines user-to-account/distributor access)
2. **Approval threshold sync or real-time callout** — For order approval enforcement
3. **API discovery needed** — Sam Central's API capabilities are unknown; this is a prerequisite for integration design

**Key Questions:**
1. Does Sam Central expose a REST or SOAP API?
2. Can the cost center hierarchy be exported as a file (CSV, XML)?
3. What is the data model for approval thresholds? (Per-user amount? Per-role? Per-category?)
4. Can Sam Central be modified to push data to Salesforce, or must Salesforce pull?
5. Is Sam Central being replaced or modernized independently of the MerchTank migration?
6. Who is the technical owner of Sam Central within BBC IT?

## Notes

- Sam Central was previously described as an "unknown system" in wiki pages. The client email from IT on 2026-04-06 provided full identification.
- The real-time approval threshold lookup is a significant integration requirement — it means Sam Central is not just a data source but a live dependency at order time.
- The cost center hierarchy (updated daily) may be a candidate for Salesforce Buyer Account hierarchy design — should be discussed in the account hierarchy workshop.
