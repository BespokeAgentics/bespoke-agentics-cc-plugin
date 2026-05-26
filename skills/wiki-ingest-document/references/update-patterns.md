# Steps 3–4 — Update existing pages & create new ones (sparingly)

## Step 3 — Update existing pages

For each affected existing page, use the Edit tool. **Never overwrite; always merge.**

### Pattern: adding evidence to an existing page

```markdown
## Evidence from {document-type}: {document-identifier}

Source: {document-path}
Date: {date-if-available}

{Summary of what this document adds to our understanding}

- New insight: {specific finding}
- Reference: {exact quote or paraphrase with page/section if applicable}
```

### Pattern: updating decision status

Update frontmatter:

```yaml
decision: {new-status}  # Updated {today} per {document-type}: {doc-id}
```

Add content:

```markdown
## Decision Update — {document-date}

**Status**: {ootb|config|custom|gap|tbd|third-party}
**Rationale**: From {document-type}: {Brief explanation}
**Source**: {document-path}
```

### Pattern: resolving an open question

In the question page frontmatter:

```yaml
status: resolved  # Updated {today}
```

Add content:

```markdown
## Resolution — {document-date}

**Answer**: {The answer provided}
**Source**: {document-type}: {doc-id}
**Resolved by**: {Person or team if mentioned}
```

### Pattern: noting a contradiction

Add a `⚠️ Contradiction Notice` section to the affected page:

```markdown
## ⚠️ Contradiction Notice — {document-date}

This document contradicts or modifies previous information:

**Previous Information** (from {old-source}):
{Previous statement}

**New Information** (from {new-document-type}):
{New statement}

**Resolution**: {Explanation of the discrepancy or which version is current}
**Updated by**: {document-path}
```

### Pattern: adding a new constraint or requirement

```markdown
## New Constraint — {document-date}

**Constraint**: {Description}
**Source**: {document-type}
**Impact**: {How this affects implementation or estimation}
**Reference**: {Exact quote from document}
```

## Step 4 — Create new pages (sparingly)

Only create a new page if ALL of the following are true:

1. The document mentions an entity that does NOT yet exist in the wiki.
2. The entity is significant enough to warrant a dedicated page (not just a passing mention).
3. The document provides enough detail to populate at least a stub.
4. The entity is one of the core types: feature, gap, decision, or question.

Do NOT create pages for:
- Passing mentions of vendors or systems.
- Unconfirmed hypotheticals.
- Entities already covered by an existing page under a different name.

### New decision page

Path: `wiki/clients/{company}/decisions/{decision-slug}.md`. Template: `wiki/_schema/templates/decision.md`.

Frontmatter:

```yaml
type: decision
client: {company}
status: approved  # (or other accurate status)
created: {today}
updated: {today}
sources: [{document-path}]
tags: [{document-type}, ingest]
```

Content sections:
- **Decision** — one-sentence statement.
- **Context** — why was this decision made? What prompted it?
- **Rationale** — the reasoning behind it.
- **Impact** — what changes as a result?
- **Related entities** — links to affected features, gaps, or questions.
- **Source** — reference the document.

### New question page

Only if the document poses a significant, unresolved question. Use `wiki/_schema/templates/question.md`. Populate frontmatter + content with the question, why it matters, and a reference to the document.

## Example scenarios

### Email with a decision

- doc: `/data/emails/2024-04-01-budget-approval.eml`, type `email`, summary `"Client approved custom LWC for dynamic budget enforcement"`.
- Affected: `features/budget-enforcement.md` (update decision status), `gaps/budget-enforcement-gap.md` (mark gap as having resolution), possibly create `decisions/budget-custom-lwc.md`.
- Updates: feature gets "Decision Update" section, `decision: custom`, `updated` date refreshed; gap notes resolution + links to decision; new decision page sets `status=approved`, `source=email`.
- Log: "Email from client CTO approving custom LWC scope".

### PDF spec clarifying a feature

- doc: `/data/specs/BudgetingProcess_v2.1.pdf`, type `pdf`.
- Affected: `features/budget-approval-workflow.md` only.
- Updates: add "Evidence from PDF" section with workflow details and rules; append the PDF to `sources`; refine feature description from the spec.
- Log: "PDF spec adds detailed workflow and business rules".

### Slack message raising a question

- doc: `/data/slack/2024-04-05-tokenization-q.slack`, type `slack`.
- Affected: check if `questions/payment-tokenization.md` exists. If yes → add the slack message as a new reference; if no → create a question page only if the question is significant enough.
- Updates: question gets "Clarification needed on tokenization approach (Slack, 2024-04-05)"; link to related payment-decision pages.
- Log: "Slack message raises question about tokenization implementation".
