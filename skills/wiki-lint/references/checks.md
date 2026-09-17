# The eight checks

Run these in order against every parsed page from `discovery.md`. Each check emits zero or more issue records in the format shown.

## Check 1 — Broken wiki-links (CRITICAL)

For every `[[target-slug|Display]]` found in every page:

1. Parse the target slug (everything before `|`).
2. Find the target file with `wiki/**/{target-slug}.md`.
3. If absent → BROKEN_LINK.

```
BROKEN_LINK | CRITICAL |
  Source: {source-page-path}
  Link: [[{target-slug}|{display-name}]]
  Expected: wiki/**/{target-slug}.md
  Status: NOT FOUND
```

Fix strategy:
- Obvious typo (`budgett-management` → `budget-management`): fix and log.
- Ambiguous (multiple candidates): log, do not auto-fix.
- Target genuinely missing: log as requires-manual-review.

When project-ontology is installed, take broken links from Check 8's `link-broken` records instead of
resolving them here: one resolution algorithm (the write hook's), and each broken link reported once.

## Check 2 — Orphan detection (MEDIUM)

For every page P, count incoming `[[]]` links. If 0 → ORPHAN_PAGE.

Exceptions (allowed to be orphans):
- Meeting summary pages (linked only from index).
- Entity pages younger than 7 days.
- Pages tagged `archived` or `deprecated`.
- `wiki/_schema/` content.

```
ORPHAN_PAGE | MEDIUM |
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

**Required keys come from the vault's templates, not from this file.** A typed page must carry every key
its template `wiki/_schema/templates/<type>.md` declares (an empty value is allowed unless the key has a
vocabulary and the vault expects a value). Every page needs `type`. A type with no template has no
required keys beyond `type`. (An earlier hard-coded list required `sources`, `category` and `decision`
on vaults whose templates never defined them.) Formats: keys named like `*date*`, `created`, `updated`
must be ISO `YYYY-MM-DD`; keys the template writes as lists (`sources`, `tags`, `attendees`) must be lists.
Untyped pages (README, index pages without `type`) are not frontmatter-checked.

**Count one INVALID_FRONTMATTER issue per page**, listing every missing key and bad value on that page in
its record — the health score weighs pages, not fields.

**Allowed values come from the vault, never from this file.** (A hard-coded list here once said feature
statuses were `identified|in-design|in-dev|delivered|deprecated` while the vault's templates and schema
said otherwise — lint and ingest then disagreed about every page.) Resolve the vocabulary in order:

1. **Ontology installed** (`.claude/ontology/ontology.py` + the ontology file) → value checks belong to
   Check 8. Check 6 validates presence and format only.
2. **Template comments** → a key's `# a|b|c` (or `# <binding>: a|b|c`) comment in
   `wiki/_schema/templates/<type>.md` is its vocabulary; flag values outside it.
3. **No comment** → the key is free text; do not invent a vocabulary.

```
INVALID_FRONTMATTER | MEDIUM |
  Page: {path}
  Issue: {every missing key / invalid value on this page, semicolon-separated}
  Fix: {what to set, per key}
```

Fix strategy (when `fix=true`):
- Add missing required fields with placeholder values only when the vocabulary has one (e.g. `decision: tbd`).
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

## Check 8 — Ontology (HIGH / LOW)

Runs only when the project has an ontology: `.claude/ontology/ontology.py` exists and loads the file
named in `.claude/ontology/config.json`. Otherwise report `Check 8: not installed (run /ontology:init to
control the vocabulary)` and move on. The rules are the engine's — the same ones the PreToolUse write hook
enforces — so lint never disagrees with the hook.

```bash
python3 .claude/ontology/ontology.py check --all --format lint                 # scope full
python3 .claude/ontology/ontology.py check <page> <page>... --format lint      # scope client:<slug> / recent
```

Records arrive in lint format:

```
ONTOLOGY_VIOLATION | HIGH |
  Page: wiki/clients/acme/gaps/new-gap.md:5
  Rule: value-unknown (strict)
  Issue: severity: `urgent` is not a registered gap.severity value
  Recommendation: approved: critical · high · medium · low
  Fix: python3 .claude/ontology/ontology.py propose gap.severity.urgent --label urgent --definition "<what it means>"
```

Severity: `strict` → HIGH (a strict `link-broken` → CRITICAL, replacing Check 1's record for that link),
`warn` → LOW. Group the report by rule: `value-unknown`, `value-noncanonical`, `value-deprecated`,
`value-proposed`, `type-unknown`, `link-*`, `relation-*`, `id-duplicate`. Violations that predate the
current edit never block writes (ratchet) — lint is where they are counted down.

Fix strategy (when `fix=true`): run `python3 .claude/ontology/ontology.py apply --dry-run`, list the
rewrites in the report, then `apply` — it only touches mechanical cases (aliases, spelling variants,
deprecated values with a replacement, uniquely-resolvable links). Never approve, deprecate or propose
terms from lint: list proposed terms awaiting approval under Recommendations (`/ontology:approve`).

If the ontology file does not load, report one CRITICAL `ONTOLOGY_UNLOADABLE` issue with the engine's
error — every write to a governed page is blocked until it is fixed.
