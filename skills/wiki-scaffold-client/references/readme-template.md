# Client README template

Write at `wiki/{group}/{company-slug}/README.md` (`{group}` = the grouping folder in `_schema/SCHEMA.md`).

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

Migrating from **{Platform Source}** to **{Platform Target}**.

[If platform-target differs from the vault's default target platform (per `_schema/SCHEMA.md`), note the rationale here.]

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

Run the project's meeting-analysis pipeline on the recording or transcript so it writes markdown analysis files into a meeting folder — for example:

```bash
/bespoke-agentics:video-to-deliverables 'Acme/meetings/2026-03-15/recording.mp4' 'acme-corp' 'discovery-01' --profile meeting
```

### Step 2 — Ingest Pipeline Outputs

```bash
/wiki:ingest-meeting '{company}' '{meeting-dir}' '{meeting-label}'
```

### Step 3 — Add Existing Documents

```bash
/wiki:ingest-document '{company}' '{document-path}' '{type}'
```

Types: `email`, `pdf`, `spec`, `slack`, `other`.

Example:

```bash
/wiki:ingest-document 'acme-corp' 'Documents/Acme_Requirements.pdf' 'spec'
```

### Step 4 — Validate the Wiki

```bash
/wiki:lint --scope client:{company-slug}
```

Reports: missing cross-references, conflicting information, stale or incomplete pages, recommendations.

## Contact & Team

**Account Lead**: [TBD — update after kickoff]
**Technical Lead**: [TBD — update after kickoff]
**{Org Name} Team**: [Assign team members as they join] _(org section per `_schema/SCHEMA.md`; omit this line if the vault has none)_

## Key Decisions

[This section will populate as decisions are made]

---

**Last Updated**: {today}
**Created**: {today}
```
