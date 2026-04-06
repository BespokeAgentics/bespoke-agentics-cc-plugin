---
type: feature
client: boston-beer-company
status: draft
category: admin
decision: custom
effort: M
priority: P1
created: 2026-04-06
updated: 2026-04-06
sources:
  - /sessions/sweet-trusting-ride/mnt/Vendale-Agentics/BostonBeerCompany/gap-analysis-batch-3-my-account.md
  - /sessions/sweet-trusting-ride/mnt/Vendale-Agentics/BostonBeerCompany/meetings/01-merchtank-overview/analysis/gap-analysis-sample-bbc-merchtank.md
  - client-email-merchtank-feeder-systems-2026-04-06
tags:
  - approvals
  - order-management
  - financial-controls
  - email
---

# Approval Workflows

## Description

Salesforce B2B Commerce supports approval workflows for orders that exceed spending thresholds or require authorization. BBC requires automated manager approval for orders when spend limits are exceeded. Spend limits are managed in "Sam Central" and must be integrated with Salesforce approval logic. This feature is critical for financial controls and governance.

## Current Implementation

**MerchTank Approach:**
- Spend limits (coworker approval thresholds) defined in **Sam Central** — BBC's legacy coworker database
- Sam Central contains: organizational hierarchy, sales geography hierarchy, coworker approval thresholds, and coworker-to-distributor mappings
- The organizational hierarchy is merged with the sales geography hierarchy and coworker-to-distributor mappings to generate a **cost center hierarchy** of which coworkers have access to which distributors (updated daily)
- When orders are submitted or approved, coworker approval thresholds are **looked up directly from Sam Central** (real-time lookup, not cached)
- Manager notification and approval workflow not clearly defined
- Automatic enforcement of spend limits at checkout

## Target Implementation

1. **Approval Workflow Configuration:**
   - Salesforce Approval Process or Record-Triggered Flow
   - When order total exceeds user's Sam Central spend limit:
     - Route to user's manager for approval
     - Can be approved or rejected
     - Approved orders proceed; rejected orders are cancelled

2. **Sam Central Integration:**
   - Custom Apex callout to Sam Central API
   - Retrieve spend limits for each user
   - Cache locally in Salesforce for performance

3. **Out-of-Office Proxy:**
   - Buyer Manager role can reassign approval authority during absence
   - Temporary delegation of approvals to another user

## Gaps & Risks

**Gap AW-G1: Sam Central Integration**
- Severity: High
- Description: Sam Central is now identified as BBC's legacy coworker database (per client email 2026-04-06). It holds org hierarchy, sales geography hierarchy, approval thresholds, and distributor mappings. Cost center hierarchy is updated daily. Approval thresholds looked up directly at order submit/approve time.
- Impact: Spend limit enforcement requires real-time API access to Sam Central (or periodic sync to Salesforce)
- Resolution: Determine Sam Central API availability (REST, SOAP, database), data contract for approval thresholds, and integration pattern (real-time callout vs. cached sync)
- Effort: TBD (depends on API availability)

**Gap AW-G2: Approval Workflow Design**
- Severity: Medium
- Description: Approval rules and escalation paths need clarification
- Impact: Approval workflow could be configured incorrectly
- Resolution: Define approval matrix with BBC
- Effort: M (workflow design and testing)

**Gap AW-G3: Out-of-Office Delegation**
- Severity: Medium
- Description: Buyer Managers must be able to reassign approvals during absence
- Impact: Without delegation, approvals could be blocked while manager is out
- Resolution: Custom LWC for temporary approval delegation
- Effort: M

## Dependencies

- [[sam-central-integration|Sam Central Integration]] (spend limit data)
- [[buyer-manager-role|Buyer Manager Role]] (approval authority)

## Open Questions

1. What is the Sam Central API contract for retrieving spend limits?
2. Are spend limits per user, per role, or per account?
3. How are approval escalations handled if manager doesn't respond?
4. How long does an out-of-office delegation last? Until manually cleared?
5. Can approvals be delegated to specific users, or to a group/queue?

## Evidence from Email: MerchTank Feeder Systems (2026-04-06)

Source: Client email — IT department notes on Sam Central
Date: 2026-04-06

Sam Central is now fully identified:
- **System**: Legacy coworker database
- **Contains**: Organizational hierarchy, sales geography hierarchy, coworker approval thresholds, coworker-to-distributor mappings (for distributors outside their own hierarchy)
- **Process**: Org hierarchy merged with sales geography + coworker-distributor mappings → generates cost center hierarchy (which coworkers access which distributors). Updated daily.
- **Approval thresholds**: Looked up directly from Sam Central when orders are submitted or approved (real-time, not cached)
- **Key insight**: Sam Central is a live dependency for the approval workflow, not just a data source — thresholds are fetched at order time

## Evidence

**Batch 3 - My Account:**
- "Critical Req #22: Automated manager approval on orders placed when spend limits are exceeded. Spend limits are set by company governance and live in Sam Central."
- "Critical Req #9: Out of Office Proxy — admin access to change approver. This requires the ability for a Buyer Manager to reassign approval authority during absence."
- "Map 'Sam Central' spend limit data to Salesforce for automated enforcement"
