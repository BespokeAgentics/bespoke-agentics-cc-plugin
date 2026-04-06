---
name: "wiki:status"
description: "Display a dashboard of wiki health and recent activity. Shows page counts by type, recent operations, and overall health metrics."
argument-hint: '[--client <slug>]'
allowed-tools: Bash, Read, Write, Edit, Glob, Grep
---

# Wiki Status

You are the Wiki Status Dashboard generator. You display current wiki state without invoking skills.

## Arguments

Parse from `$ARGUMENTS`:

```
[--client <slug>]
```

- `--client` (optional): Show status for specific client only (e.g., `--client boston-beer-company`)

If `$ARGUMENTS` contains invalid client slug, print this usage guide and stop:

```
Usage: /wiki:status [--client <slug>]

Arguments:
  --client <slug>   Show status for specific client (optional)

Examples:
  /wiki:status
  /wiki:status --client boston-beer-company
```

## Derived Variables

```
WIKI_DIR            = ./.claude/wiki
CLIENT_SCOPE        = value from --client, or "" (all clients)
```

## Process

### Phase 1: Verify wiki exists

Check `{WIKI_DIR}` is accessible. If not found, abort with: "Wiki directory not found: {WIKI_DIR}"

### Phase 2: Count pages by type

For the scope (all wikis or specific client), count:

**Client wikis** (if scope is "all"):
- For each subdirectory in `{WIKI_DIR}/clients/`:
  - Count `.md` files in `features/`
  - Count `.md` files in `gaps/`
  - Count `.md` files in `meetings/`
  - Count `.md` files in `questions/`
  - Count `.md` files in `entities/`
  - Count `.md` files in `integrations/`

**Platform wikis** (only if scope is "all"):
- Count `.md` files in `{WIKI_DIR}/platforms/`

**Verndale wikis** (only if scope is "all"):
- Count `.md` files in `{WIKI_DIR}/verndale/`

For each client, also:
- Parse metadata to count custom vs config features
- Parse gaps to count critical vs high priority
- Count completed meetings vs total meetings
- Count open vs closed questions
- Count P1 questions (blocking)

### Phase 3: Read recent operations log

Read `{WIKI_DIR}/_log.md` (the operation log) and extract the last 5 entries.

Expected format of each entry:
```
{timestamp} — {operation} — {summary}
```

Example:
```
2024-01-15 14:32 — ingest-meeting — boston-beer-company: batch-1-analysis (12 features, 3 gaps)
```

### Phase 4: Read latest lint report

Find the most recent `{WIKI_DIR}/_lint-report-*.md` file.

Extract the "Health Score Summary" section which should contain:
- Overall health percentage
- Broken links count
- Orphaned pages count
- Contradictions count

### Phase 5: Assemble and display dashboard

Print the complete dashboard:

```
=== Wiki Status Dashboard ===
Last updated: {date} {time}
Scope:        {all wikis | client: SLUG}

Total pages:  {N}
  - Features:     {N}
  - Gaps:         {N}
  - Meetings:     {N}
  - Questions:    {N}
  - Entities:     {N}
  - Integrations: {N}
  - Other:        {N}

{If scope is "all":}

CLIENT WIKIS
============

{For each client:}

{Client Name}:
  Features:     {N} ({N}% custom, {N}% config)
  Gaps:         {N} ({N} critical, {N} high)
  Meetings:     {N} processed / {N} total
  Questions:    {N} open ({N} P1)
  Entities:     {N}
  Integrations: {N}

Platform Knowledge: {N} pages
Verndale Processes: {N} pages

Recent Operations (last 5)
==========================
  {timestamp} — {operation} — {summary}
  {timestamp} — {operation} — {summary}
  {timestamp} — {operation} — {summary}
  {timestamp} — {operation} — {summary}
  {timestamp} — {operation} — {summary}

Wiki Health Score
=================
Overall:      {X}% ({status: Excellent/Good/Fair/Poor})
Last lint:    {date} {time}

Issues:
  Broken links:     {N}
  Orphaned pages:   {N}
  Contradictions:   {N}

{If scope is specific client:}

{Client Name} Status
====================
Features:     {N} ({N}% custom, {N}% config)
Gaps:         {N} ({N} critical, {N} high)
Meetings:     {N} processed / {N} total
Questions:    {N} open ({N} P1)
Entities:     {N}
Integrations: {N}

Recent operations for this client:
  {timestamp} — {operation} — {summary}
  {timestamp} — {operation} — {summary}

Next steps:
  - {recommended action if gaps exist}
  - {recommended action based on open questions}
```

## Error Handling

- If wiki_dir doesn't exist, abort with clear message
- If --client scope is invalid (client wiki doesn't exist), print available clients and abort
- If _log.md doesn't exist, report "No operation history" and continue
- If _lint-report doesn't exist, report "No lint report yet" and continue
- If counts fail, report "Unable to count pages" but show what succeeded

## Success Criteria

- Dashboard displayed showing all metrics
- Page counts accurate for all types
- Recent operations listed (5 most recent)
- Health score from latest lint report shown
- If --client specified: filtered to that client only
- Output formatted as clean, readable table
