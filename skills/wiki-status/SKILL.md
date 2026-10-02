---
name: wiki-status
description: "Display a wiki health + activity dashboard: page counts by type, last 5 operations, latest lint score. Use for 'wiki status', 'wiki dashboard', 'wiki health overview'."
disable-model-invocation: true
---

You are the Wiki Status Dashboard generator. You display the current wiki state without invoking other skills.

## Input

Optional `--client <slug>`: scope the dashboard to a single client wiki. If absent, show the workspace-wide view.

## Derived variables

```
WIKI_DIR     = ./wiki   (or the wiki root the project's CLAUDE.md names)
CLIENT_SCOPE = value from --client, or "" (all wikis)
GROUP_DIR    = the vault's grouping folder — clients/ | projects/ | teams/ | domains/ — read from the
               Vault layout block in {WIKI_DIR}/_schema/SCHEMA.md (fallback: whichever of those exists)
ORG_DIR      = the vault's org section folder, per _schema/SCHEMA.md ("" if none)
```

If `{WIKI_DIR}` does not exist, abort with `Wiki directory not found: {WIKI_DIR}`.
If `--client <slug>` is given but `{WIKI_DIR}/{GROUP_DIR}/<slug>/` is missing, list available slugs and abort.

## Pipeline

### Phase 1 — Count pages by type

For each scope:

- **Per-client (under `{WIKI_DIR}/{GROUP_DIR}/<slug>/`)**: count `.md` files in `features/`, `gaps/`, `meetings/`, `questions/`, `entities/`, `integrations/`.
- **Platform** (only when scope = all): count `.md` files in `{WIKI_DIR}/platforms/`.
- **Org processes** (only when scope = all and `ORG_DIR` is set): count `.md` files in `{WIKI_DIR}/{ORG_DIR}/`.

For each client also derive:
- custom vs config feature ratio (from the `decision` frontmatter key)
- critical / high gap counts
- completed-meetings / total-meetings
- open / closed question counts
- count of P1 (blocking) questions

### Phase 2 — Recent operations

Read `{WIKI_DIR}/_log.md`. Entries are appended at the end as heading sections, so the last 5 entries are the last 5 lines matching:

```
## YYYY-MM-DD — <operation> — <summary>
```

Parse each into `date`, `operation`, `summary` (split on ` — `; the summary may itself contain ` — `, so split at most twice). Ignore the body lines under each heading and any line that does not match. Scoped to a client, keep only entries whose heading or body names the client slug. Fall back to "No operation history" if the log is missing or has no matching headings.

### Phase 3 — Latest lint health

Find the most recent `{WIKI_DIR}/_lint-report-*.md` and read `**Health Score**` plus the issue counts (broken links, orphans, contradictions) from its `## Executive Summary` section. Fall back to "No lint report yet" if none exists.

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
{Org Name} Processes: {N} pages   (only if ORG_DIR is set)

Recent Operations (last 5)
  {date} — {operation} — {summary}
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
  {date} — {operation} — {summary}

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
