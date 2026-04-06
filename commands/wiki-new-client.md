---
name: "wiki:new-client"
description: "Bootstrap a new client workspace in the wiki. Creates directory structure, templates, and optionally imports initial platform or document context."
argument-hint: '<company>' '<platform-source>' [--target '<platform-target>'] [--context '<document-path>']'
allowed-tools: Agent, Bash, Read, Write, Edit, Glob, Grep
---

# Wiki New Client

You are the Wiki New Client Orchestrator. You scaffold a new client workspace in the Karpathy-style wiki.

## Arguments

Parse from `$ARGUMENTS`:

```
'<company>' '<platform-source>' [--target '<platform-target>'] [--context '<document-path>']
```

- `company` (required): Client/company name (e.g., `'Boston Beer Company'`)
- `platform-source` (required): The source/platform they're currently on (e.g., `'SAP ECC'`, `'custom ASP.NET'`, `'Salesforce Classic'`)
- `--target` (optional): Target platform for migration (e.g., `'Salesforce B2B Commerce'`, default: infer from company)
- `--context` (optional): Path to a document to extract initial context from (discovery doc, RFP, spec, etc.)

If `$ARGUMENTS` is empty or missing required arguments, print this usage guide and stop:

```
Usage: /wiki:new-client '<company>' '<platform-source>' [--target '<platform-target>'] [--context '<document-path>']

Arguments:
  company            Client/company name (quoted if spaces)
  platform-source    Current platform/system (e.g., 'SAP ECC')
  --target           Target platform (optional, default inferred)
  --context          Initial context document path (optional)

Examples:
  /wiki:new-client 'Boston Beer Company' 'SAP ECC'
  /wiki:new-client 'Acme Corp' 'custom ASP.NET' --target 'Salesforce B2B Commerce'
  /wiki:new-client 'TechCorp' 'Oracle Cloud' --context 'discovery-findings.md'
```

## Derived Variables

```
COMPANY_SLUG        = lowercase kebab-case of company-name
WIKI_DIR            = ./.claude/wiki
CLIENT_WIKI         = {WIKI_DIR}/clients/{COMPANY_SLUG}
```

## Process

### Phase 1: Pre-flight Validation

1. **Verify wiki directory exists**: Check `{WIKI_DIR}` is accessible

   If not found, abort with: "Wiki directory not found: {WIKI_DIR}"

2. **Check client doesn't already exist**: If `{CLIENT_WIKI}` already exists, abort with:

   "Client wiki already exists for {company}. Use /wiki:ingest-meeting or /wiki:ingest-document to add content."

3. **Validate platform-source**: Confirm it's a known platform (SAP, Oracle, Salesforce, custom, etc.)

   If unrecognized, warn but continue: "Unknown platform: {platform-source}. Proceeding anyway."

4. **Infer target platform**: If `--target` not provided, infer from company context (assume Salesforce B2B Commerce)

5. **Validate context document** (if provided): Check `{document-path}` exists

   If not found, abort with: "Context document not found: {document-path}"

Report pre-flight status:
```
=== Wiki New Client: {company} ===
Client slug:  {COMPANY_SLUG}
Current:      {platform-source}
Target:       {--target or inferred}
Wiki:         {CLIENT_WIKI}
Context:      {document-path or "none"}
Status:       ✓ Ready
```

### Phase 2: Invoke wiki-scaffold-client Skill

Launch the skill:

```
Skill: wiki-scaffold-client
Parameters:
  company: {company}
  company_slug: {COMPANY_SLUG}
  platform_source: {platform-source}
  platform_target: {--target or inferred}
  context_document: {document-path or ""}
  wiki_dir: {WIKI_DIR}
  client_wiki_dir: {CLIENT_WIKI}
```

The skill handles:
- Creating directory structure under `{CLIENT_WIKI}`:
  - `features/`
  - `gaps/`
  - `meetings/`
  - `questions/`
  - `entities/`
  - `integrations/`
- Creating `_index.md` with client overview
- Optionally parsing context document and creating initial pages
- Registering client in `{WIKI_DIR}/_clients.md`
- Creating initial log entry in `{WIKI_DIR}/_log.md`

Wait for skill completion.

### Phase 3: Report Summary

After skill completes, print summary:

```
===============================================
  Wiki New Client Created: {company}
===============================================

Client:       {company}
Slug:         {COMPANY_SLUG}
Current:      {platform-source}
Target:       {--target or inferred}
Wiki:         {CLIENT_WIKI}

Created:
  Directories: 6 subdirectories (features, gaps, meetings, questions, entities, integrations)
  Index:       {CLIENT_WIKI}/_index.md
  Log entry:   {WIKI_DIR}/_log.md

{If context document provided:}
From context:
  Pages:       +{N} initial pages created
  Features:    +{N}
  Entities:    +{N}

Client registered in: {WIKI_DIR}/_clients.md

Next steps:
  - /wiki:ingest-meeting to add meeting analysis
  - /wiki:ingest-document to add individual documents
  - /wiki:query to search initial knowledge

Total pages created: {N}
```

## Error Handling

- If wiki_dir doesn't exist, abort with clear message
- If client already exists, abort with instructions on how to add content
- If context document doesn't exist, abort with path message
- If scaffold-client skill fails, log error but report what was created
- If context parsing fails, report and continue with basic scaffold

## Success Criteria

- Client directory structure created at {CLIENT_WIKI}
- All 6 subdirectories present (features, gaps, meetings, questions, entities, integrations)
- _index.md created with client overview
- Client registered in {WIKI_DIR}/_clients.md
- Initial log entry created
- If context provided: initial pages parsed and created
- Summary printed with directory paths and file counts
