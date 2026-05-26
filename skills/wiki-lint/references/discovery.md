# Discovery & parse

Steps 1–2 of the lint workflow. Run these once at the start before any checks.

## Step 1 — Discover all wiki pages

```bash
find wiki/ -name "*.md" \
  -not -path "wiki/_schema/*" \
  -not -path "wiki/_*" \
  -type f
```

Excludes templates (`wiki/_schema/templates/`), index files (`wiki/_index.md`, `wiki/_log.md`), and prior lint reports.

Apply the scope filter from the skill's `scope` argument:

- `full` — keep all pages.
- `client:{slug}` — keep only `wiki/clients/{slug}/**/*.md`.
- `recent` — keep only pages whose mtime is within the last 7 days.

For each discovered page record: file path, mtime, parsed YAML frontmatter (first 20 lines), inferred page type (from frontmatter `type:` or path).

## Step 2 — Parse frontmatter and content

For every page extract:

**Frontmatter fields**
- `type` — one of: feature, gap, decision, question, meeting, entity, integration
- `client` — client slug (or empty for platform-level pages)
- `status`, `created`, `updated`, `sources`, `tags`

**Content analysis**
- All wiki-links — `[[slug|Display]]` or `[[slug]]`.
- All markdown links — `[text](url)`.
- Section/header counts.
- Mentioned entities (features, gaps, etc.) by name.

**Validity check**
- Does the frontmatter parse as valid YAML?
- Are required fields present?
- Are dates `YYYY-MM-DD`?

Pages that fail to parse: log the error, skip later validation for that page, continue.
