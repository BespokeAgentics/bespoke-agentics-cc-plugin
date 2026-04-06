---
name: "wiki:ingest-meeting"
description: "Ingest a completed migration pipeline meeting output into the Karpathy-style LLM Wiki. Validates meeting analysis outputs and imports structured data."
argument-hint: '<company>' '<meeting-dir>' '<meeting-label>'
allowed-tools: Agent, Bash, Read, Write, Edit, Glob, Grep
---

# Wiki Meeting Ingest

You are the Wiki Meeting Ingest Orchestrator. You take the output of a completed migration pipeline meeting and import it into the Karpathy-style LLM Wiki.

## Arguments

Parse from `$ARGUMENTS`:

```
'<company>' '<meeting-dir>' '<meeting-label>'
```

- `company` (required): Client/company name (e.g., `'Boston Beer Company'`)
- `meeting-dir` (required): Path to directory containing migration pipeline outputs (frames, transcripts, analyses)
- `meeting-label` (required): Short meeting identifier (e.g., `'batch-1-analysis'`)

If `$ARGUMENTS` is empty or missing required arguments, print this usage guide and stop:

```
Usage: /wiki:ingest-meeting '<company>' '<meeting-dir>' '<meeting-label>'

Arguments:
  company           Client/company name (quoted if spaces)
  meeting-dir       Path to directory with pipeline outputs
  meeting-label     Short meeting identifier (e.g., 'batch-1-analysis')

Example:
  /wiki:ingest-meeting 'Boston Beer Company' 'BostonBeerCompany/docs' 'batch-1-analysis'
```

## Derived Variables

```
COMPANY_SLUG    = lowercase kebab-case of company-name
CLIENT_DIR      = top-level client directory containing meeting-dir
WIKI_DIR        = ./.claude/wiki
CLIENT_WIKI     = {WIKI_DIR}/clients/{COMPANY_SLUG}
```

## Process

### Phase 1: Pre-flight Validation

1. **Verify meeting-dir exists** and contains expected outputs:
   - `gap-analysis-*.md` (required)
   - `feature-inventory-*.md` (required)
   - `*-transcript.txt` or audio-transcript.txt (required)
   - `screen-catalog.md` (required)
   - `component-library.md` (recommended)
   - `integration-assessment-*.md` (recommended)

   If critical files are missing, abort with: "Meeting outputs incomplete. Missing: {files}"

2. **Check wiki structure** — Verify `{WIKI_DIR}` exists with standard subdirectories:
   - `{WIKI_DIR}/clients/{COMPANY_SLUG}/` (may need creation)
   - `{WIKI_DIR}/questions/`
   - `{WIKI_DIR}/entities/`
   - `{WIKI_DIR}/_log.md`

3. **Create client wiki directory** if it doesn't exist: `mkdir -p {CLIENT_WIKI}`

Report pre-flight status:
```
=== Wiki Meeting Ingest: {company} ===
Meeting:          {meeting-label}
Meeting outputs:  {meeting-dir}
Wiki target:      {CLIENT_WIKI}
Status:           ✓ All files present
```

### Phase 2: Invoke wiki-ingest-meeting Skill

Launch the skill:

```
Skill: wiki-ingest-meeting
Parameters:
  company: {company}
  company_slug: {COMPANY_SLUG}
  meeting_dir: {meeting-dir}
  meeting_label: {meeting-label}
  wiki_dir: {WIKI_DIR}
  client_wiki_dir: {CLIENT_WIKI}
```

The skill handles:
- Extracting features from gap analysis → wiki/clients/{COMPANY_SLUG}/features/
- Extracting gaps from analysis → wiki/clients/{COMPANY_SLUG}/gaps/
- Creating questions from open items → wiki/questions/
- Creating entity definitions → wiki/entities/
- Creating meeting record → wiki/clients/{COMPANY_SLUG}/meetings/
- Updating _log.md with ingest record

Wait for skill completion.

### Phase 3: Report Summary

After skill completes, print summary:

```
===============================================
  Wiki Ingest Complete: {company}
===============================================

Imported from: {meeting-label}
Target wiki:  {CLIENT_WIKI}

New pages created:
  Features:     {N} ({N} custom, {N} config)
  Gaps:         {N} ({N} critical, {N} high)
  Questions:    {N} open items
  Entities:     {N}
  Meeting:      1 record

Updated:
  _log.md:      {COMPANY_SLUG} ingest recorded

Total pages: +{N}
```

## Error Handling

- If meeting-dir doesn't exist, abort with clear path message
- If critical outputs are missing, list them and abort
- If wiki-ingest-meeting skill fails, log the error and report partial results
- If _log.md update fails, continue (not critical)

## Success Criteria

- All feature/gap pages created in {CLIENT_WIKI}
- Meeting record created in wiki/clients/{COMPANY_SLUG}/meetings/
- New questions added to wiki/questions/
- _log.md updated with ingest operation
- Summary printed with page counts and changes
