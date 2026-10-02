# Entity & stub templates

## Step 3a — Client entity page

Path: `wiki/{group}/{company-slug}/entities/{company-slug}.md`. Template: `wiki/_schema/templates/entity.md`.

Frontmatter:

```yaml
---
title: "{Company Name}"
type: entity
client: {company-slug}
entity-type: client
status: active
created: {today}
updated: {today}
related:
  - {platform-source-slug}
---
```

Body must cover: brief company description (industry, size, mission if known), migration scope (`from {platform-source} to {platform-target}`), key stakeholders (placeholder `TBD - to be populated after discovery`), locations/regions served, link to primary contact info (placeholder).

Example body opener:

```markdown
## Overview
Acme Corp, a regional distributor of industrial supplies...

## Migration Context
**Source Platform**: {Platform Source}
**Target Platform**: {Platform Target}
**Scope**: Full platform replacement with integration to the ERP
```

## Step 3b — Source-platform entity page

Path: `wiki/{group}/{company-slug}/entities/{platform-source-slug}.md`. Slug derivation: e.g. `Shopify Plus → shopify-plus`.

Frontmatter:

```yaml
---
title: "{Platform Source Name}"
type: entity
client: {company-slug}
entity-type: source-platform
status: active
created: {today}
updated: {today}
related:
  - {company-slug}
---
```

Body must cover: brief platform description, current version/edition (if known), known capabilities (placeholder `To be detailed from discovery`), known limitations (placeholder), integration points (placeholder `To be documented from pipeline analysis`).

## Step 4 — Initial-context ingest (only if `initial-context` was provided)

### 4a. Parse the source file

Read the file (supports `.txt`, `.md`, `.pdf`, transcripts). Extract:

- **Mentioned features** — e.g. "We use the current platform for budgets, quotes, pricing..."
- **Integrations** — e.g. "The current platform syncs with the ERP and the CRM..."
- **Known gaps** — e.g. "We can't do dynamic discounts", "No subscription support..."
- **Open questions** — e.g. "How will payment tokenization work?", "Multi-currency scope?"
- **Business context** — company size, locations, key business drivers.

### 4b. Feature stub template

Path: `wiki/{group}/{company-slug}/features/{feature-slug}.md`. Template: `wiki/_schema/templates/feature.md`.

```yaml
---
title: "{Feature Name}"
type: feature
client: {company-slug}
status: stub
sources: [{initial-context}]
created: {today}
updated: {today}
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

### 4c. Integration stub template

Path: `wiki/{group}/{company-slug}/integrations/{integration-slug}.md`.

```yaml
---
title: "{System Name} Integration"
type: integration
client: {company-slug}
status: stub
sources: [{initial-context}]
created: {today}
updated: {today}
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
[Implications for the migration to {Platform Target}, if known]

## Status
Stub created from initial context. Details to be extracted in discovery phase.
```

### 4d. Question stub template

Path: `wiki/{group}/{company-slug}/questions/{question-slug}.md`.

```yaml
---
title: "{Question}"
type: question
client: {company-slug}
status: open
priority: P2
sources: [{initial-context}]
created: {today}
updated: {today}
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

Adjust `priority` based on context urgency (P1 if explicitly blocking, P3 if speculative).
