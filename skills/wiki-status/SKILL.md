---
name: wiki-status
description: "Display a wiki health + activity dashboard: page counts by type, last 5 operations, latest lint score. Use for 'wiki status', 'wiki dashboard', 'wiki health overview'."
---

You are the Wiki Status Dashboard generator. You display the current wiki state without invoking other skills.

## Input

Optional `--client <slug>`: scope the dashboard to a single client wiki. If absent, show the workspace-wide view.

## Derived variables

```
WIKI_DIR     = ./.claude/wiki   (or the project's documented wiki root)
CLIENT_SCOPE = value from --client, or "" (all wikis)
```

If `{WIKI_DIR}` does not exist, abort with `Wiki directory not found: {WIKI_DIR}`.
If `--client <slug>` is given but `{WIKI_DIR}/clients/<slug>/` is missing, list available client slugs and abort.

## Pipeline

### Phase 1 — Count pages by type

For each scope:

- **Per-client (under `{WIKI_DIR}/clients/<slug>/`)**: count `.md` files in `features/`, `gaps/`, `meetings/`, `questions/`, `entities/`, `integrations/`.
- **Platform** (only when scope = all): count `.md` files in `{WIKI_DIR}/platforms/`.
- **Verndale / cumulative processes** (only when scope = all): count `.md` files in `{WIKI_DIR}/verndale/` or `{WIKI_DIR}/cumulative/`.

For each client also derive:
- custom vs config feature ratio (from frontmatter)
- critical / high gap counts
- completed-meetings / total-meetings
- open / closed question counts
- count of P1 (blocking) questions

### Phase 2 — Recent operations

Read `{WIKI_DIR}/_log.md` and extract the last 5 rows. Schema is one of:

```
{timestamp} — {operation} — {summary}
```

(or the project's documented schema in `{WIKI_DIR}/_schema/SCHEMA.md`). Tolerate either — fall back to "No operation history" if the log is missing.

### Phase 3 — Latest lint health

Find the most recent `{WIKI_DIR}/_lint-report-*.md` and extract its `## Health Score Summary` section (overall %, broken links, orphans, contradictions). Fall back to "No lint report yet" if none exists.

### Phase 4 — Render dashboard

Print the assembled dashboard. Workspace-wide template:

```
=== Wiki Status Dashboard ===
Last updated: {date} {time}
Scope:        all wikis

Total pages:  {N}
  Features:     {N}
  Gaps:         {N}
  Meetings:     {N}
  Questions:    {N}
  Entities:     {N}
  Integrations: {N}

CLIENT WIKIS
============
{For each client:}
{Client Name}:
  Features: {N} ({N}% custom, {N}% config)
  Gaps:     {N} ({N} critical, {N} high)
  Meetings: {N} processed / {N} total
  Questions:{N} open ({N} P1)

Platform Knowledge: {N} pages
Verndale Processes: {N} pages

Recent Operations (last 5)
  {timestamp} — {operation} — {summary}
  ...

Wiki Health Score
Overall:    {X}% ({Excellent|Good|Fair|Poor})
Last lint:  {date} {time}
Issues:     {N} broken / {N} orphans / {N} contradictions
```

Single-client template:

```
=== {Client Name} Wiki Status ===
Features: {N} ({N}% custom, {N}% config)
Gaps:     {N} ({N} critical, {N} high)
Meetings: {N} processed / {N} total
Questions:{N} open ({N} P1)
Entities: {N}
Integrations: {N}

Recent operations for this client:
  {timestamp} — {operation} — {summary}

Next steps:
  - {recommended action if open critical gaps}
  - {recommended action based on P1 questions}
```

## Error handling

- Missing wiki_dir → abort with clear message.
- Invalid `--client` slug → list available clients and abort.
- Missing `_log.md` → "No operation history", continue.
- Missing `_lint-report` → "No lint report yet", continue.
- Counting failures on a subdir → "Unable to count {subdir}", continue and show what succeeded.

## Success criteria

- Dashboard rendered with accurate counts for the requested scope.
- Last 5 operations listed (or graceful fallback).
- Health score reflected from the latest lint report (or graceful fallback).
- Output is a clean, monospaced report suitable for the terminal.
