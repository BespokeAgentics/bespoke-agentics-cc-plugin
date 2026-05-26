# Steps 5–6 — Finalize: frontmatter, ingest log, output

## Step 5 — Update frontmatter on all touched pages

For every page you updated:

1. **`updated:`** — set to today's date.
2. **`sources:`** — append the document path:

   ```yaml
   sources:
     - /previous/source/path
     - {document-path}  # NEW
   ```

3. **`tags:`** — add the document-type tag if not already present:

   ```yaml
   tags:
     - meeting-label
     - email   # or pdf, slack, spec
     - {document-type}-{date-if-applicable}
   ```

## Step 6 — Append ingest log entry

Prepend to `wiki/_log.md`:

```markdown
## Lightweight Ingest — {document-type} — {today}

**Document**: {document-path}
**Company**: {company}
**Type**: {email|pdf|spec|slack|other}

**Classification**: {Decision|Clarification|Scope Change|Risk Alert|Evidence|Question|Approval}

**Pages Updated**:
- [[feature-slug|Feature Name]]: {brief change summary}
- [[gap-slug|Gap Name]]: {brief change summary}
- [[decision-slug|Decision Name]]: {brief change summary}

**Pages Created**: {none|list if any}

**Contradictions Found**: {none|list}

**Key Takeaway**: {One-sentence summary of what this document added to our knowledge}

**Status**: ✓ Complete
```

Also update `wiki/_index.md` if any NEW pages were created (same format as the meeting-ingest entries).

## Output format

```
✓ Complete — {X} pages updated, {Y} pages created, {Z} contradictions found

Updated:
- [[feature-slug|Feature Name]]
- [[gap-slug|Gap Name]]

Created:
- [[decision-slug|Decision Name]]

Contradictions:
- {Page}: {Brief description of conflict}

Log Entry:
{The markdown entry that was appended to wiki/_log.md}
```
