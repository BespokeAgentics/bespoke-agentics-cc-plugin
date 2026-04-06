# Migration Profile

Deliverable profile for platform migration analysis. Designed for assessing a client's current system and mapping it to a target platform — originally built for Salesforce B2B Commerce migrations but applicable to any platform migration (CRM, ERP, e-commerce, etc.).

## Primary Deliverable
`{DOCS_DIR}/gap-analysis-{PROJECT_SLUG}-{LABEL}.md`

## Wave Structure

```
Wave 1 (parallel): Meeting Analyst ∥ UI Migration ∥ Integration Analyst ∥ Data Schema
    ↓
Wave 2 (sequential): Platform Expert Assessment (depends on Wave 1 Meeting Analyst)
    ↓
Wave 3 (sequential): Gap Analysis Synthesis (depends on ALL Wave 1+2)
    ↓
Wave 4 (parallel): Validator ∥ Client Elicitor ∥ Export Formatter
```

## Intermediate Deliverables
- `{DOCS_DIR}/feature-inventory-{PROJECT_SLUG}-{LABEL}.md`
- `{DOCS_DIR}/ui-migration-map-{LABEL}.md`
- `{DOCS_DIR}/integration-assessment-{LABEL}.md`
- `{DOCS_DIR}/data-schema-mapping-{LABEL}.md`
- `{DOCS_DIR}/platform-assessment-{LABEL}.md`

## Final Deliverables
- `{DOCS_DIR}/gap-analysis-{PROJECT_SLUG}-{LABEL}.md` — Gap analysis (primary)
- `{DOCS_DIR}/platform-validation-{PROJECT_SLUG}.md` — Fact-checked validation
- `{DOCS_DIR}/client-elicitation-{PROJECT_SLUG}.md` — Open questions & assumptions
- `{DOCS_DIR}/meeting-prep-{PROJECT_SLUG}-validation.md` — Follow-up meeting prep
- `{DOCS_DIR}/gap-analysis-export-{PROJECT_SLUG}.html` — Export format (HTML)

---

## Wave 1 — 4 Parallel Agents

All read from Phase 1 synthesis outputs.

### Agent 1: Meeting/Recording Analyst

```
Agent: "Meeting transcript analysis"
Prompt: |
  Analyze the recording for {project-name} to extract functional requirements and business context.

  Read:
  - {FRAMES_DIR}/transcript.txt (if available)
  - {DOCS_DIR}/screen-catalog.md
  - {DOCS_DIR}/component-library.md
  - {DOCS_DIR}/system-architecture-map.md

  Extract:
  - Functional requirements (what the system must do)
  - User roles and personas
  - Pain points with current platform
  - Integration hints and dependencies
  - Business rules and constraints
  - Volume/scale data (users, transactions, catalog size)

  Save the Feature Inventory to: {DOCS_DIR}/feature-inventory-{PROJECT_SLUG}-{LABEL}.md
```

### Agent 2: UI Migration Mapping

```
Agent: "UI component migration mapping"
Prompt: |
  Map {project-name}'s current UI to target platform equivalents.

  Read:
  - {DOCS_DIR}/screen-catalog.md
  - {DOCS_DIR}/component-library.md

  For every UI component observed:
  - Current implementation (what it looks like and does now)
  - Target platform equivalent (standard component, configuration, custom development)
  - Migration complexity (Drop-in / Configure / Custom Build / No Equivalent)
  - Notes on behavioral differences

  Save to: {DOCS_DIR}/ui-migration-map-{LABEL}.md
```

### Agent 3: Integration Assessment

```
Agent: "Integration and API assessment"
Prompt: |
  Assess {project-name}'s integration landscape for platform migration.

  Read:
  - {DOCS_DIR}/system-architecture-map.md
  - {FRAMES_DIR}/transcript.txt (if available)

  Catalog:
  - Every external system and third-party service
  - Data flows between systems (direction, frequency, format)
  - API dependencies (REST, SOAP, file-based, manual)
  - Authentication/authorization patterns
  - Target platform integration architecture recommendation

  Save to: {DOCS_DIR}/integration-assessment-{LABEL}.md
```

### Agent 4: Data Schema Mapping

```
Agent: "Data schema and object mapping"
Prompt: |
  Design the target platform data model for {project-name}'s migration.

  Read:
  - {DOCS_DIR}/system-architecture-map.md
  - {DOCS_DIR}/component-library.md

  Reverse-engineer the current data model from screens and map to target platform objects:
  - Current entities/objects observed
  - Target platform standard objects that match
  - Custom objects/fields needed
  - Data migration considerations (transforms, mappings, cleanup)
  - Relationships and dependencies

  Save to: {DOCS_DIR}/data-schema-mapping-{LABEL}.md
```

Wait for ALL 4 Wave 1 agents to complete.

---

## Wave 2 — Platform Expert Assessment

Depends on Wave 1 Meeting Analyst (feature inventory).

```
Agent: "Target platform capability assessment"
Prompt: |
  Evaluate {project-name}'s requirements against the target platform's capabilities.

  Read:
  - {DOCS_DIR}/feature-inventory-{PROJECT_SLUG}-{LABEL}.md
  - {DOCS_DIR}/screen-catalog.md
  - {DOCS_DIR}/component-library.md
  - {DOCS_DIR}/system-architecture-map.md

  For each feature in the inventory, assess:
  - Platform capability match: Standard / Configuration / Custom Development / Third-Party / No Equivalent
  - Implementation complexity: Low / Medium / High / Very High
  - Notes on approach, limitations, or alternatives

  Use WebSearch to verify platform capabilities against official documentation where uncertain.

  Save to: {DOCS_DIR}/platform-assessment-{LABEL}.md
```

Wait for Wave 2 to complete.

---

## Wave 3 — Gap Analysis Synthesis

Depends on ALL Wave 1 + Wave 2.

```
Agent: "Gap analysis synthesis"
Prompt: |
  Produce the comprehensive gap analysis for {project-name}'s platform migration.

  Read ALL upstream documents:
  - {DOCS_DIR}/feature-inventory-{PROJECT_SLUG}-{LABEL}.md
  - {DOCS_DIR}/platform-assessment-{LABEL}.md
  - {DOCS_DIR}/ui-migration-map-{LABEL}.md
  - {DOCS_DIR}/integration-assessment-{LABEL}.md
  - {DOCS_DIR}/data-schema-mapping-{LABEL}.md
  - {DOCS_DIR}/screen-catalog.md
  - {DOCS_DIR}/component-library.md
  - {DOCS_DIR}/system-architecture-map.md

  Synthesize ALL findings into a client-centric, workflow-based gap analysis:
  - Organize by business workflow (not by technical category)
  - For each workflow area: current state, target state, gaps, recommended approach, effort estimate
  - Prioritize gaps by business impact
  - Include risk assessment and mitigation strategies
  - Provide implementation phasing recommendation

  Save to: {DOCS_DIR}/gap-analysis-{PROJECT_SLUG}-{LABEL}.md
```

Wait for gap analysis to complete. This is the **primary deliverable**.

---

## Wave 4 — 3 Parallel Agents

All depend on the gap analysis being complete.

### Agent 1: Platform Validator

```
Agent: "Platform capability validation"
Prompt: |
  Fact-check the gap analysis for {project-name} against official platform documentation.

  Read: {DOCS_DIR}/gap-analysis-{PROJECT_SLUG}-{LABEL}.md

  For every capability claim, verify against official documentation using WebSearch.
  Flag any inaccuracies, outdated information, or missing options.

  Save to: {DOCS_DIR}/platform-validation-{PROJECT_SLUG}.md
```

### Agent 2: Client Elicitor

```
Agent: "Client elicitation synthesis"
Prompt: |
  Consolidate all open questions and unvalidated assumptions from {project-name}'s analysis.

  Read ALL upstream documents:
  - {DOCS_DIR}/gap-analysis-{PROJECT_SLUG}-{LABEL}.md
  - {DOCS_DIR}/feature-inventory-{PROJECT_SLUG}-{LABEL}.md
  - {FRAMES_DIR}/transcript.txt (if available)

  Produce TWO files:
  - {DOCS_DIR}/client-elicitation-{PROJECT_SLUG}.md — All open questions, unvalidated assumptions, low-confidence features, prioritized by impact
  - {DOCS_DIR}/meeting-prep-{PROJECT_SLUG}-validation.md — Structured agenda for a follow-up validation meeting with the client
```

### Agent 3: Export Formatter

```
Agent: "Gap analysis export"
Prompt: |
  Convert the gap analysis into shareable formats for {project-name}.

  Read: {DOCS_DIR}/gap-analysis-{PROJECT_SLUG}-{LABEL}.md

  Produce:
  - {DOCS_DIR}/gap-analysis-export-{PROJECT_SLUG}.html — Clean, styled HTML version suitable for sharing via Confluence, SharePoint, or email
```

Wait for all 3 agents to complete.
