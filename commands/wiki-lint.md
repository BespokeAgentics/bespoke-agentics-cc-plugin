---
name: "wiki:lint"
description: "Lint and validate the wiki. Checks for broken links, orphaned pages, contradictions, and data quality. Optionally auto-fix issues."
argument-hint: '[--scope full|client:<slug>|recent] [--fix]'
allowed-tools: Agent, Bash, Read, Write, Edit, Glob, Grep
---

# Wiki Lint

You are the Wiki Lint Orchestrator. You validate wiki health and optionally auto-fix issues.

## Arguments

Parse from `$ARGUMENTS`:

```
[--scope full|client:<slug>|recent] [--fix]
```

- `--scope` (optional): Lint scope. One of:
  - `full` (default): Lint entire wiki
  - `client:<slug>`: Lint only one client (e.g., `client:boston-beer-company`)
  - `recent`: Lint only pages modified in last 7 days
- `--fix` (optional): Auto-fix issues where possible (default: false)

If `$ARGUMENTS` is empty or invalid scope, print this usage guide and stop:

```
Usage: /wiki:lint [--scope full|client:<slug>|recent] [--fix]

Scope options:
  full (default)          Lint entire wiki
  client:<slug>           Lint specific client (e.g., client:boston-beer-company)
  recent                  Lint pages modified in last 7 days

Flags:
  --fix                   Auto-fix issues where possible

Examples:
  /wiki:lint
  /wiki:lint --scope client:boston-beer-company
  /wiki:lint --scope recent --fix
```

## Derived Variables

```
WIKI_DIR            = ./.claude/wiki
SCOPE_VALUE         = value from --scope (default: "full")
FIX_ENABLED         = true if --fix present, false otherwise
REPORT_FILE         = {WIKI_DIR}/_lint-report-$(date +%Y%m%d-%H%M%S).md
```

## Process

### Phase 1: Pre-flight

1. **Verify wiki directory exists**: Check `{WIKI_DIR}` is accessible

   If not found, abort with: "Wiki directory not found: {WIKI_DIR}"

2. **Compute scope**: Parse `--scope` value
   - If `full`: target all wiki pages
   - If `client:<slug>`: target only `{WIKI_DIR}/clients/{slug}/**`
   - If `recent`: find all `.md` files with mtime < 7 days
   - If invalid: abort with clear error

3. **Check previous report**: Read most recent `_lint-report-*.md` for baseline

Report pre-flight status:
```
=== Wiki Lint: {SCOPE_VALUE} ===
Wiki:      {WIKI_DIR}
Scope:     {SCOPE_VALUE}
Auto-fix:  {yes/no}
Status:    ✓ Ready
```

### Phase 2: Invoke wiki-lint Skill

Launch the skill:

```
Skill: wiki-lint
Parameters:
  wiki_dir: {WIKI_DIR}
  scope: {SCOPE_VALUE}
  auto_fix: {FIX_ENABLED}
  report_file: {REPORT_FILE}
```

The skill performs:
- **Link validation**: Check all `[text](link)` references point to real pages
- **Orphan detection**: Find pages with no incoming links
- **Contradiction check**: Find contradictory claims across pages
- **Metadata validation**: Check all required frontmatter fields
- **Duplicate detection**: Find near-duplicate pages
- **Coverage analysis**: Check if features have corresponding gap entries
- **Entity resolution**: Verify all entity references are defined
- **Date validation**: Check all timestamps are valid

Wait for skill completion.

### Phase 3: Parse Report and Print Health Score

Read `{REPORT_FILE}` and extract the health score summary section. The report should contain:

```markdown
## Health Score Summary

- **Overall Health**: {X}% ({status: Excellent/Good/Fair/Poor})
- **Total pages scanned**: {N}
- **Broken links**: {N}
- **Orphaned pages**: {N}
- **Contradictions found**: {N}
- **Missing metadata**: {N}
- **Duplicates**: {N}
- **Coverage gaps**: {N}
- **Last updated**: {date}
```

Parse and display this summary prominently:

```
===============================================
  Wiki Lint Report: {SCOPE_VALUE}
===============================================

Health Score: {X}% ({status})

Pages scanned:       {N}
Issues found:
  Broken links:      {N}
  Orphaned pages:    {N}
  Contradictions:    {N}
  Missing metadata:  {N}
  Duplicates:        {N}
  Coverage gaps:     {N}

Report saved to: {REPORT_FILE}
```

### Phase 4: Auto-fix (if --fix enabled)

If `--fix` is enabled and the skill found fixable issues, re-invoke:

```
Skill: wiki-lint
Parameters:
  wiki_dir: {WIKI_DIR}
  scope: {SCOPE_VALUE}
  auto_fix: true
  apply_fixes: true
  report_file: {REPORT_FILE}
```

Wait for fixes to complete. Update summary:

```
Auto-fix applied:
  Links corrected:   {N}
  Metadata added:    {N}
  Duplicates merged: {N}
```

## Error Handling

- If wiki_dir doesn't exist, abort with clear message
- If scope is invalid, print valid scopes and abort
- If linting fails, report partial results
- If auto-fix fails on specific pages, log them and continue
- If report file can't be written, print results to stdout

## Success Criteria

- Wiki linted according to specified scope
- Health score computed and displayed
- Report file generated at {REPORT_FILE}
- If --fix enabled: issues auto-corrected where possible
- Summary printed showing:
  - Overall health percentage
  - Total pages scanned
  - Issue counts by category
  - Report location
