---
type: question
client: Boston Beer Company
status: open
priority: P1
category: technical-feasibility
owner: IT / ERP Team
created: 2026-03-25
updated: 2026-03-25
sources:
  - meetings/04-fulfillment-demo/analysis/gap-analysis-boston-beer-company-fulfillment-demo.md
  - meetings/04-fulfillment-demo/analysis/client-elicitation-boston-beer-company.md
tags:
  - integration
  - order-intake
  - blocking-architectural-decision
---

# Question: Upstream Order Batching System Identity

## Question

**What is the upstream system that batches and sends orders to MerchTank after 5:00 PM daily?**

Specifically:
1. What is the system name and vendor? (e.g., SAP, Oracle, custom application, middleware)
2. What technology stack does it use? (e.g., .NET, Java, cloud-based, on-premise)
3. What APIs or data exchange protocols does it support? (e.g., REST, SOAP, EDI, file-based)
4. How is the batch currently transmitted to MerchTank? (e.g., API call, database push, file upload, message queue)
5. What team owns this system, and who can discuss architecture/modification?
6. What is the SLA for batch delivery (always by 5 PM, or variable)?

## Context

From [[meeting-04-fulfillment|Meeting 04 - Fulfillment Demo]], the fulfillment operator described:

> "Daily batch at 5:00 PM delivers orders from upstream system; 16-hour delay before operator receives work queue (typical for Brew Hub/intranet check at 9 AM next day)"

**Why This Blocks Design:**

This is identified as **P0 Design Blocker** in the fulfillment client elicitation because:

1. **Integration Architecture Depends On It:** The entire order intake integration to Salesforce B2B Commerce cannot be designed without knowing:
   - Whether the upstream system has a documented API (favors direct integration via MuleSoft or Apex callouts)
   - Whether it sends files or streams data (favors file-based import via SFTP)
   - Whether it can be modified to increase batch frequency or switch to real-time (affects order latency in new system)

2. **Effort Estimate Variance:**
   - **Known, well-documented API:** 40-50 hours (MuleSoft connector design)
   - **Unknown or file-based system:** 60-80+ hours (discovery, custom file parsing, fallback approaches)

3. **Timeline Impact:**
   - If the upstream system can be modified to support real-time or hourly batches, order latency improvements are possible (currently 16 hours from batch to operator awareness)
   - If the upstream system is rigid, the 5 PM batch constraint persists regardless of Salesforce implementation

4. **Technology Stack Decisions:**
   - Determines whether MuleSoft is the right middleware choice
   - Affects ERP integration strategy
   - Influences whether custom Apex direct callouts are viable

## Impact if Unanswered

1. **Cannot Design Integration Architecture:** Order intake integration is the foundation for all downstream fulfillment workflows. Without knowing the upstream system, the integration pattern cannot be specified.
2. **Fallback to Inefficient Approach:** Default approach would be file-based CSV import via SFTP (low confidence, manual process).
3. **Risk of Scope Creep:** If the upstream system is complex (multi-vendor, EDI, legacy mainframe), scope could expand significantly.
4. **Latency Remains:** If improvements to batch timing are desired, the upstream system must be willing/able to modify its output frequency.
5. **Parallel Development Risk:** Integration team cannot start MuleSoft connector development until the upstream system is identified.

## Proposed Answer (if any)

**Most Likely Scenarios Based on Context:**

1. **ERP Module (Probability: High)** - The upstream system is likely an Oracle or SAP module (Finance, Supply Chain, or custom integration layer) that orchestrates order batching. Oracle was observed in IT team browser tabs during [[meeting-03-custom-requests|Meeting 03]].

2. **Custom Middleware (Probability: Medium)** - BBC may have built custom integration middleware to stage orders from various source systems before batching to MerchTank.

3. **File-Based Process (Probability: Low)** - Less likely given the structured 5 PM timing; suggests automated batch job rather than manual file drop.

**Evidence Supporting ERP Module:**
- Oracle observed in IT environment (Meeting 03)
- Budget sync mentioned as critical integration (Meeting 04)
- Co-op billing complexity suggests finance system involvement
- 5 PM batch timing suggests scheduled job (ERP-native capability)

**Confidence: Low** — Requires direct confirmation from IT/ERP team

## Related Features

- [[order-intake|Order Intake Batch]]: The exact feature that receives batched orders from upstream
- [[batch-import|Batch Import Mechanism]]: How the batch is technically ingested into Salesforce
- [[fulfillment-queue|Operator Queue Management]]: Downstream of batch import; uses order data from upstream

## Related Gaps

- [[gap-batch-import|Gap: Batch Import Mechanism]]: Cannot close until upstream system identity is known

## Related Decisions

- **D-02 (Open Questions, Meeting 04):** Order batching model (keep daily, micro-batch, near-real-time) depends on upstream system flexibility
- **Decision: Middleware Selection** - MuleSoft vs direct Apex vs file-based depends on upstream API availability

## Resolution

**Status:** Open - Awaiting IT/ERP team confirmation

**When resolved, document:**
- System name, vendor, technology (API/database/file)
- Current batch transmission mechanism and SLA
- Available APIs or integration endpoints
- Contact name and team for technical discussions
- Feasibility of increasing batch frequency (hourly, real-time) if desired
- Link to technical documentation (API spec, EDI format, etc.)

**Owner:** BBC IT / ERP Team

---

## Next Steps

1. **[IT Leadership]:** Identify the upstream order batching system owner and technical lead
2. **[IT Integration Team]:** Schedule working session with upstream system team to review architecture, APIs, and modification feasibility
3. **[Salesforce Architect]:** Prepare API discovery checklist for the kick-off call
4. **[MuleSoft Team]:** Prepare to evaluate whether a pre-built connector exists (Salesforce AppExchange, MuleSoft Anypoint Connectors)
