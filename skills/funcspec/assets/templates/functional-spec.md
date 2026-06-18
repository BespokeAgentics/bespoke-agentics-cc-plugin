---
type: spec
status: draft
date: {{DATE}}
source: funcspec
workspace: {{WORKSPACE}}
related: []
---

# {{APP_NAME}} — Functional Specification

## Overview

**Purpose:** {{PURPOSE}}
**Users & roles:** {{ROLES}}
**Backend reality:** {{BACKEND}}
**Auth model:** {{AUTH}}

<!-- One H2 per composite (first), then per page. Repeat the block below. -->

## {{PAGE_TITLE}} ({{page-id}})

{{SUMMARY}}

**User goals:** {{GOALS}}

| Element | Implied behavior | Confidence | Evidence |
|---------|------------------|------------|----------|
| {{ELEMENT}} | {{BEHAVIOR}} | {{high/medium/low}} | {{EVIDENCE}} |

**Entities:** {{ENTITY_LIST_WITH_FIELD_COUNTS}}
**Operations:** {{OP_LIST}}
**Navigation:** {{NAV_LIST}}
**States:** {{STATES — flag "implied but not designed" items}}
**Roles/permissions:** {{ROLE_CUES_OR_NONE}}

## Explicitly out of scope

<!-- Cut features (Stage-2) + Stage-1 non-goals, each with one-line rationale -->

- {{ITEM}} — {{WHY}}
