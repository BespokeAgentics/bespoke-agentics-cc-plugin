---
type: feature
client: boston-beer-company
status: draft
category: custom-requests
decision: custom
effort: XL
priority: P1
created: 2026-04-06
updated: 2026-04-06
sources:
  - /sessions/sweet-trusting-ride/mnt/Vendale-Agentics/BostonBeerCompany/meetings/01-merchtank-overview/analysis/gap-analysis-sample-bbc-merchtank.md
  - /sessions/sweet-trusting-ride/mnt/Vendale-Agentics/BostonBeerCompany/meetings/03-custom-requests/analysis/gap-analysis-bbc-custom-requests-meeting.md
  - client-email-merchtank-feeder-systems-2026-04-06
tags:
  - custom-requests
  - creative-operations
  - design-workflow
  - email
---

# Custom Item Design Submission

## Description

MerchTank's custom item design workflow (Items From Scratch / IFS) allows requestors to submit specifications for custom POS merchandise items that do not exist in the standard catalog. Requestors provide detailed item specifications (dimensions, materials, branding), select a designer, and specify delivery method (digital or physical). The system routes requests to creative operations for design and proofing. This is a core value proposition for BBC's merchandise offering and differentiates the platform from a standard ordering system.

## Current Implementation

**User Workflow:**
1. User navigates to "Items From Scratch" or "Custom Design" program
2. Fills out multi-field customization form with two panels:
   - **Left Panel (Item Specifications):** Height (inches), Width (inches), Material, Shape, Part By Reference (link to existing branding assets), Related Website
   - **Right Panel (Proof Management):** Designer assignment, Delivery Method (Digital Proof / Digital Email), Need-By Date, Proof Required checkbox, Budget Approval
3. Submits request with request number auto-generated (format: NNNNN-YYYYMMDDNN)
4. System routes to assigned designer
5. Designer works in Adobe Illustrator, exports files at print quality (300 ppi, CMYK)
6. Proofs uploaded via drag-and-drop modal
7. Approval workflow with proof review, approval/decline, posting decision
8. Requestor receives email notification with approved proof

**Business Rules:**
- Request numbers follow pattern NNNNN-YYYYMMDDNN (e.g., 83106-26400571)
- Categories assigned (e.g., "Everyday")
- Rush priority available with surcharge ("Rush (+$__)")
- Multiple file formats supported for logo/reference: doc, docx, xls, xlsx, ppt, pptx, png, jpg, psd, ai, eps, pdf (max 50MB)
- Designer assignment couples designer identity with delivery method (e.g., "Digital Then -- Jason Krok")
- Need-by dates influence feasibility calculation
- Proofs can be posted even without approval (requires explicit confirmation)

**Current Technical Implementation:**
- Two-panel form in MerchTank web UI
- Custom request records stored in database
- File upload handling with 50MB max size
- Designer routing logic (manual dropdown selection)
- Proof upload and approval workflow with status tracking
- Email notifications from no_return@bostonbeer.com

**Systems Involved:**
- MerchTank (form, workflow, storage), Adobe Creative Suite (design work), OneDrive (file storage), Microsoft Outlook (email notifications and vendor quote requests)
- **WorkFront** — Project management system where asset intake happens and POS workflow gets managed. Tasks in WorkFront collect all needed info for item setup in MT. Brand coworker goes to WF to get proof, downloads thumbnail image, uploads to MT in .jpg format.
- **Outlook** — Creative Team and Co-ops use Outlook to request quotes from approved vendors (Kirkwood, Six Strings, etc.). Quote info entered into MT for sales rep review/approval. POS proofs and supporting images attached at this stage.
- **Vendor Portals (various)** — Creative Team/Co-ops pull approved order details from MT, enter into vendor portals to process and ship POS materials. Also used for tracking info, recorded back in MT.

## Target Implementation

Salesforce B2B Commerce does not have a native custom product design/proofing workflow. This requires significant custom development.

**Proposed Salesforce Architecture:**

1. **Custom Objects:**
   - `Custom_Request__c`: Master request record
     - Fields: Request_Number__c (External ID), Requestor__c (User lookup), Designer__c (User lookup), Category__c, Priority__c, Need_By_Date__c, Delivery_Method__c (picklist: Digital Proof, Digital Email, Physical Ship), Budget_Approval__c, Status__c, Price__c, Created_Date__c
   - `Custom_Item_Spec__c`: Item specification details (master-detail to Custom_Request__c)
     - Fields: Height__c, Width__c, Material__c, Shape__c, Part_By_Reference__c, Related_Website__c, Color__c, Size__c
   - `Proof__c`: Proof files and approval workflow (master-detail to Custom_Request__c)
     - Fields: Proof_Status__c (Uploaded, Under Review, Approved, Declined), Uploaded_Date__c, Uploaded_By__c, File_ID__c (ContentDocument lookup), Preview_Available__c
   - `Proof_Approval__c`: Approval records for audit trail
     - Fields: Proof__c, Approver__c, Approval_Date__c, Action__c (Approved, Declined, Override Posted), Comments__c

2. **Lightning Web Components:**
   - `c-custom-request-form`: Two-panel form matching current UX
     - Panel 1: Item specifications input fields
     - Panel 2: Designer selector, delivery method, need-by date
     - File upload for logo/reference (supports required file formats)
   - `c-proof-upload-modal`: Drag-and-drop proof upload
     - Supports PDF, PNG, image formats
     - Thumbnail preview display
     - Multiple file upload
   - `c-proof-approval-workflow`: Proof approval LWC
     - Display uploaded proof with preview
     - Approve/Decline buttons
     - "Post Unapproved" override with confirmation dialog
   - `c-custom-request-dashboard`: Monitoring dashboard for Creative Operations
     - List view with bar chart showing request volume distribution
     - Status filters (Pending, Approved, Bid Request, Sent To Print, etc.)
     - Sub-tabs for different fulfillment stages (Admin, To Print, Shipping)

3. **Apex Classes:**
   - `CustomRequestService`: Business logic for request creation, number generation, status transitions
   - `ProofApprovalService`: Proof workflow management, approval routing
   - `DesignerAssignmentService`: Route requests to designers based on availability/load
   - `NotificationService`: Email notifications at key workflow stages

4. **Salesforce Approval Process OR Flow:**
   - Route proofs to designated approvers
   - Capture approval decisions with audit trail
   - Support override capability with reason tracking

5. **File Management:**
   - Use Salesforce Files (ContentDocument/ContentVersion) for proof and logo uploads
   - Enforce max file size (50MB) and allowed formats
   - Generate preview thumbnails for image/PDF files

## Gaps & Risks

**Gap CIDS-G1: No Native Product Customization Workflow**
- Severity: Critical
- Description: Salesforce B2B Commerce has no equivalent to the multi-field customization form with file uploads, designer routing, and proof approval
- Impact: The entire custom design workflow would fail without this custom build
- Resolution: Full custom LWC + Apex implementation as described above
- Effort: XL (4-6 weeks)

**Gap CIDS-G2: Request Number Format**
- Severity: Medium
- Description: Format NNNNN-YYYYMMDDNN requires custom generation logic
- Resolution: Apex trigger on insert to generate using sequence counter + date stamp, or use External ID field
- Effort: Bundled with CIDS-G1

**Gap CIDS-G3: Designer Assignment with Delivery Method Coupling**
- Severity: Low
- Description: Current system couples designer and delivery method in single field
- Impact: Loss of data integrity and reportability
- Resolution: Separate Designer__c and Delivery_Method__c fields; custom LWC can display together
- Effort: Bundled with CIDS-G1

**Gap CIDS-G4: Proof Approval Override**
- Severity: Medium
- Description: Ability to post unapproved proofs with confirmation dialog
- Impact: If this bypass is operationally critical, must be implemented
- Resolution: Custom "Post Unapproved" action in LWC with reason capture and audit logging
- Effort: Bundled with CIDS-G1

**Gap CIDS-G5: Bar Chart Visualization**
- Severity: Low
- Description: Dashboard must display inline bar chart of request volume
- Resolution: Custom LWC using Chart.js library (lightweight, no additional license)
- Effort: Bundled with CIDS-G1

**Gap CIDS-G6: File Format Support**
- Severity: Medium
- Description: Current system supports 9 file formats (doc, docx, xls, xlsx, ppt, pptx, png, jpg, psd, ai, eps, pdf) with 50MB max
- Resolution: Salesforce Files supports all formats; implement validation via Apex
- Effort: Low (validation only)

**Gap CIDS-G7: Need-By Date Feasibility Calculation**
- Severity: Medium
- Description: System auto-adjusts available need-by dates based on delivery method
- Impact: Without this, users may request unrealistic delivery dates
- Resolution: Apex date calculation service called by form LWC; delivery method (digital) allows sooner dates than physical shipping
- Effort: M (bundled with form validation)

## Dependencies

- [[buyer-account-model|Buyer Account Model]] for requestor context
- [[approval-process-or-flow|Salesforce Approval Process or Flow]] for proof routing
- [[salesforce-files|Salesforce Files]] for proof and logo storage
- [[email-notifications|Email Notification Framework]] for workflow status emails
- Adobe Illustrator integration (separate from Salesforce — design work continues in Adobe)

## Open Questions

1. What are the business rules for need-by date feasibility? How many days minimum for digital vs. physical?
2. Should designer assignment be automated based on workload, or remain manual selection?
3. What are all the request categories beyond "Everyday"?
4. Is the proof approval override used frequently? Is there a quality control concern?
5. Should proofs be versioned (v1, v2, etc.) to track revision cycles?
6. Are there SLAs for designer turnaround, approval time, etc.?
7. How should rush surcharge be calculated? Is it a percentage or fixed amount?

## Evidence

**Meeting 1 (MerchTank Overview):**
- "Certain items are flagged as 'customizable' in MerchTank. When a user selects one, they're taken to a customization form..."
- "The entire custom POS workflow — a core value proposition of MerchTank — would not function" without this feature
- "The custom proofing workflow — a specialized feature that requires custom development"
- Recommendation: "Option 1 — keeps everything on-platform for single-system management, though this is one of the largest development efforts in the migration"

**Meeting 3 (Custom Requests):**
- Detailed form structure with 20+ fields for item specifications, branding references, designer assignment
- "Requests are manually routed to a specific designer via the 'Items To Designers' dropdown"
- "Proofs can be posted even if not yet approved, but this requires explicit confirmation through a warning dialog"
- "Request numbers are used in email subjects, file naming, and cross-system references"
