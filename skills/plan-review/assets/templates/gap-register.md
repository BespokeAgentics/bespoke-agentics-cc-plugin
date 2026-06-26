---
type: gap-register
status: draft
date: {{DATE}}
source: plan-review
artifact: {{ARTIFACT_PATH}}
related: []
---

# {{ARTIFACT_TITLE}} — Gap & Ambiguity Register

Status legend: 🟢 OOTB · 🔵 Config · 🟡 Custom Dev · 🔴 Gap · ⚪ TBD · 🟣 3rd Party

<!-- One row per open item from the review. Group by color, 🔴 first. The "Evidence" column carries
     the artifact quote and/or file:line so each row stands on its own. "Priority" mirrors the
     interview (P0/P1/P2). This table is the author's action list. -->

## 🔴 Gaps (missing & needed)

| ID | Item | Priority | Evidence (artifact / code) | Recommendation | Owner |
|----|------|----------|----------------------------|----------------|-------|
| F1 | {{second auth chain not covered}} | P0 | "update mw.ts" / `edge/auth.ts:12` | add a task for the edge chain | {{name}} |

## 🟡 Custom development (real work the plan under-scoped)

| ID | Item | Priority | Evidence | Recommendation | Owner |
|----|------|----------|----------|----------------|-------|

## ⚪ TBD / ambiguities (need a decision)

| ID | Item | Priority | Evidence | Assumption taken if unanswered | Owner |
|----|------|----------|----------|--------------------------------|-------|

## 🟣 Third-party candidates

| ID | Item | Priority | Evidence | Options | Owner |
|----|------|----------|----------|---------|-------|

## 🔵 Configuration / 🟢 OOTB (already covered / trivial)

| ID | Item | Evidence | Note | Owner |
|----|------|----------|------|-------|
