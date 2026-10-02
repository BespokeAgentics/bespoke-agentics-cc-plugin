# Finalization

## Step 6 — Update the global wiki index

Update `wiki/_index.md`:

1. Find the section for the vault's grouping folder (`## Clients`, `## Projects`, … — per `_schema/SCHEMA.md`).
2. Add a new subsection:

```markdown
### {Company Name}
- [[{company-slug}]] — Client overview
- [[{company-slug}/entities/{platform-source-slug}]] — Source platform
- [Status: Workspace scaffolded, {count} pages]
```

3. Update the global page count at the top of the index.

## Step 7 — Log the scaffold operation

Append at the end of `wiki/_log.md`, in the vault's heading format:

```markdown
## {today} — scaffold-client — {company-slug}: workspace created

- Path: wiki/{group}/{company-slug}/ (7 directories)
- Pages created: {count} ({list of entity/stub pages})
- Initial context: {path, or "none"}
```

## Step 8 — Print completion summary

```markdown
## New Client Workspace Created: {Company Name}

Directory: wiki/{group}/{company-slug}/
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

1. **Analyze a Discovery Meeting** (any meeting-analysis pipeline that writes markdown analysis files, e.g.)
   ```bash
   /bespoke-agentics:video-to-deliverables '{recording}' '{company}' '{meeting-label}' --profile meeting
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

**Workspace Ready**: wiki/{group}/{company-slug}/README.md
```

## Edge cases

- **Duplicate company name** — if the slug already exists, ask for clarification ("Is this Acme Corp (acme-corp) or a different company?").
- **Non-English company names** — transliterate to ASCII, then slug (e.g. `Société Générale → societe-generale`).
- **Very long company names** — use the common short form (e.g. `International Business Machines → ibm`).
- **Special characters in platform names** — normalize to slug (e.g. `SAP Commerce Cloud → sap-commerce-cloud`).
