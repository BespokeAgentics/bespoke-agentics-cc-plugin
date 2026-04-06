---
type: meeting
client: Boston Beer Company
meeting-date: 2025-12-09
attendees: Boston Beer Finance Leadership
recording-path: meetings/05-finance-workflow/source/
transcript-path: null
pipeline-outputs: null
created: 2026-03-16
updated: 2026-03-16
sources: []
tags:
  - finance
  - budget-management
  - unprocessed
---

# Meeting: Prioritize Finance MT Requirements

## Summary

**⚠️ UNPROCESSED:** This meeting has been recorded as raw MP4 only. Pipeline processing (frame extraction, transcript analysis, gap analysis, and client elicitation) has not yet been completed. The video recording exists but requires:

1. Frame extraction and OCR analysis
2. Audio transcript generation
3. Feature inventory and workflow mapping
4. Gap analysis against Salesforce capabilities
5. Integration assessment with finance systems

This page serves as a placeholder to indicate the meeting exists in the repository and needs to be prioritized for processing.

## Known Context

- **Recording Date:** December 9, 2025
- **Topic:** Finance team requirements for MerchTank migration
- **Attendees:** Boston Beer Finance Leadership (specific names/roles to be documented)
- **Expected Coverage:** Budget allocation models, period management, co-op billing splits, financial reporting, Oracle ERP integration, invoice generation

## Critical Finance Topics Likely Covered

Based on earlier meetings, this finance walkthrough probably addresses:

- **Budget Management:** Initial allocation processes, period structure (annual/quarterly/rolling?), budget resets
- **Co-op Billing:** Wholesaler cost-sharing logic, split calculations, invoice generation
- **Financial Reporting:** Automated reports, Excel exports, reconciliation processes
- **Oracle ERP Integration:** Budget sync direction, invoice creation, account code mapping
- **Role-Based Access:** Finance team permissions in MerchTank and planned Salesforce migration
- **Audit & Compliance:** Financial control requirements, change tracking, approval workflows

## Next Steps

### Processing Pipeline

1. **[Content Analysis Team]:** Extract frames and generate OCR transcript - Due [Week 1]
2. **[Gap Analysis Team]:** Produce comprehensive gap-analysis-finance-workflow.md - Due [Week 2]
3. **[Client Elicitation Team]:** Generate client-elicitation document with finance-specific questions - Due [Week 2]
4. **[Architecture Team]:** Update budget and billing gap definitions based on finance walkthrough - Due [Week 3]

### Immediate Questions for Finance Team

- **Budget Rule Complexity:** Simple annual allocation with decrement, or complex accruals/rollovers?
- **Period Structure:** Annual, quarterly, rolling, per-wholesaler, per-region?
- **Co-op Split Logic:** How are wholesaler invoices calculated from orders?
- **Oracle Integration:** What is the system of record for budgets (Oracle or MerchTank)?
- **Invoice Generation:** Who generates invoices and what triggers them?
- **Financial Reporting:** What reports are business-critical?
- **Audit Requirements:** Change tracking, approval workflows, compliance standards?

## Placeholder Details

| Detail | Status |
|--------|--------|
| Recording | ✅ Available at meetings/05-finance-workflow/source/*.mp4 |
| Transcript | ⏳ Pending pipeline processing |
| Gap Analysis | ⏳ Pending pipeline processing |
| Client Elicitation | ⏳ Pending pipeline processing |
| Confluence Export | ⏳ Pending pipeline processing |
| Estimated Impact | HIGH -- Budget management is critical to every transaction in MerchTank |

---

**Status:** STUB - Awaiting full pipeline processing
**Priority:** HIGH - Finance requirements block multiple architectural decisions
**Link to Index:** See /sessions/sweet-trusting-ride/mnt/Vendale-Agentics/BostonBeerCompany/INDEX.md for meeting inventory
