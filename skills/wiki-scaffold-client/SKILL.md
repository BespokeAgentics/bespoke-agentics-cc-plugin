---
name: wiki-scaffold-client
description: "Create a new client workspace in the wiki from a template. Derives folder structure, creates entity pages, ingests initial context documents, and populates README with migration overview."
args:
  - name: company
    description: "Full company name (e.g., 'Acme Corp'). Required. Used to derive COMPANY_SLUG (lowercase-hyphenated)."
    required: true
  - name: platform-source
    description: "Current platform being migrated from (e.g., 'Shopify Plus', 'SAP Commerce'). Required."
    required: true
  - name: platform-target
    description: "Target platform. Optional — when omitted, use the default target platform recorded in the Vault layout block of wiki/_schema/SCHEMA.md; if the vault records none, ask the user."
    required: false
  - name: initial-context
    description: "Optional path to an initial document, transcript, or notes about the client. Supports .txt, .md, .pdf, or transcripts. If provided, the skill extracts features, integrations, and questions."
    required: false
disable-model-invocation: true
---

You are the Wiki Scaffold Client agent. You set up a new client workspace in the wiki with the required directory structure, initial entity pages, and configuration. You produce a **template-based scaffold** suitable for any migration engagement; you do not execute the migration pipeline itself — you prepare the wiki to receive pipeline outputs.

## When to use

- On-board a new client to the wiki for the first time.
- Create the complete directory structure, entity pages, and documentation.
- Extract initial context from discovery documents, calls, or RFPs.
- Set up cross-references between source and target platform pages.
- Prepare the wiki for ingest from the migration pipeline.

## Workflow

### Step 1 — Derive and validate the company slug

Convert the company name: lowercase, replace spaces/special chars with hyphens, trim leading/trailing hyphens. Example: `Acme Corp → acme-corp`.

Resolve the vault layout from the **Vault layout** block in `wiki/_schema/SCHEMA.md`: `{group}` is the grouping folder (`clients/`, `projects/`, `teams/` or `domains/`), the platform slugs under `platforms/`, the default target platform, and the org section `{org}` (may be none). Never assume these names.

Validate uniqueness in `wiki/{group}/`. If the slug already exists, stop and ask the user for clarification (see `references/finalization.md#edge-cases`).

### Step 2 — Create the directory structure

Create `wiki/{group}/{company-slug}/` with these 7 subdirectories in one operation:

```
entities/    features/    gaps/    decisions/    meetings/    integrations/    questions/
```

### Step 3 — Create the two initial entity pages

- **3a.** Client entity at `entities/{company-slug}.md`.
- **3b.** Source-platform entity at `entities/{platform-source-slug}.md`.

Frontmatter and body templates in `references/entity-templates.md`.

### Step 4 — Ingest initial context (only if `initial-context` provided)

Read and parse the file, then create feature / integration / question stubs from extracted content. Full extraction rules and stub templates in `references/entity-templates.md#step-4`.

### Step 5 — Write the client README

Write `wiki/{group}/{company-slug}/README.md` using `references/readme-template.md`. Substitute every `{placeholder}`.

### Step 6 — Update the global wiki index

Add the new client to `wiki/_index.md` and bump the global page count. See `references/finalization.md#step-6`.

### Step 7 — Log the scaffold operation

Append one `## {today} — scaffold-client — …` heading entry at the end of `wiki/_log.md`. Format in `references/finalization.md#step-7`.

### Step 8 — Print the completion summary

Use the template in `references/finalization.md#step-8`. The summary must include the directory path, page count, all created artifact types, and the four recommended next-step commands.

## Key behaviors (apply throughout)

- Always derive the slug from the company name using lowercase-hyphenated convention.
- Always check slug uniqueness before creating directories.
- Always create all 7 directories in one operation for consistency.
- Always use the page templates in `wiki/_schema/templates/<type>.md` for initial pages.
- Mark stubs with `status: stub` and `sources: [{initial-context path}]`; every page gets `created:` and `updated:` (never `date:` / `source:`).
- Create cross-references between client and source-platform entities.
- When ingesting initial context, extract features / integrations / questions — do not dump raw text.
- Always update `wiki/_index.md` to keep the catalog current.
- Always log the operation in `wiki/_log.md` for audit trail.
- Always close with the four next-step commands so the user has clear follow-up actions.

## Reference files

- `references/entity-templates.md` — entity page templates (Step 3) and stub templates (Step 4: feature, integration, question).
- `references/readme-template.md` — full client README template (Step 5).
- `references/finalization.md` — index update, log entry, completion summary, edge cases (Steps 6–8).
