# Steps 1–2 — Discover & parse Confluence exports

## Step 1 — Discover Confluence exports

If `confluence-dir` is provided:

```bash
find {confluence-dir} -type f \( -name "*.html" -o -name "*.confluence" \)
```

Else auto-discover under the company tree:

```bash
find . -path "*/{company-title}/meetings/*/confluence/*" -type f \( -name "*.html" -o -name "*.confluence" \)
```

For each export, note: file path, date (from filename or file metadata), document type (gap analysis, feature comparison, meeting summary, …).

## Step 2 — Parse Confluence documents

### Gap analysis tables

Columns to expect: Feature #, Functionality, Decision, Status, Notes, Effort.

```
| Feature # | Functionality     | Decision    | Status      | Notes              |
|-----------|-------------------|-------------|-------------|--------------------|
| F-001     | Budget Management | Custom LWC  | In Progress | Estimated 6 weeks  |
| F-002     | Catalog Filtering | OOTB        | Approved    | No gaps            |
```

For each row extract:
- **Feature ID / Name** → normalized wiki slug.
- **Decision badge** → decoded to wiki value via the badge map (see `report-and-sync.md#decision-badge-mapping`).
- **Status** — current implementation status.
- **Effort** — story points / time estimate (if present).
- **Notes** — additional details or risks.

### Summary tables

For feature/gap summaries: extract every entity name + slug, every decision status + rationale, every open question / risk.

### Prose content

For narrative sections: extract explicit decisions, identified gaps/risks, mentioned assumptions, action items, and next steps.
