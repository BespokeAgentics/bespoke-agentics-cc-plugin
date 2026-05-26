# The seven checks

Run these in order against every parsed page from `discovery.md`. Each check emits zero or more issue records in the format shown.

## Check 1 — Broken wiki-links (CRITICAL)

For every `[[target-slug|Display]]` found in every page:

1. Parse the target slug (everything before `|`).
2. Find the target file with `wiki/**/{target-slug}.md`.
3. If absent → BROKEN_LINK.

```
BROKEN_LINK | MEDIUM |
  Source: {source-page-path}
  Link: [[{target-slug}|{display-name}]]
  Expected: wiki/**/{target-slug}.md
  Status: NOT FOUND
```

Fix strategy:
- Obvious typo (`budgett-management` → `budget-management`): fix and log.
- Ambiguous (multiple candidates): log, do not auto-fix.
- Target genuinely missing: log as requires-manual-review.

## Check 2 — Orphan detection (MEDIUM)

For every page P, count incoming `[[]]` links. If 0 → ORPHAN_PAGE.

Exceptions (allowed to be orphans):
- Meeting summary pages (linked only from index).
- Entity pages younger than 7 days.
- Pages tagged `archived` or `deprecated`.
- `wiki/_schema/` content.

```
ORPHAN_PAGE | LOW |
  Page: {path}
  Type: {type}
  Created: {date}
  Last updated: {date}
  Incoming links: 0
  Recommendation: Link from related pages, or mark as deprecated/archived
```

Don't auto-link.

## Check 3 — Contradictions (HIGH)

Build a decision matrix: for each feature/gap that appears in multiple pages, extract decision/status from each. Flag when the same entity has incompatible values across pages without an explicit reconciliation note.

Contradiction types:
- **Decision drift** — same feature `decision: ootb` in one page, `decision: custom` in another, no reconciliation.
- **Status conflict** — feature marked both `resolved` and `open`.
- **Severity mismatch** — gap `low` in one meeting, `critical` in another.
- **Effort inconsistency** — same task estimated `S` in one place, `XL` in another.

```
CONTRADICTION | HIGH |
  Entity: [[{slug}|{name}]]
  Type: {type}
  Pages involved: {N}
  Page 1: {path} — {status1} — updated {date}
  Page 2: {path} — {status2} — updated {date}
  Issue: Conflicting decision statuses not explained
  Recommendation: Update one page with rationale, or add contradiction notice
```

Never auto-fix contradictions.

## Check 4 — Stale pages (LOW)

Find the most recent meeting date across all `wiki/clients/*/meetings/`. Pages with `updated < (most-recent-meeting - 14 days)` are stale.

- Very stale (>90 days): may contain outdated info.
- Moderately stale (30–90 days): review if project is active.
- Slightly stale (14–30 days): minor flag.

```
STALE_PAGE | LOW |
  Page: {path}
  Last updated: {date}
  Most recent meeting: {date}
  Days since update: {N}
  Recommendation: Review and update if still relevant
```

Don't modify content. Only flag.

## Check 5 — Missing cross-references (MEDIUM)

Detect relationships that should exist but don't:

1. **Features without gap pages** — a feature should link to at least one gap *or* be marked `ootb` with "no gaps" noted.
2. **Gaps without feature references** — every gap should be linked from at least one feature.
3. **Questions without owners** — open questions older than 14 days must have an owner/deadline.
4. **Integrations not referenced by features** — every integration should be linked from a feature or marked `planning`/`research`.
5. **Decision orphans** — decision pages should link to affected features/gaps; features should link back.

```
MISSING_XREF | MEDIUM |
  Page: {path}
  Issue: {short description}
  Details: {what's missing}
  Recommendation: {suggested link or page to create}
  Status: requires-manual-review
```

Fix strategy:
- Obvious missing reciprocal link: auto-add a "See also:" entry.
- Missing page: suggest creation, never auto-create.
- Open question >14 days: flag, never auto-close.

## Check 6 — Frontmatter validation (MEDIUM)

Required on every page: `type`, `client` (or empty for platform-level), `created`, `updated`, `sources` (array), `tags` (array).

Type-specific extras:

| Type | Required additionally |
| ---- | --------------------- |
| feature | `status` ∈ {identified, in-design, in-dev, delivered, deprecated}; `category` ∈ {catalog, ordering, checkout, budget, account, fulfillment, reporting, integration, admin}; `decision` ∈ {ootb, config, custom, gap, tbd, third-party} (may be empty) |
| gap | `severity` ∈ {critical, high, medium, low} |
| question | `priority` ∈ {P1, P2, P3}; `status` ∈ {open, resolved, blocked} |
| meeting | `meeting-date` (YYYY-MM-DD); `pipeline-outputs` (array) |

```
INVALID_FRONTMATTER | MEDIUM |
  Page: {path}
  Issue: {missing field / invalid value}
  Fix: {what to set}
```

Fix strategy (when `fix=true`):
- Add missing required fields with placeholder values (e.g. `decision: tbd`).
- Repair date format issues.
- Never guess a value where logic isn't obvious.

## Check 7 — Decision drift (HIGH)

For each feature, look at all meetings that mention it. Extract decision status from the feature page and from each meeting. If statuses differ across meetings without a reconciliation note, flag drift.

```
DECISION_DRIFT | HIGH |
  Entity: [[{slug}|{name}]]
  Current status: {decision/effort}
  Meeting {date}: {status}
  Meeting {date}: {status}
  Issue: Status changed between meetings without documented reconciliation
  Recommendation: Add "Update" section to feature page explaining the change
```

Never auto-fix drift.
