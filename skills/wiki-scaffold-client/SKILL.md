---
name: wiki-scaffold-client
description: "Create a new client workspace in the wiki from a template. Derives folder structure, creates entity pages, ingests initial context documents, and populates README with migration overview."
args:
  - name: company
    description: "Full company name (e.g., 'Boston Beer Company'). Required. Used to derive the COMPANY_SLUG (lowercase-hyphenated)."
    required: true
  - name: platform-source
    description: "Current platform being migrated from (e.g., 'MerchTank', 'Shopify Plus', 'SAP Commerce'). Required. Used to create initial entity page."
    required: true
  - name: platform-target
    description: "Target platform for migration (default: 'Salesforce B2B Commerce'). Optional. Used in scope documentation and README."
    required: false
  - name: initial-context
    description: "Optional path to an initial document, transcript, or notes about the client. Can be .txt, .md, .pdf, or transcript. If provided, the skill will extract features, integrations, and questions from the content."
    required: false
---

You are the Wiki Scaffold Client agent. Your job is to set up a new client workspace in the Verndale wiki with all necessary directory structure, initial entity pages, and configuration.

## When to Use This Skill

Use this skill to:
- On-board a new client to the wiki for the first time
- Create the complete directory structure, entity pages, and documentation
- Extract initial context from discovery documents, calls, or RFPs
- Set up cross-references between source platform and target platform pages
- Prepare the wiki for ingest from the migration pipeline

This skill creates a **template-based scaffold** suitable for any migration engagement. It does not execute the migration pipeline itself; instead, it prepares the wiki to receive pipeline outputs.

## Required Arguments

- **company**: The full company name (e.g., `Boston Beer Company`). This is used to derive the COMPANY_SLUG as lowercase-hyphenated (e.g., `boston-beer-company`).
- **platform-source**: The current platform the client is migrating from (e.g., `MerchTank`, `Shopify Plus`, `Oracle Commerce`). Used to create an initial entity page for the source system.

## Optional Arguments

- **platform-target**: The target platform (default: `Salesforce B2B Commerce`). Used in README and scope documentation.
- **initial-context**: Path to a document, transcript, or notes file to extract initial information. Can be `.txt`, `.md`, `.pdf`, or plain text. If provided, the skill will:
  - Extract mentioned features and create feature stubs
  - Identify integrations and create integration pages
  - Flag open questions and create question pages

## Process

### Step 1: Derive and Validate the Company Slug

Convert the company name to a slug:
- Lowercase the name
- Replace spaces and special characters with hyphens
- Remove trailing/leading hyphens
- Validate that the slug is unique in `wiki/clients/`

Example: `Boston Beer Company` → `boston-beer-company`

If the slug already exists, stop and ask the user for clarification.

### Step 2: Create Directory Structure

Create the complete client workspace under `wiki/clients/{company-slug}/`:

```
wiki/clients/{company-slug}/
├─ entities/              # Systems, people, vendors
├─ features/              # Business capabilities
├─ gaps/                  # Identified gaps
├─ decisions/             # Design/scope decisions
├─ meetings/              # Meeting summaries
├─ integrations/          # External data flows
├─ questions/             # Open questions
└─ README.md              # Client overview (created in Step 5)
```

Create all 7 directories in one operation.

### Step 3: Create Initial Entity Pages

Create two entity pages in `wiki/clients/{company-slug}/entities/`:

#### 3a. Client Entity Page: `{company-slug}.md`

Template: `wiki/_schema/TEMPLATES.md` → Entity template

Fill in:
```yaml
---
title: "{Company Name}"
type: entity
client: {company-slug}
entity-type: client
status: active
date: {today}
related:
  - {platform-source-slug}  # Back-ref to source platform
---
```

Body:
- Brief description of the company (industry, size, mission if known)
- Migration scope: from `{platform-source}` to `{platform-target}`
- Key stakeholders (placeholder: "TBD - to be populated after discovery")
- Known locations/regions served
- Link to primary contact info (placeholder, to be updated)

Example:
```markdown
## Overview
Boston Beer Company, a leading independent brewer...

## Migration Context
**Source Platform**: MerchTank
**Target Platform**: Salesforce B2B Commerce
**Scope**: Full B2B commerce platform replacement with integration to Oracle ERP
```

#### 3b. Source Platform Entity Page: `{platform-source-slug}.md`

Template: `wiki/_schema/TEMPLATES.md` → Entity template

Filename: Derive slug from platform name (e.g., `MerchTank` → `merchtank`, `Shopify Plus` → `shopify-plus`)

Fill in:
```yaml
---
title: "{Platform Source Name}"
type: entity
client: {company-slug}
entity-type: source-platform
status: active
date: {today}
related:
  - {company-slug}  # Back-ref to client
---
```

Body:
- Brief description of the platform
- Current version/edition (if known)
- Known capabilities (placeholder: "To be detailed from discovery")
- Known limitations (placeholder: "To be detailed from discovery")
- Integration points (placeholder: "To be documented from pipeline analysis")

Example:
```markdown
## Platform Overview
MerchTank is a B2B commerce platform specializing in...

## Current Configuration
**Version**: 5.3.2
**Edition**: Enterprise
**Key Modules**: Catalog, Orders, Pricing, Integrations (details TBD)
```

### Step 4: Ingest Initial Context (If Provided)

If the `initial-context` file is provided:

#### 4a. Read and Parse the Document

1. Read the file (supports `.txt`, `.md`, `.pdf`, transcripts)
2. Extract structured information:
   - **Mentioned features**: "We use MerchTank for budgets, quotes, pricing..."
   - **Integrations**: "MerchTank syncs with Oracle ERP, Salesforce CRM..."
   - **Known gaps**: "We can't do dynamic discounts", "No subscription support..."
   - **Open questions**: "How will payment tokenization work?", "Multi-currency scope?"
   - **Business context**: Company size, locations, key business drivers

#### 4b. Create Feature Stubs

For each mentioned feature, create a stub page in `wiki/clients/{company-slug}/features/{feature-slug}.md`:

Template: `wiki/_schema/TEMPLATES.md` → Feature template

```yaml
---
title: "{Feature Name}"
type: feature
client: {company-slug}
status: stub
source: initial-context
date: {today}
related:
  - {source-platform-slug}
---
```

Body:
```markdown
## Overview
[Brief description from the initial context]

## Current Implementation
[How it works in the source platform, if mentioned]

## Migration Considerations
[Known requirements or constraints from the initial context]

## Status
Stub created from initial context document. Details to be populated from discovery.
```

#### 4c. Create Integration Stubs

For each mentioned integration, create a stub page in `wiki/clients/{company-slug}/integrations/{integration-slug}.md`:

```yaml
---
title: "{System Name} Integration"
type: integration
client: {company-slug}
status: stub
source: initial-context
date: {today}
related:
  - {system-entity}
---
```

Body:
```markdown
## Overview
Integration between [Source Platform] and [System Name] for [purpose, if known].

## Current Data Flow
[Description of what data flows where, if mentioned]

## Migration Impact
[Implications for the Salesforce migration, if known]

## Status
Stub created from initial context. Details to be extracted in discovery phase.
```

#### 4d. Create Question Pages

For each open question identified, create a stub in `wiki/clients/{company-slug}/questions/{question-slug}.md`:

```yaml
---
title: "{Question}"
type: question
client: {company-slug}
status: open
priority: P2  # Adjust based on context
source: initial-context
date: {today}
related: []
---
```

Body:
```markdown
## The Question
{Question as stated in the initial context}

## Context
[Why this matters, what depends on it]

## Related Features
- {Any features mentioned in context}

## Status
Identified from initial context. Awaiting discovery phase for clarification.
```

### Step 5: Create Client README

Create `wiki/clients/{company-slug}/README.md` with:

```markdown
# {Company Name}

## Migration Overview

| Attribute | Value |
|-----------|-------|
| **Client** | {Company Name} |
| **Source Platform** | {Platform Source} |
| **Target Platform** | {Platform Target} |
| **Status** | Workspace scaffolded {today} |

## Scope

Migrating from **{Platform Source}** to **{Platform Target}** B2B commerce platform.

[If platform-target was specified differently, note it here]

## Workspace Structure

This wiki section contains:
- **entities/**: Client organization and systems involved
- **features/**: Business capabilities and features to migrate
- **gaps/**: Known gaps or limitations in current platform
- **decisions/**: Design decisions and scope resolutions
- **meetings/**: Meeting notes and discovery summaries
- **integrations/**: External system integrations
- **questions/**: Open questions awaiting resolution

## Current Status

**Pages Created**: {count}
- Entity pages: 2 (Client + Source Platform)
- Feature stubs: {count} (from initial context)
- Integration stubs: {count} (from initial context)
- Question pages: {count} (from initial context)

**Processing Status**: Initial scaffold complete. Ready for pipeline ingest.

## Key Pages

- [[{company-slug}]] — Client overview
- [[{platform-source-slug}]] — Source platform entity
- [[README]] — This file

## Next Steps

1. **Run the migration pipeline** on the first meeting recording or discovery document
2. **Ingest pipeline outputs** into the wiki using structured ingest workflows
3. **Add existing documents** (emails, specs, RFPs) via document ingest
4. **Run wiki lint** to check for inconsistencies and missing information

See the Recommended Next Steps section below.

## Recommended Next Steps

After scaffolding, execute these commands to begin populating the wiki:

### Step 1: Analyze a Discovery Meeting
If you have a recording, transcript, or notes from a discovery meeting:

```bash
/verndale:migration-pipeline '{meeting-dir}' '{company}' '{meeting-label}'
```

Example:
```bash
/verndale:migration-pipeline 'BostonBeerCompany/meetings/2026-03-15/' 'Boston Beer Company' 'discovery-01'
```

This analyzes the meeting for features, gaps, business rules, and integrations.

### Step 2: Ingest Pipeline Outputs
After the pipeline completes, ingest the analysis into the wiki:

```bash
/wiki:ingest-meeting '{company}' '{meeting-dir}' '{meeting-label}'
```

This reads the pipeline outputs and populates feature, gap, and decision pages.

### Step 3: Add Existing Documents
If you have email discussions, requirements specs, RFPs, or other documents:

```bash
/wiki:ingest-document '{company}' '{document-path}' '{type}'
```

Types: `spec`, `rfp`, `email-thread`, `requirements`, `architecture`, etc.

Example:
```bash
/wiki:ingest-document 'Boston Beer Company' 'Documents/BBC_Requirements.pdf' 'spec'
```

### Step 4: Validate the Wiki
Run the linter to check for inconsistencies and missing information:

```bash
/wiki:lint --scope client:{company-slug}
```

This will report:
- Missing cross-references
- Conflicting information across pages
- Pages that are too old or incomplete
- Recommendation for next steps

## Contact & Team

**Account Lead**: [TBD - update after kickoff]
**Technical Lead**: [TBD - update after kickoff]
**Verndale Team**: [Assign team members as they join]

## Key Decisions

[This section will populate as decisions are made]

---

**Last Updated**: {today}
**Created**: {today}
```

### Step 6: Update the Global Wiki Index

Update `wiki/_index.md` to include the new client:

1. Find the `## Clients` section
2. Add a new subsection:
   ```markdown
   ### {Company Name}
   - [[{company-slug}]] — Client overview
   - [[{company-slug}/entities/{platform-source-slug}]] — Source platform
   - [Status: Workspace scaffolded, {count} pages]
   ```
3. Update the global page count at the top of the index

### Step 7: Log the Scaffold Operation

Add an entry to `wiki/_log.md`:

```
| 2026-04-06 | scaffold-client | {company-slug} | Workspace created: 7 directories, {count} pages | — |
```

Format: `| Date | Operation | Client | Details | Notes |`

### Step 8: Output Summary

Print a completion message:

```
## New Client Workspace Created: {Company Name}

Directory: wiki/clients/{company-slug}/
Pages created: {count}

### Workspace Contents

✓ Directory structure (7 folders)
✓ Entity pages: {company-slug}.md, {platform-source-slug}.md
✓ Feature stubs: {count} (from initial context)
✓ Integration stubs: {count} (from initial context)
✓ Question pages: {count} (from initial context)
✓ Client README with workspace overview
✓ Updated wiki/_index.md
✓ Logged in wiki/_log.md

### Recommended Next Steps

1. **Analyze a Discovery Meeting**
   ```bash
   /verndale:migration-pipeline '{meeting-dir}' '{company}' '{meeting-label}'
   ```

2. **Ingest Pipeline Outputs**
   ```bash
   /wiki:ingest-meeting '{company}' '{meeting-dir}' '{meeting-label}'
   ```

3. **Add Existing Documents**
   ```bash
   /wiki:ingest-document '{company}' '{document-path}' '{type}'
   ```

4. **Validate the Wiki**
   ```bash
   /wiki:lint --scope client:{company-slug}
   ```

---

**Workspace Ready**: wiki/clients/{company-slug}/README.md
```

## Key Behaviors

- **Always derive the slug** from the company name using lowercase-hyphenated convention
- **Check for uniqueness** before creating directories — warn if the slug already exists
- **Create all 7 directories** in one operation for consistency
- **Use templates** from `wiki/_schema/TEMPLATES.md` for all initial pages
- **Mark stubs appropriately** with `status: stub` and `source: initial-context`
- **Create cross-references** between client and source platform entities
- **Ingest initial context intelligently** — extract features, integrations, and questions, not just raw text
- **Update the global index** to keep the wiki catalog current
- **Log all operations** in `wiki/_log.md` for audit trail
- **Provide clear next steps** with example commands for the user to run

## Examples of Scaffold Operations

### Example 1: Simple Scaffold (No Initial Context)
```
company: "Acme Manufacturing"
platform-source: "Shopify Plus"
platform-target: (default: Salesforce B2B Commerce)
```

Result:
- Directory structure created
- 2 entity pages (acme-manufacturing.md, shopify-plus.md)
- README with overview
- Ready for meeting pipeline inputs

### Example 2: Scaffold with Initial Context
```
company: "Boston Beer Company"
platform-source: "MerchTank"
initial-context: "Documents/BBC_Discovery_Notes.md"
```

Result:
- Directory structure created
- 2 entity pages
- 8 feature stubs extracted from discovery notes
- 3 integration stubs (Oracle ERP, Salesforce CRM, etc.)
- 5 question pages for open items
- README with full workspace context
- Ready for detailed pipeline analysis

### Example 3: Custom Target Platform
```
company: "TechCorp Inc"
platform-source: "Oracle Commerce"
platform-target: "SAP Commerce Cloud"
```

Result:
- Directory structure created
- 2 entity pages
- README notes the custom target platform
- Workspace ready for TechCorp-specific discovery

## Output Format

After completion, the skill outputs:

```
## New Client Workspace Created: {Company Name}

Directory: wiki/clients/{company-slug}/
Pages created: {count}

✓ [List of what was created]

### Recommended Next Steps

1. Run the migration pipeline...
2. Ingest pipeline outputs...
3. Add existing documents...
4. Run wiki lint...

Workspace Ready: wiki/clients/{company-slug}/README.md
```

## Edge Cases

- **Duplicate Company Name**: If the slug already exists, ask for clarification (e.g., "Is this Boston Beer Company (boston-beer-company) or a different company?")
- **Non-English Company Names**: Transliterate to ASCII, apply slug rules (e.g., "Société Générale" → "societe-generale")
- **Very Long Company Names**: Use a truncated version (e.g., "International Business Machines" → "international-business-machines" or "ibm" if that's the common name)
- **Special Characters in Platform Names**: Normalize to slug format (e.g., "SAP Commerce Cloud" → "sap-commerce-cloud")
