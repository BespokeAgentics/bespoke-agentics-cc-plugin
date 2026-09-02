# Report structure — the content contract

This is the section-by-section contract for a delivery recap. It exists so that two runs of the
skill over the same window produce the same document rather than two different essays. The
*presentation* of the Artifact is governed by the `artifact-design` skill; what follows is the
*content* both the markdown and the Artifact must carry.

## Contents

- [Status legend](#status-legend)
- [Confidence labels](#confidence-labels)
- [Section 1 — Headline](#section-1--headline)
- [Section 2 — TL;DR](#section-2--tldr)
- [Section 3 — What shipped](#section-3--what-shipped)
- [Section 4 — Validate it yourself](#section-4--validate-it-yourself)
- [Section 5 — UI surfaces impacted](#section-5--ui-surfaces-impacted)
- [Section 6 — Backend & data changes](#section-6--backend--data-changes)
- [Section 7 — Not yet committed](#section-7--not-yet-committed)
- [Section 8 — Changed, but effect unconfirmed](#section-8--changed-but-effect-unconfirmed)
- [Section 9 — Risks & follow-ups](#section-9--risks--follow-ups)
- [Section 10 — Appendix](#section-10--appendix)
- [Worked example](#worked-example)
- [Anti-patterns](#anti-patterns)

---

## Status legend

Include the legend in the report — a reader should never have to guess what an icon means — but
**include only the rows you actually used.** A five-row legend on a report that uses two statuses is
overhead every reader pays and nobody needs.

| Icon | Status | Means |
|---|---|---|
| ✅ | Shipped | Committed, on the branch, and visible/usable as described |
| 🟡 | In progress | Partially landed — the described outcome is not fully reachable yet |
| 🚩 | Behind a flag | Committed but gated; name the flag and its current state |
| 📦 | Not yet committed | Exists only in the working tree on one machine |
| ⚪ | Unconfirmed | Changed, but the user-visible effect could not be established |

These are deliberately distinct from the project's decision-status colours (🟢 OOTB / 🔵 Config /
🟡 Custom Dev / 🔴 Gap / ⚪ TBD / 🟣 3rd Party), which grade *feasibility of a future feature*.
Delivery status grades *what exists now*. Do not mix the two vocabularies in one document.

## Confidence labels

Attach one to every deliverable and every backend/data row:

- **Verified** — read the diff and traced the effect (the route renders it, the migration defines
  the column, the endpoint exists).
- **Inferred** — the code strongly implies it, but the effect was not traced end to end. Say what
  the inference rests on.
- **Unconfirmed** — the change is real; its user-visible effect is not established. Belongs in
  Section 8.

Never use a hedge word ("appears to", "should now") in place of a label. The label is precise; the
hedge just makes a claim quietly unfalsifiable.

---

## Section 1 — Headline

One sentence, pasteable into Slack, naming the window and the shape of the work.

> **Sep 1, 2026 (last 24h)** — Overdue-invoice handling shipped end to end: new status chip in the
> admin list, a row drawer replacing full-page navigation, and a new `invoices.overdue_at` column.
> One item is behind a flag; one migration still needs to run on staging.

## Section 2 — TL;DR

3–6 bullets. Outcomes only. No file names, no library names, no commit hashes.

## Section 3 — What shipped

One block per deliverable, ordered by how much the reader will care (user-visible first,
infrastructure last).

```markdown
### ✅ Overdue invoices show a red status chip in the admin list

**What changed for the user** — The Status column previously showed plain grey text for every
invoice. Overdue ones now render as a red chip, so an overdue invoice is visible while scanning
rather than only when reading each row.

**Where to see it** — `/admin/invoices?status=overdue` (admin sign-in required)

**Evidence** — `4c0848a`, `d696585` · `src/components/InvoiceTable.tsx`, `src/lib/invoice-status.ts`

**Confidence** — Verified: `InvoiceTable` is rendered by `app/admin/invoices/page.tsx:24`, and the
chip branch is reached whenever `overdue_at` is non-null.
```

Rules for this section:

- The title is the outcome. If you cannot write the title as an outcome, the item is not a
  deliverable — move it to Section 8.
- "What changed for the user" must contrast with the previous behaviour. A reader validating the
  change needs to know what it replaced, or they cannot tell whether they are looking at the new
  thing.
- Evidence is commits **and** the two or three files that carry the change, not all twenty.
- One deliverable may span several commits. Several commits may produce no deliverable.

## Section 4 — Validate it yourself

The payload. State the base URL and any sign-in requirement once, then numbered steps that follow
one continuous path through the app.

Each step: where to go → what to do → **what they should see** (with the before-state named).

Follow with a short "Cannot be checked in the browser" list for cron jobs, migrations, and internal
APIs — each with how a technical reader could confirm it instead (a query, a log line, a CLI call).

If nothing in the window is browser-visible, say exactly that. It is a useful sentence, and far
better than a walkthrough of things that will look identical.

## Section 5 — UI surfaces impacted

| Screen / route | What changed | Who sees it | Confidence |
|---|---|---|---|
| `/admin/invoices` | Status column renders a chip; row click opens a drawer | Admins | Verified |
| `/billing` | Shared `StatusChip` restyled — colour only | All signed-in users | Inferred |

When a shared component changed, list every route you traced and state how many you traced, so an
unlisted route reads as "not checked" rather than "not affected".

## Section 6 — Backend & data changes

| Change | Kind | Effect | Rollout note | Evidence |
|---|---|---|---|---|
| `invoices.overdue_at` added | DB column | Stores when an invoice became overdue; drives the chip | Migration `0042`; **not yet run on staging** | `d696585` · `migrations/0042_*.sql` |
| `InvoiceStatusJob` | Scheduled job | Backfills `overdue_at` hourly | Effect appears within 1h of deploy | `12a73f3` · `src/jobs/invoice-status.ts` |
| `GET /api/invoices` | Endpoint | Response gains `overdueAt`; existing fields unchanged | Backward compatible | `12a73f3` |

Call out explicitly, in their own sentence rather than a table cell: destructive schema changes
(dropped/renamed columns), new **required** environment variables, and anything not backward
compatible. These are the rows that cause an incident when skimmed past.

## Section 7 — Not yet committed

Only when the working tree is dirty. Open with the fact that this work exists on one machine and is
not on the branch. Then list the files grouped by area and say what they appear to do.

## Section 8 — Changed, but effect unconfirmed

The honest section, and the one that makes the rest of the report trustworthy.

```markdown
- `src/lib/rate-limit.ts` (+84/−12, `438e7c8`) — the rate-limit window changed from fixed to
  sliding. No commit message, session prompt, or wiki page explains why, and no UI surface consumes
  it directly. A technical reviewer should confirm the intended limits.
```

State what changed, that the effect is unestablished, and who could establish it. Do not guess at
motivation.

## Section 9 — Risks & follow-ups

Only evidenced items: a migration not yet run, a flag left off, a `TODO`/`FIXME` introduced in this
window, a skipped or deleted test, a new required env var. Cite each. If there are none, write "None
identified in this window" rather than omitting the section — its absence otherwise reads as an
oversight.

## Section 10 — Appendix

For the tech lead who wants to spot-check:

- **Commits** — table of short SHA, author, time, subject, files changed. Link to the remote when
  `repo.remote` is present.
- **Sessions** — id, time range, and what the engineer asked for in their own words (the prompts).
  This is what distinguishes the recap from a git log: it shows intent, including intent that
  produced no commit.
- **Wiki updates** — pages created or modified, with their commits.
- **Excluded as noise** — one line: lockfiles, formatting, generated files, merge commits.

---

## Worked example

A thin window, done right — proportion matters more than completeness:

```markdown
# Delivery Recap — Aug 29, 2026 (last 24h)

**One bug fix shipped**: CSV exports no longer time out on accounts with more than 5,000 rows.
No UI changes; no schema changes.

## TL;DR
- Exporting a large customer list used to fail after 30 seconds with a generic error. It now
  streams and completes.
- Affects every account over ~5,000 customers (14 accounts today).

## Validate it yourself
Base: https://staging.acme.app (sign in as an admin)

1. Go to /customers and click **Export CSV** on an account with more than 5,000 customers.
   → The file downloads within a few seconds. Previously this spun for 30 seconds and then showed
   "Something went wrong".

## What shipped

### ✅ Large CSV exports complete instead of timing out
**What changed for the user** — The export built the whole file in memory before sending it, which
exceeded the request timeout past roughly 5,000 rows. It now streams rows as they are read.
**Where to see it** — `/customers` → Export CSV
**Evidence** — `a1b2c3d` · `src/api/export/customers.ts`
**Confidence** — Verified: the handler is the route for `/api/export/customers`, called from
`CustomerToolbar.tsx:61`.

## UI surfaces impacted
No visual changes. The Export CSV button behaves the same; only its success rate changed.

## Backend & data changes
| Change | Kind | Effect | Rollout note | Evidence |
|---|---|---|---|---|
| `GET /api/export/customers` | Endpoint | Streams the response instead of buffering | No config change; effective on deploy | `a1b2c3d` |

No database changes.

## Risks & follow-ups
- No test covers the >5,000-row path; the fix was verified manually (`a1b2c3d` adds no test file).

## Appendix
**Commits** — `a1b2c3d` · qdhenry · 14:22 · fix(export): stream customer CSV · 1 file (+38/−15)
**Sessions** — `27a31f06` 14:05–14:40 — "the CSV export times out for big accounts, fix it"
**Excluded as noise** — none.
```

---

## Anti-patterns

Each of these is a real way the report fails a reader:

- **The git log with headings.** Sections named after commits. Fix: group by outcome.
- **The confident fiction.** "This improves conversion on the checkout flow" when no evidence
  mentions conversion. Fix: describe the change, not the imagined benefit.
- **The unlocatable UI claim.** "Updated the dashboard component" with no route. Fix: trace to a
  route or say you could not.
- **The buried blocker.** A required new env var mentioned in an appendix table cell. Fix: its own
  sentence in Section 6 or Section 9.
- **The padded thin week.** Three paragraphs about a lockfile bump. Fix: a short report is a good
  report.
- **The six-times story.** One change appearing as the headline, a TL;DR bullet, a shipped item, a
  validation step, a table row, and a risk. Each repetition costs the reader attention they would
  otherwise spend on the line that actually mattered. Fix: each section adds something new, or the
  change appears in fewer sections.
- **The legend nobody needed.** Five status rows explained; two used. Fix: trim the legend to what
  the report contains.
- **The undifferentiated dump.** Twenty deliverables of equal weight. Fix: order by reader
  interest; collapse mechanical changes into one appendix line.
