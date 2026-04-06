---
type: question
client: Boston Beer Company
status: open
priority: P1
category: scope-decision
owner: IT Procurement / Sponsor
created: 2026-03-25
updated: 2026-03-25
sources:
  - meetings/03-custom-requests/analysis/gap-analysis-bbc-custom-requests-meeting.md
  - meetings/04-fulfillment-demo/analysis/gap-analysis-boston-beer-company-fulfillment-demo.md
tags:
  - salesforce-licensing
  - order-management
  - fulfillment-architecture
  - budget-impact
---

# Question: Should BBC License Salesforce Order Management?

## Question

**Will Boston Beer Company license Salesforce Order Management (OMS), or will the fulfillment and order tracking functionality be built using custom Salesforce objects on B2B Commerce?**

This decision impacts:
1. **Fulfillment workflow implementation** (Salesforce OMS vs custom objects)
2. **Returns & Credits handling** (OMS natively supports; custom requires building)
3. **Shipment tracking & status management** (OMS vs custom fulfillment engine)
4. **Total cost of implementation** (licensing + development)
5. **Long-term maintenance burden** (OOTB OMS vs custom code)

## Context

**Fulfillment Workflow Requirements from [[meeting-04-fulfillment|Meeting 04 - Brewery Fulfillment Demo]]:**

- Daily order intake batch from upstream system
- Two-touch fulfillment process (MerchTank review → UPS WorldShip label generation)
- Operator queue management with order status tracking
- UPS shipping integration (WorldShip → API)
- Tracking number management and shipment linking
- Multi-location support (Milton Brewery confirmed; other locations unknown)
- Returns & Credits processing (scope unclear; modules observed but not demonstrated)

**Two Architecture Options:**

| Aspect | Salesforce OMS | Custom Objects (B2B Commerce) |
|--------|---|---|
| **Cost (Licensing)** | $500-2,000/month (depends on transaction volume) | $0 (included in B2B Commerce) |
| **Implementation (Dev)** | M effort (2-3 weeks configuration) | L effort (4-6 weeks custom objects + LWCs) |
| **Fulfillment Features** | Native support (order → shipment → tracking) | Custom build required |
| **Returns & Credits** | Native support | Custom build required |
| **Multi-location Support** | Built-in (handles 1-many locations easily) | Custom build required if locations have different workflows |
| **Maintenance Burden** | Low (OOTB product) | High (custom code maintenance) |
| **Long-term Cost** | Higher licensing, lower support | Lower licensing, higher support |
| **Timeline Impact** | Faster (use OOTB OMS) | Slower (custom development) |

## Impact if Unanswered

**Budget Impact:**
- **OMS:** ~$12K-24K/year licensing + M effort (2-3 weeks)
- **Custom:** $0 licensing + L effort (4-6 weeks)
- **Difference:** OMS costs $12K-24K more annually but saves 1-3 weeks of dev time

**Scope Impact:**
- **OMS:** Returns & Credits automatically supported (good if in-scope)
- **Custom:** Returns & Credits require additional custom development if needed (2-3 weeks)

**Timeline Impact:**
- **OMS:** Faster fulfillment workflow implementation
- **Custom:** Longer fulfillment development; may delay Phase 3 timeline

**Risk Impact:**
- **OMS:** Proven, tested fulfillment engine; lower risk of bugs
- **Custom:** New code; higher risk of fulfillment logic errors

## Proposed Answer (if any)

**Most Likely Decision: Do NOT License OMS in Phase 1**

**Rationale:**
1. **Unknown Location Count:** [[q-fulfillment-locations|Meeting 04]] identified that only Milton Brewery was demonstrated. If BBC operates only 1-2 fulfillment locations, custom objects are simpler than OMS.
2. **Lightweight Approach Recommended:** Client elicitation from Meeting 04 states: "Lightweight custom-object approach recommended pending fulfillment location count validation"
3. **Returns/Credits Out of Scope:** Returns/Credits modules were never demonstrated, suggesting they may not be Phase 1 priority
4. **Budget Constraints:** Cost avoidance ($12K-24K/year) may favor custom approach if business case isn't strong
5. **Phased Approach:** Can defer OMS to Phase 2/3 if fulfillment needs expand

**Alternative Decision: License OMS if Multiple Locations Confirmed**

**Rationale:**
- If [[q-fulfillment-locations|fulfillment locations]] exceed 3-4 locations with different workflows, OMS complexity justifies licensing cost
- Returns & Credits become more important with multi-location setup
- OMS better handles complex routing logic across multiple fulfillment centers

**Confidence: Medium** — Depends on [[q-fulfillment-locations|location count question]] being answered first

## Related Features

- [[fulfillment-queue|Operator Queue Management]]: Requires either OMS queue functionality or custom LWC
- [[shipment-status|Shipment Status Tracking]]: OMS natively supports; custom requires Shipment__c object
- [[returns-credits|Returns & Credits Processing]]: OMS has native support; out-of-scope for custom approach

## Related Gaps

- [[gap-fulfillment-dashboard|Gap: Fulfillment Dashboard]]: Severity Medium - Custom LWC required either way
- [[gap-returns-credits|Gap: Returns & Credits Unobserved]]: Cannot size scope until scope is confirmed

## Related Decisions

- **Decision: Lightweight vs Full OMS Architecture** - Depends on [[q-fulfillment-locations|location count]] answer
- **Decision: Phase 1 vs Phase 2 for Returns/Credits** - OMS makes Phase 1 Returns easier; custom approach favors Phase 2 deferral

## Related Questions

- [[q-fulfillment-locations|Fulfillment Location Count]]: Directly impacts OMS decision (1-2 locations → custom is fine; 3+ locations → OMS may be justified)
- [[q-returns-credits-scope|Returns/Credits In Scope]]: If in-scope for Phase 1, OMS is more attractive

## Resolution

**Status:** Open - Awaiting IT Procurement / Business Sponsor decision

**When resolved, document:**
- OMS licensing decision and justification
- If OMS is licensed: configuration approach and implementation timeline
- If custom objects: detailed custom object model for fulfillment (Order → Shipment → TrackingEvent)
- Returns & Credits handling approach (OMS vs custom vs deferred)
- Total cost of ownership (licensing + dev + support)
- Link to licensing agreement (if applicable)

**Owner:** IT Procurement (licensing authority) with Business Sponsor (business case) and Salesforce Architect (technical impact)

---

## Recommended Next Steps

1. **[Business Sponsor]:** Confirm fulfillment location count and workflow complexity
2. **[IT Procurement]:** Obtain Salesforce OMS licensing quote and compare to custom development cost
3. **[Business Sponsor]:** Confirm whether Returns & Credits are Phase 1 scope
4. **[Salesforce Architect]:** Prepare two implementation proposals:
   - **Proposal A (OMS):** Architecture diagram, configuration checklist, timeline
   - **Proposal B (Custom Objects):** Object model (Order, Shipment, TrackingEvent), LWC requirements, timeline
5. **[Finance]:** Cost comparison analysis (licensing vs custom dev vs hybrid)
6. **[Decision Meeting]:** Present both approaches and make a recommendation to business stakeholders

---

## Cost Comparison Template

| Item | Custom Objects | Salesforce OMS |
|------|---|---|
| **Licensing (annual)** | $0 | $12K-24K (est.) |
| **Dev (hours)** | 160-240 | 40-60 |
| **Dev (weeks @ 40h/wk)** | 4-6 weeks | 1-1.5 weeks |
| **Maintenance (annual)** | High (ongoing custom code) | Low (OOTB product) |
| **Phase 1 Timeline Impact** | -4-6 weeks for fulfillment | -1-1.5 weeks for fulfillment |
| **Returns/Credits Support** | Requires additional custom build (2-3 weeks) | Natively supported |
| **Multi-location Complexity** | High (custom routing rules) | Low (OOTB multi-location) |
| **Phase 2+ Upgrade Path** | Can migrate to OMS later (effort TBD) | N/A |
| **Total Phase 1 Cost** | Dev labor cost (~$16K-24K @ $100/hr) | Dev labor (~$4K-6K) + Licensing (~$1K) = $5K-7K |
| **Net 3-Year Cost** | Dev + Support (~$24K + ongoing) | Dev + Licensing (~$40K) |
