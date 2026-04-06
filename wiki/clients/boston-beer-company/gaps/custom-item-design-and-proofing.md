---
type: gap
client: boston-beer-company
status: open
severity: critical
category: product-customization
related-feature: "[Custom POS Ordering]([[feature|custom-pos-ordering]])"
resolution-approach: custom-dev
created: 2026-04-06
updated: 2026-04-06
sources:
  - "[[meeting|01-merchtank-overview]] Gap W3-G1, W3-G2"
  - "[[meeting|03-custom-requests]] Workflow 1: Custom Request Submission"
tags: custom-pos, design-proofing, file-uploads, creative-operations, core-value-prop
---

# Gap: Custom Item Design and Proofing Workflow

## Description

MerchTank provides a comprehensive custom item design and proofing workflow where users can submit print customization requests for select POS merchandise (e.g., branded tap handles, custom labels). The workflow includes: customization form submission, file uploads, delivery method selection, feasibility date calculations, proof request routing, designer assignment, and approval override capability.

This is a core value proposition of MerchTank and affects the entire Creative Operations team. Salesforce B2B Commerce has no native product customization or design proofing workflow.

## Current State

**MerchTank Customization Flow:**
1. User selects a customizable item from catalog
2. Customization form opens with fields:
   - Text to be printed (free text)
   - Notes to designer (free text, optional)
   - Delivery method (Digital/Email or Physical Ship)
   - Proof request toggle (request approval before printing)
   - Logo upload (formats: doc, docx, xls, xlsx, ppt, pptx, png, jpg, psd, ai, eps, pdf; max 50MB)
   - Reference picture upload (max 5MB)
3. System calculates need-by date feasibility based on delivery method:
   - Digital dates: sooner (1-2 weeks)
   - Physical shipping dates: later (2-4 weeks)
4. On submission:
   - CustomizationRequest record created
   - Routed to Creative Operations team
   - Designer assigned (manual or auto-assignment logic)
   - If proof_request = true, approval workflow initiated
   - Designer can post proof, user approves/rejects, designer proceeds with printing

**Supporting Requirements:**
- [[meeting|03-custom-requests]] Critical Req (implied): "Custom item design submission and proofing"
- Request number format: Custom format (needs validation)
- Designer assignment: Coupled to delivery method (implied from current system)
- Proof approval: Can be overridden post-unapproved (unapproved proofs can be posted with confirmation)

## Target State

**Salesforce Custom Item Design Architecture:**
- Custom Object `CustomizationRequest__c`:
  - Fields: OrderItemSummary__c (lookup), Customization_Text__c (LongTextArea), Designer_Notes__c (LongTextArea), Delivery_Method__c (picklist: Digital/Physical), Proof_Requested__c (checkbox), Requested_Need_By_Date__c (date), Status__c (picklist: Draft/Submitted/Assigned/In_Design/Proof_Ready/Approved/Printing/Complete), Created_By_User__c (lookup)

- File Management:
  - Salesforce Files linked to CustomizationRequest
  - Logo files (max 50MB each; support multiple formats)
  - Reference images (max 5MB each)

- Custom LWC `c-customization-form`:
  - Multi-step form with validation
  - File upload component (single or multi-file)
  - Feasibility date calculation (delivery method dependent)
  - Pre-submission validation (required fields, file size limits)
  - Confirmation dialog before submit

- Designer Assignment Workflow:
  - Option A: Auto-assignment Flow based on delivery method + workload
  - Option B: Manual assignment by Procurement through admin LWC
  - Assignment creates Case or custom Task record for Creative Ops visibility

- Proof Approval Process:
  - If Proof_Requested__c = true: Custom Approval Process route to assigned Designer
  - Designer can view proof and approve/reject
  - Post-Unapproved: Custom action/Flow to bypass approval with confirmation dialog
  - Approval override logs audit trail

- Status Transitions:
  - Draft → Submitted (user submits form)
  - Submitted → Assigned (designer assigned)
  - Assigned → In_Design (designer starts work)
  - In_Design → Proof_Ready (designer creates proof)
  - Proof_Ready → Approved (approval process complete or override)
  - Approved → Printing (designer starts printing)
  - Printing → Complete (printing finished, items ready for shipment)

- Integration with Order:
  - CustomizationRequest linked to OrderItemSummary
  - Order cannot be marked as shipped until CustomizationRequest.Status__c = Complete

**File Upload Approach:**
- Use Salesforce Files (ContentVersion/ContentDocument)
- Store in Salesforce as-is (no external file system)
- Max 50MB per file (within Salesforce limit of 2GB)
- Support formats: doc, docx, xls, xlsx, ppt, pptx, png, jpg, psd, ai, eps, pdf

## Gap Analysis

### What Salesforce Lacks

Salesforce B2B Commerce and standard Salesforce have no integrated design/proofing workflow:
- No out-of-the-box customization form
- No design request routing to Creative Ops
- No proof approval process specific to design
- No feasibility calculation for design turnaround
- No custom file upload handling for design assets

### Root Cause

B2B Commerce is focused on catalog-based commerce. Custom item design is a specialized business process unique to BBC's POS merchandise business. This requires purpose-built domain objects and workflows.

### Impact

**Without Resolution:**
- Custom POS workflow is unavailable → Users cannot order customizable items
- Creative Ops cannot manage design requests → No visibility into pipeline
- No proof approval → Printing starts without review, risking quality issues
- File management is manual → No clear audit trail of design versions
- Need-by date feasibility is not enforced → Users request unrealistic dates

## Resolution Options

### Option 1: Custom LWC Customization Module + Approval Process (RECOMMENDED)

**Approach:**
1. Create `CustomizationRequest__c` object as designed above
2. Build custom LWC `c-customization-form`:
   - Step 1: Item selection and customization text entry
   - Step 2: File uploads (logo, reference image) with validation
   - Step 3: Delivery method selection
   - Step 4: Feasibility date calculation and review
   - Step 5: Proof request toggle and submission
3. Implement Need-By Date Feasibility Calculation:
   - Apex service class `CustomizationDateCalculator` with logic:
     - Digital delivery: today + 14 days
     - Physical shipping: today + 21 days
   - Validate against holiday calendar and designer capacity (optional)
4. Designer Assignment:
   - Scheduled Flow or batch Apex job that assigns designers based on:
     - Delivery method (digital designers vs. print designers)
     - Current workload (optional)
     - Designer availability
5. Create Custom Approval Process:
   - Initiator: CustomizationRequest.CreatedBy
   - Approver: Assigned Designer
   - Steps: Approve/Reject
   - If Rejected: Route back to submitter for revisions
6. Post-Unapproved Proof Override:
   - Custom action on CustomizationRequest: "Post Unapproved Proof"
   - Confirmation dialog: "You are posting proof of concept that has not yet been approved!"
   - Override creates audit record
7. Status dashboard for Creative Ops:
   - Custom LWC showing pipeline (Draft | In Design | Proof Pending | Approved | Printing | Complete)
   - Filter by designer, delivery method, status

**Effort:** XL (Extra Large) — 4-6 weeks
- Week 1: Object design, Apex service classes
- Week 2-3: LWC customization form (multi-step, file upload)
- Week 4: Designer assignment Flow, approval process
- Week 5: Status dashboard, creative ops visibility
- Week 6: Testing, documentation, data migration

**Advantages:**
- Full feature parity with current system
- All data in Salesforce: audit trail, file versions, designer notes
- Integrated with Order lifecycle (cannot ship until design complete)
- Extensible: Can add proof versioning, feedback loops, SLA tracking
- Transparent: Creative Ops has clear visibility into requests and status

**Risks/Dependencies:**
- File upload complexity: LWC file upload requires careful error handling
- Designer capacity modeling: Auto-assignment logic may need refinement
- Approval process UX: Multiple approval steps can be confusing
- Data migration: Design request history from MerchTank may or may not be migrated

**Trade-offs:**
- Largest development effort on the project (~XL)
- Requires Creative Ops training on new system
- File storage in Salesforce adds data volume and storage costs
- Ongoing maintenance of custom approval processes and LWCs

---

### Option 2: Salesforce CPQ Product Configuration Integration

**Approach:**
- Use Salesforce CPQ Product Configurator as foundation for customization
- CPQ attributes for design fields (text, delivery method, proof request)
- CPQ configuration captured in custom Order summary fields
- Designer assignment via Flow

**Effort:** L (Large) — 2-3 weeks
- Week 1: CPQ attribute setup, order integration
- Week 2-3: Designer assignment, file upload handling (custom)

**Advantages:**
- Leverages existing Salesforce CPQ infrastructure
- Faster implementation than full custom build
- Integrates tightly with order creation

**Risks/Dependencies:**
- Requires CPQ license (additional cost)
- CPQ Configurator is not designed for design proofing (missing Approval Process integration)
- File upload must be custom (CPQ doesn't handle design files well)
- Reduced flexibility for complex designer workflows

**Trade-offs:**
- Licensing cost
- Less control over customization UX
- Still requires custom code for file handling and approval

---

### Option 3: External Customization Tool Integration

**Approach:**
- Keep design/proofing workflow in external tool (e.g., Heroku app, third-party SaaS like Cimpress, Art.io)
- Salesforce triggers order creation and sends customization data to external system
- External system handles design, proofing, file management
- Webhooks sync back to Salesforce (CustomizationRequest status updates, completion)

**Effort:** M-L (2-4 weeks)
- Week 1: Evaluate third-party tools, API integration design
- Week 2-3: API integration (order creation webhook, status sync)
- Week 4: Testing, data validation

**Advantages:**
- Proven design/proofing UX (if using established SaaS tool)
- Reduces Salesforce development effort
- Specialized vendors may have better features (proof versioning, feedback loops)

**Risks/Dependencies:**
- External system dependency: Tool availability affects BBC operations
- Integration maintenance: Two systems to keep in sync
- Data duplication: Design data lives in external system, Salesforce only stores status
- Licensing cost: Third-party tool per-user or per-transaction fees

**Trade-offs:**
- Less control over customization logic
- External system is source of truth (Salesforce is just a status tracker)
- Reduced audit trail visibility in Salesforce

---

## Recommended Approach

**Option 1 (Custom LWC Customization Module)** is recommended because:

1. **Core Value Proposition:** Custom POS design is central to BBC's business. Keeping it on-platform ensures control and visibility.
2. **Integration:** Tight integration with Order lifecycle (cannot ship until design complete) ensures process completeness.
3. **Audit Trail:** All design data, approvals, and file versions stored in Salesforce for compliance and traceability.
4. **Future Features:** Custom build is extensible for advanced features (design templates, automated routing, capacity planning).

**Option 3** is a fallback if BBC prefers to use a specialized design tool and can accept reduced visibility in Salesforce.

## Effort Estimate

**Option 1:** Extra Large (XL)
- Effort: 4-6 weeks (160-240 hours)
- Confidence: Medium (LWC file upload and multi-step form are well-established patterns; Approval Process integration is standard; risk is complexity of feasibility calculation and designer assignment)
- Unknowns: Feasibility calculation rules (are they simple or complex?); designer workload modeling; data migration scope

**Option 2:** Large (L)
- Effort: 2-3 weeks (80-120 hours)
- Confidence: Medium (CPQ integration is less common; file handling must be custom)
- Unknowns: CPQ licensing; CPQ Configurator fit; file upload complexity

**Option 3:** Medium-Large (M-L)
- Effort: 2-4 weeks (80-160 hours)
- Confidence: High (straightforward API integration; risk is tool evaluation and selection)
- Unknowns: Tool selection; API complexity; licensing cost

## Dependencies

### Must Happen Before
- [[decision|Custom-POS-Strategy]] — Confirm custom POS is in scope for Phase 1 (vs. deferred to Phase 2)
- [[decision|File-Management-Strategy]] — Decide whether to store design files in Salesforce or externally

### Must Happen Alongside
- [[feature|order-lifecycle-integration]] — Order cannot be marked shipped until CustomizationRequest is complete

### Blocks
- [[feature|custom-pos-ordering]] — No custom item design workflow without this gap resolved

## Evidence

### Meeting 1: MerchTank Overview (Dec 4, 2025)
**Gap W3-G1: Custom Item Design Submission Form**
- Severity: Critical
- Description: "No equivalent to the multi-field customization form with file uploads, delivery method selection, date feasibility calculation, and proof request routing."
- Impact: "The entire custom POS workflow — a core value proposition of MerchTank — would not function."
- Recommendation: "Custom LWC Customization Module...Build a custom Lightning Web Component that replicates the form, stores data in custom objects (CustomizationRequest__c), and uses Salesforce Files for uploads. Route to creative team via Case or custom approval process. (~XL effort, 4-6 weeks)"

**Gap W3-G2: Need-By Date Feasibility Calculation**
- Severity: Medium
- Description: "MerchTank automatically adjusts available need-by dates based on delivery method (digital dates are sooner, physical shipping pushes dates out)."
- Impact: "Without this, users may request unrealistic delivery dates."

### Meeting 3: Custom Requests (Mar 9, 2026)
**Workflow 1: Custom Request Submission**
- Current State: "Customization form with text to be printed, notes to designer, delivery method selection"
- "File uploads: logo (multiple formats, max 50MB), reference picture (max 5MB)"
- "Proof approval with override capability"
- "Designer assignment coupled to delivery method"

**Additional Gaps:**
- Gap W1-G1: "Custom Request Number Format" (custom format validation needed)
- Gap W1-G2: "Designer Assignment with Delivery Method Coupling"
- Gap W1-G3: "Proof Approval Override (Post Unapproved Proof)"

## Validation Notes

SFCC Validation Report confirms:
- "Salesforce B2B Commerce does not have product customization"
- "Custom LWC approach is viable for file uploads (2GB limit is sufficient)"
- "Approval Process integration recommended for designer workflow"

## Open Questions

1. **Feasibility Calculation Rules:** Are the date rules simple (Digital +14, Physical +21) or more complex? Are there holiday calendars, designer capacity limits, or batch scheduling?
   - *Impact if answered wrong:* Feasibility calculation logic is more complex; effort +1 week
   - *Owner:* BBC Creative Ops/Procurement

2. **Designer Assignment Logic:** Is designer assignment purely automatic (based on delivery method) or does it require manual selection or approval?
   - *Impact if answered wrong:* Assignment workflow design changes
   - *Owner:* BBC Creative Ops

3. **Design Request Number Format:** What is the custom format for request numbers? (e.g., "CUST-2026-001" or other pattern)
   - *Impact if answered wrong:* Auto-number sequence logic changes
   - *Owner:* BBC Procurement

4. **Design History Migration:** Should design request history from MerchTank be migrated to Salesforce, or start fresh?
   - *Impact if answered wrong:* Data migration scope and complexity change
   - *Owner:* BBC IT/Procurement

5. **Proof Versioning:** How many proof versions should be stored? Are previous proofs archived or deleted?
   - *Impact if answered wrong:* File management and retention logic changes
   - *Owner:* BBC Creative Ops

## Related Gaps

- [[gap|need-by-date-feasibility-calculation]] — Feasibility date calculation is part of this gap
- [[gap|proof-approval-override]] — Post-unapproved proof posting is part of this gap

## Status & Next Steps

**Status:** Open (design phase)

**Next Steps:**
1. Confirm custom POS is Phase 1 or Phase 2 (impacts effort and timeline)
2. Schedule feasibility calculation rules workshop with BBC Creative Ops
3. Confirm designer assignment logic
4. Validate custom request number format
5. Finalize CustomizationRequest__c schema
6. Begin LWC customization form development
7. Start Apex service class development for date calculation
