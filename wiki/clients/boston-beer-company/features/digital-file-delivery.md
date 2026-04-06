---
type: feature
client: boston-beer-company
status: draft
category: custom-requests
decision: custom
effort: M
priority: P2
created: 2026-04-06
updated: 2026-04-06
sources:
  - /sessions/sweet-trusting-ride/mnt/Vendale-Agentics/BostonBeerCompany/meetings/03-custom-requests/analysis/gap-analysis-bbc-custom-requests-meeting.md
tags:
  - digital-file-delivery
  - creative-operations
  - automation
---

# Digital File Delivery

## Description

Currently, digital file delivery for custom creative requests is a fully manual, multi-application workflow spanning 4 systems (MerchTank, Adobe Illustrator, OneDrive, Outlook). After a proof is approved, designers manually export files from Illustrator, upload to OneDrive, copy sharing links, compose emails with standardized templates, and send to requestors. This workflow is error-prone and lacks automation. Salesforce integration offers an opportunity to consolidate this entire process into a single platform with automated file delivery.

## Current Implementation

**Current Workflow:**
1. Design completed in Adobe Illustrator
2. File exported with naming convention: RequestNumber_BrandCode_Description
3. File uploaded to OneDrive "Digital Files" folder
4. Sharing link copied from OneDrive
5. Email composed in Outlook with subject: "Digital file for MT#{order_number}-{line_item_id} ---- {BRAND} {PRODUCT_CODE} {SIZE} {DESCRIPTION}"
6. OneDrive link pasted into email body with standardized template
7. Email sent to requestor

**Business Rules:**
- Subject line format is critical for tracking
- Email template includes "print ready files" language
- Files shared via OneDrive links (not attachments)
- Multiple drafts composed in Outlook Drafts (batch preparation)
- Files organized in "Digital Files" OneDrive folder structure

**Current Technical Implementation:**
- Manual export from Adobe
- Manual OneDrive upload
- Manual email composition
- Email addresses extracted from MerchTank request records

**Systems Involved:**
- MerchTank (request data), Adobe Illustrator (design work), OneDrive (file storage), Microsoft Outlook (email)

## Target Implementation

Salesforce can automate this entire workflow with integrated file management, automated notifications, and digital asset delivery.

**Proposed Salesforce Architecture:**

1. **Salesforce Files Integration:**
   - Store approved proof files in Salesforce using ContentDocument/ContentVersion
   - Link files to Custom_Request__c record
   - Files automatically available for download from Salesforce

2. **Automated File Delivery Flow:**
   - When Proof status changes to "Approved", Record-Triggered Flow fires
   - Flow creates a new Salesforce File record or moves file to delivery folder
   - Flow generates a share link (ContentDistribution or simple file download link)
   - Flow composes email notification with:
     - Subject: Standardized format using request details
     - Body: Standardized template + file download link
     - Recipient: Requestor email from Custom_Request__c
   - Flow sends email via Flow Email Action

3. **Designer Handoff LWC:**
   - When designer marks proof as "Ready for Delivery"
   - Automatically triggers file preparation
   - Designer can override or confirm file details before sending

4. **Notifications:**
   - Requestor receives single, consolidated email from Salesforce
   - Attachment is Salesforce content link (not email attachment to avoid size limits)

## Gaps & Risks

**Gap DFD-G1: Multi-Application Workflow Consolidation**
- Severity: High
- Description: Current workflow requires 4 systems; Salesforce can handle all in one
- Impact: Automation opportunity; reduces manual work by ~80%
- Resolution: Salesforce Files + Flow automation
- Effort: M (2-3 weeks)

**Gap DFD-G2: Adobe Integration**
- Severity: Medium
- Description: Design work remains in Adobe; integration would require API or plugin
- Impact: Designers continue using Adobe; Salesforce integration handles file delivery only
- Resolution: No change to design workflow; focus on post-approval automation
- Effort: Not required for Phase 1

**Gap DFD-G3: OneDrive Replacement**
- Severity: Medium
- Description: Decision: Replace OneDrive with Salesforce Files, or integrate both?
- Impact: If replacing, requires migration of existing digital files
- Resolution: Salesforce Files for new files; OneDrive archive for legacy (if needed)
- Effort: Bundled with DFD-G1

## Dependencies

- [[custom-item-design-submission|Custom Item Design Submission]] (Proof approval trigger)
- [[salesforce-files|Salesforce Files]] for file storage
- [[email-notifications|Email Notifications]] framework

## Open Questions

1. Should historic digital files be migrated from OneDrive to Salesforce?
2. Are there file format or size restrictions beyond 50MB?
3. Should requestors have direct access to view/download files from Salesforce, or only via email?

## Evidence

**Meeting 3 (Custom Requests):**
- "A fully manual, multi-application workflow for delivering completed design files to requestors"
- "Entirely manual process spanning 4 applications (MerchTank, Illustrator, OneDrive, Outlook) with no automation"
- "Significant automation opportunity -- this is the single highest-value workflow to improve in migration"
- Multiple drafts in Outlook suggest batch preparation
