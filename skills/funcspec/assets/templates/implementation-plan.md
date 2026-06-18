---
type: plan
status: draft
date: {{DATE}}
source: funcspec
workspace: {{WORKSPACE}}
related: []
---

# {{APP_NAME}} — Implementation Plan

## Architecture summary

**Frontend:** {{STACK — from the workspace, e.g. React 18 + TS + Tailwind v4, Untitled UI conventions}}
**Backend approach:** {{From Stage-1: greenfield REST/GraphQL | existing API | BaaS}}
**Auth:** {{MODEL + boundary notes}}

Key decisions:

1. {{DECISION}} — {{RATIONALE}}

## Data model

<!-- One H3 per merged entity -->

### {{Entity}}

| Field | Type | Notes |
|-------|------|-------|
| {{name}} | {{type}} | {{enum values / nullable / formatting concerns}} |

**Relations:** {{e.g. belongsTo Customer, hasMany LineItem}}
**Open conflicts:** {{none | link to gap-register IDs}}

## API surface

<!-- Grouped by entity. For existing-API backends add a "Maps to" column. -->

### {{Entity}}

| Operation | Sketch | Auth | Consumed by |
|-----------|--------|------|-------------|
| {{intent}} | `{{METHOD /path?params}}` | {{yes/role}} | {{page-ids}} |

## Frontend wiring

<!-- One H3 per page -->

### {{Page title}} ({{page-id}})

- **State:** {{server state (which queries) / local UI state / URL state (filters, pagination, tabs)}}
- **Data contracts:** {{operations consumed, fetch timing, invalidation triggers}}
- **Forms & validation:** {{rules per field, submit behavior, dirty-state handling}}
- **States to implement:** {{loading/empty/error/... — note which lack designs}}

## Shared services

### {{Service}}

**Requirement:** {{what ≥2 pages imply}}
**Approach:** {{suggested implementation}}
**Build vs buy:** {{🟣 candidate? note options}}

## Phasing

### Phase 1 — P0

**Features:** {{list}}
**Demonstrable outcome:** {{what a stakeholder can click through at phase end}}

### Phase 2 — P1

…

### Phase 3 — P2

…
