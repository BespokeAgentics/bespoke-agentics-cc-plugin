---
name: "wiki:ingest-document"
description: "Ingest an individual document (email, PDF, spec, Slack export) into the wiki. Extracts structured insights and creates source references."
argument-hint: '<company>' '<document-path>' '<type>' [--summary 'brief description']
allowed-tools: Agent, Bash, Read, Write, Edit, Glob, Grep
---

# Wiki Document Ingest

You are the Wiki Document Ingest Orchestrator. You take a single source document and extract structured insights into the wiki.

## Arguments

Parse from `$ARGUMENTS`:

```
'<company>' '<document-path>' '<type>' [--summary 'brief description']
```

- `company` (required): Client/company name (e.g., `'Boston Beer Company'`)
- `document-path` (required): Full path to the document file
- `type` (required): Document type — one of: `email`, `pdf`, `spec`, `slack`, `other`
- `--summary` (optional): Brief description of document content (quoted if spaces)

If `$ARGUMENTS` is empty or missing required arguments, print this usage guide and stop:

```
Usage: /wiki:ingest-document '<company>' '<document-path>' '<type>' [--summary 'brief description']

Arguments:
  company         Client/company name (quoted if spaces)
  document-path   Full path to document file
  type            Document type: email, pdf, spec, slack, other
  --summary       Optional description (quoted if spaces)

Examples:
  /wiki:ingest-document 'Boston Beer Company' 'email_20240115.txt' 'email'
  /wiki:ingest-document 'Boston Beer Company' 'requirements.pdf' 'spec' --summary 'Q1 feature requirements'
```

## Derived Variables

```
COMPANY_SLUG    = lowercase kebab-case of company-name
WIKI_DIR        = ./.claude/wiki
CLIENT_WIKI     = {WIKI_DIR}/clients/{COMPANY_SLUG}
```

## Process

### Phase 1: Pre-flight Validation

1. **Verify document file exists**: Check `{document-path}` is accessible

   If not found, abort with: "Document not found: {document-path}"

2. **Validate document type**: Must be one of: email, pdf, spec, slack, other

   If invalid, abort with: "Invalid type: {type}. Must be: email, pdf, spec, slack, other"

3. **Check wiki structure**: Verify `{CLIENT_WIKI}` exists (create if needed)

4. **File size check**: If file > 50MB, warn user: "Large file ({size}MB). Ingest may be slow."

Report pre-flight status:
```
=== Wiki Document Ingest: {company} ===
Document:  {document-path}
Type:      {type}
Size:      {size}
Wiki:      {CLIENT_WIKI}
Status:    ✓ Ready for ingest
```

### Phase 2: Invoke wiki-ingest-document Skill

Launch the skill:

```
Skill: wiki-ingest-document
Parameters:
  company: {company}
  company_slug: {COMPANY_SLUG}
  document_path: {document-path}
  document_type: {type}
  summary: {summary or ""}
  wiki_dir: {WIKI_DIR}
  client_wiki_dir: {CLIENT_WIKI}
```

The skill handles:
- Reading and parsing document based on type
- Extracting key insights, requirements, decisions
- Creating or updating feature/gap pages as needed
- Creating source reference in document's metadata
- Adding to _log.md

Wait for skill completion.

### Phase 3: Report Summary

After skill completes, print summary:

```
===============================================
  Wiki Document Ingest Complete: {company}
===============================================

Document:  {document-path} ({type})
Extracted: {summary or "auto-detected"}

Changes:
  Features:   +{N}  (created/updated)
  Gaps:       +{N}  (created/updated)
  Questions:  +{N}
  Source ref: 1

Updated:
  _log.md:    ingest recorded

Total changes: +{N} pages
```

## Error Handling

- If document-path doesn't exist, abort with clear message
- If type is invalid, print valid types and abort
- If document parsing fails, attempt fallback extraction
- If wiki-ingest-document skill fails, log error and report what was extracted
- For PDF: if PDF parsing fails, try OCR (if available)
- For email: if parsing fails, treat as plain text

## Success Criteria

- Document successfully read and analyzed
- Extracted insights created/updated in {CLIENT_WIKI}
- Source reference created linking back to original document
- _log.md updated with ingest operation
- Summary printed with change counts
