# Client README template

Write at `wiki/clients/{company-slug}/README.md`.

```markdown
# {Company Name}

## Migration Overview

| Attribute | Value |
|-----------|-------|
| **Client** | {Company Name} |
| **Source Platform** | {Platform Source} |
| **Target Platform** | {Platform Target} |
| **Status** | Workspace scaffolded {today} |

## Scope

Migrating from **{Platform Source}** to **{Platform Target}** B2B commerce platform.

[If platform-target differs from default, note the rationale here.]

## Workspace Structure

This wiki section contains:
- **entities/** — Client organization and systems involved
- **features/** — Business capabilities and features to migrate
- **gaps/** — Known gaps or limitations in the current platform
- **decisions/** — Design decisions and scope resolutions
- **meetings/** — Meeting notes and discovery summaries
- **integrations/** — External system integrations
- **questions/** — Open questions awaiting resolution

## Current Status

**Pages Created**: {count}
- Entity pages: 2 (Client + Source Platform)
- Feature stubs: {count} (from initial context)
- Integration stubs: {count} (from initial context)
- Question pages: {count} (from initial context)

**Processing Status**: Initial scaffold complete. Ready for pipeline ingest.

## Key Pages

- [[{company-slug}]] — Client overview
- [[{platform-source-slug}]] — Source platform entity
- [[README]] — This file

## Next Steps

1. **Run the migration pipeline** on the first meeting recording or discovery document.
2. **Ingest pipeline outputs** into the wiki using structured ingest workflows.
3. **Add existing documents** (emails, specs, RFPs) via document ingest.
4. **Run wiki lint** to check for inconsistencies and missing information.

See the Recommended Next Steps section below.

## Recommended Next Steps

### Step 1 — Analyze a Discovery Meeting

```bash
/verndale:migration-pipeline '{meeting-dir}' '{company}' '{meeting-label}'
```

Example:

```bash
/verndale:migration-pipeline 'BostonBeerCompany/meetings/2026-03-15/' 'Boston Beer Company' 'discovery-01'
```

### Step 2 — Ingest Pipeline Outputs

```bash
/wiki:ingest-meeting '{company}' '{meeting-dir}' '{meeting-label}'
```

### Step 3 — Add Existing Documents

```bash
/wiki:ingest-document '{company}' '{document-path}' '{type}'
```

Types: `spec`, `rfp`, `email-thread`, `requirements`, `architecture`, etc.

Example:

```bash
/wiki:ingest-document 'Boston Beer Company' 'Documents/BBC_Requirements.pdf' 'spec'
```

### Step 4 — Validate the Wiki

```bash
/wiki:lint --scope client:{company-slug}
```

Reports: missing cross-references, conflicting information, stale or incomplete pages, recommendations.

## Contact & Team

**Account Lead**: [TBD — update after kickoff]
**Technical Lead**: [TBD — update after kickoff]
**Verndale Team**: [Assign team members as they join]

## Key Decisions

[This section will populate as decisions are made]

---

**Last Updated**: {today}
**Created**: {today}
```
