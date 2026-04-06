---
name: "wiki:init"
description: "Initialize a brand-new Karpathy-style LLM wiki vault from scratch. Creates the Obsidian vault, schema, templates, indexes, and platform stubs. Optionally scaffolds the first client."
argument-hint: "[--wiki-dir '<path>'] [--first-client '<company>' --platform-source '<platform>'] [--platform-target '<platform>']"
allowed-tools: Agent, Bash, Read, Write, Edit, Glob, Grep
---

# Wiki Init

You are the Wiki Init Orchestrator. You create a brand-new Karpathy-style LLM wiki vault from scratch.

## Arguments

Parse from `$ARGUMENTS`:

```
[--wiki-dir '<path>'] [--first-client '<company>' --platform-source '<platform>'] [--platform-target '<platform>']
```

- `--wiki-dir` (optional): Path to create the wiki (default: `./wiki`)
- `--first-client` (optional): Company name for the first client to scaffold
- `--platform-source` (optional): Source platform for the first client (required if `--first-client` is provided)
- `--platform-target` (optional): Target platform (default: `Salesforce B2B Commerce`)

If `$ARGUMENTS` is empty, use all defaults (creates `./wiki` with no first client).

If `--first-client` is provided without `--platform-source`, print this and stop:

```
Usage: /wiki:init [--wiki-dir '<path>'] [--first-client '<company>' --platform-source '<platform>'] [--platform-target '<platform>']

Arguments:
  --wiki-dir          Path for the wiki vault (default: ./wiki)
  --first-client      Company name for first client (optional)
  --platform-source   Source platform (required with --first-client)
  --platform-target   Target platform (optional, default: Salesforce B2B Commerce)

Examples:
  /wiki:init
  /wiki:init --wiki-dir './knowledge-base'
  /wiki:init --first-client 'Acme Corp' --platform-source 'Shopify Plus'
  /wiki:init --first-client 'Boston Beer Company' --platform-source 'MerchTank' --platform-target 'Salesforce B2B Commerce'
```

## Derived Variables

```
WIKI_DIR            = --wiki-dir value or ./wiki
TODAY               = current date (YYYY-MM-DD)
```

## Process

### Phase 1: Pre-flight Validation

1. **Check vault does NOT exist**: If `{WIKI_DIR}` already exists, abort with:

   "Wiki already exists at {WIKI_DIR}. Use /wiki:new-client to add a client, or delete the directory to start fresh."

2. **Validate first-client args**: If `--first-client` given without `--platform-source`, abort with usage.

3. **Check parent directory exists**: Ensure the parent of `{WIKI_DIR}` is writable.

Report pre-flight status:
```
=== Wiki Init ===
Wiki directory:  {WIKI_DIR}
First client:    {--first-client or "none"}
Platform source: {--platform-source or "n/a"}
Platform target: {--platform-target or "Salesforce B2B Commerce"}
Status:          ✓ Ready to initialize
```

### Phase 2: Invoke wiki-init Skill

Launch the skill:

```
Skill: wiki-init
Parameters:
  wiki-dir: {WIKI_DIR}
  first-client: {--first-client or ""}
  platform-source: {--platform-source or ""}
  platform-target: {--platform-target or "Salesforce B2B Commerce"}
```

The skill handles:
- Creating the complete vault directory structure
- Writing all 5 `.obsidian/` config files
- Writing `_schema/SCHEMA.md` (the full schema document)
- Creating all 7 page templates in `_schema/templates/`
- Creating `_index.md` and `_log.md`
- Creating platform stub pages (salesforce-b2b-commerce, salesforce-lwc)
- Creating Verndale process stubs (wiki-maintenance, migration-analysis-pipeline)
- Optionally scaffolding the first client via wiki-scaffold-client

Wait for skill completion.

### Phase 3: Report Summary

After skill completes, print summary:

```
================================================================
  Wiki Initialized Successfully
================================================================

Vault:          {WIKI_DIR}
Obsidian:       .obsidian/ (5 config files)
Schema:         _schema/SCHEMA.md + 7 templates
Global files:   _index.md, _log.md
Platform stubs: salesforce-b2b-commerce, salesforce-lwc
Process stubs:  wiki-maintenance, migration-analysis-pipeline

{If first client scaffolded:}
First Client:   {first-client} ({client-slug})
  Platform:     {platform-source} → {platform-target}
  Pages:        {N} initial pages

Total files created: {count}

Next Steps:
  1. Open the vault in Obsidian
  2. Add a client: /wiki:new-client '<company>' '<platform-source>'
  3. Ingest a meeting: /wiki:ingest-meeting '<company>' '<meeting-dir>' '<label>'
  4. Check health: /wiki:lint --scope full
================================================================
```

## Error Handling

- If wiki directory already exists, abort with clear message
- If parent directory doesn't exist, attempt to create it
- If first-client provided without platform-source, abort with usage
- If scaffold-client skill fails, log error but report what was created
- If any file write fails, report and continue with remaining files

## Success Criteria

- All `.obsidian/` config files present and valid JSON
- `_schema/SCHEMA.md` contains complete schema definition
- All 7 templates created in `_schema/templates/`
- `_index.md` and `_log.md` initialized
- Platform stubs created with real content
- Verndale process stubs created
- If first client requested: client workspace fully scaffolded
- Summary printed with file counts and next steps
