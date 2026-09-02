---
name: delivery-recap
description: >
  Produce a high-level delivery recap for a non-engineer reader — a project manager, tech lead,
  or client — explaining what was actually delivered in a time window, which UI surfaces it
  changed, which backend services, endpoints, database tables and jobs it touched, and exactly
  how to open the running site and see it. Use this whenever someone asks what shipped, what was
  worked on, what changed today/yesterday/this week/this sprint, for a status update, a standup
  summary, a client update, an end-of-day or end-of-session wrap-up, "what did we get done", "write
  this up for my PM", "summarize my work", "recap this session", or "what should I tell the team".
  Also use it proactively at the end of a substantial working session when the user is wrapping up
  and would plausibly need to report the work upward. The default window is the last 24 hours
  unless the user names another. It reads three sources — git commits plus uncommitted working-tree
  changes, Claude Code session transcripts (which record what the user was *trying* to do, not just
  what landed), and wiki page updates — via a bundled collector script, then traces changed
  components to the routes that render them so the report can say "go to this screen and look at
  this". It writes markdown to ./reports/ and publishes a shareable Artifact. Findings are graded
  by confidence and anything whose user-visible effect cannot be confirmed is listed as unverified
  rather than given an invented rationale. Read-only: it never modifies application code, never
  commits, and never pushes.
---

# Delivery Recap

Someone needs to explain to a non-engineer what got built. The failure mode is not writing too
little — it is writing a `git log` with prettier headings. A commit list answers "what files
changed"; the reader is asking a different question: **"is the thing I asked for actually there,
and how do I go look at it?"**

Those are different documents. This skill produces the second one.

Three commitments shape everything below.

**The unit of reporting is a deliverable, not a commit.** A reader does not care that
`useInvoiceQuery` was refactored across four commits. They care that overdue invoices now show a
red status chip in the admin list. One deliverable frequently spans several commits, and several
commits frequently add up to no deliverable at all (dependency bumps, formatting). Group by outcome
and the report becomes readable; group by commit and you have re-created the thing they could
already see in GitHub.

**A claim a reader cannot check is worse than no claim.** Every deliverable carries both the
evidence behind it (commits, files) and the route to go look at it. That is what makes the report
verifiable by a tech lead in two minutes rather than trusted on faith — and it is why the
"Validate it yourself" section, not the summary, is the payload.

**Confidence is part of the content.** Diffs show what changed; they do not show why, and they
frequently do not show whether it is visible to anyone. Inferring a business rationale from a
migration file is how a recap becomes fiction. Say what you verified, say what you inferred, and
give the rest its own honest section. A reader who catches the report inventing one thing stops
believing all of it.

---

## Step 1 — Fix the window and gather the evidence

Default to **the last 24 hours**. Override when the user names a period ("this week", "since
Monday", "the last 3 days", "this sprint"). Do not ask which window they meant when they said
nothing — 24h is the documented default, so use it and state it in the report.

Run the collector. It handles all the mechanical extraction so you never hand-roll git plumbing or
JSONL parsing:

```bash
python3 <skill>/scripts/collect_window.py --since 24h --out "$TMPDIR/recap-window.json"
```

Write it to a temp path, not into the repo — this is intermediate evidence, and leaving a
`.recap/` directory behind in someone's working tree is a side effect they did not ask for. If the
user wants the raw evidence kept, save it beside the report and say so.

Useful flags: `--since 3d|2w|today|yesterday|week|sprint|2026-08-28`, `--until`, `--author me`
(only this engineer's commits), `--sessions current|all|none`, `--repo <path>`, `--wiki-dir`.

Then read that JSON. **Read the `notes` array first** — it records what was unavailable
(not a git repo, no transcripts, an empty window), and those gaps must survive into the report
rather than being silently smoothed over.

What each source is for, and what it is not:

| Source | What it uniquely tells you | Trap |
|---|---|---|
| `commits` | What actually landed, with authorship and timing | Commit messages describe the change, not the user-visible effect |
| `uncommitted` | Work delivered but not yet committed | Must be labelled **not yet committed** — a reader will assume anything listed is on the branch |
| `sessions[].user_prompts` | What the engineer was *trying* to do, in their own words | The goal stated may exceed what was finished — check it landed before reporting it as shipped |
| `sessions[].files_touched` | Work that produced no commit (explorations, reverted attempts) | Touching a file is not delivering a change |
| `wiki` | Decisions and context recorded alongside the code | A wiki edit is documentation of work, not the work |
| `bucket_hint` on every file | A fast first cut at UI / api / service / db / config | It is a **path guess with its rule attached** — verify against the diff before reporting it |
| `totals.committed` vs `totals.uncommitted_or_session_only` | The two are counted separately on purpose | **Never add them into one headline figure.** "78 files changed" when 41 sit dirty on one machine is a confident falsehood in your first line — report `committed` as what shipped |

If the window is empty, say so plainly and offer to widen it. Do not pad a recap with a
dependency bump to avoid an awkward "nothing shipped".

---

## Step 2 — Understand what actually changed

Read the real diffs for the substantive changes — `git show <sha> -- <path>`, or
`git diff HEAD -- <path>` for uncommitted work. The collector deliberately gives you file names and
sizes, not content, because deciding *which* changes are substantive is judgment and reading all of
them is waste. Prioritize by: files with the most added lines, files in `ui`/`api`/`db` buckets,
and anything a session prompt explicitly asked for.

When more than a handful of areas changed, **fan out with parallel `Explore` agents** — one per
area (the UI surfaces, the API/service layer, the data layer). Ask each for: what changed in
behavioural terms, which user-facing surface it reaches, and the `file:line` evidence. Reading
twelve subsystems serially in the main thread is slow and blurs them together; the parallel reads
come back sharper.

Then assemble deliverables. A deliverable is **a change a reader could care about**, stated as an
outcome. Merge commits that serve one goal; drop pure-noise changes (lockfiles, formatting,
generated files) into a single line in the appendix.

Good titles read like a product changelog:

- ✅ "Overdue invoices now show a red status chip in the admin list"
- ❌ "Refactor InvoiceTable and add status derivation"
- ✅ "Password reset emails now retry instead of failing silently"
- ❌ "Add retry wrapper to mailer service"

If you cannot state a change as an outcome, that is itself the finding — it belongs in
**Changed, but effect unconfirmed**, not in a vaguely-worded shipped item.

---

## Step 3 — Trace UI impact to a route

"What UI was impacted" is only useful if it resolves to somewhere the reader can navigate. A
changed component file is a starting point, not an answer — the reader cannot open
`InvoiceTable.tsx`.

Trace each changed UI file up to the route(s) that render it: grep for imports of the component,
follow to the page/route file, and read the framework's routing convention (Next.js `app/`
segments, React Router definitions, Vue/Nuxt pages, Rails routes, Django urls). Record the concrete
path a browser would use — `/admin/invoices`, `/settings/billing` — plus any query param or state
needed to see the change (`?status=overdue`, "only visible to admins", "only when the list is
empty").

Two cases deserve explicit handling because they are where recaps mislead:

- **A shared component changed.** The blast radius is every route that renders it. Name them, or
  say plainly that you traced N of them and there may be more.
- **The change is invisible.** Behind a feature flag, admin-only, a performance fix, a refactor
  with no behavioural delta. Say so. "Not visible in the UI" is a legitimate and useful answer, and
  far better than a vague sentence implying something to look at.

---

## Step 4 — Describe backend and data changes in terms of effect

A PM reading "modified `invoices` table" learns nothing. Describe what it means:

- **Database:** which table, which columns added/changed/dropped, nullable or not, whether a
  migration exists and whether it has been run, whether existing rows were backfilled, and whether
  the change is reversible. A dropped or renamed column is a destructive change and should be
  called out as one.
- **Services / jobs:** what the service now does that it did not before; anything that runs on a
  schedule or a queue and therefore has a delay before its effect is visible.
- **API surface:** new/changed/removed endpoints, request or response shape changes, and — because
  this is what breaks other teams — whether the change is backward compatible.
- **Config / infra:** new environment variables (a deploy blocker if unset), changed CI, changed
  build or deploy config. Flag any new required env var loudly: it is the single most common reason
  a validated-locally change does not work on staging.

Ground each in evidence. If a migration file exists, name it. If you cannot tell whether it has
been applied to the environment the reader will visit, say that rather than assuming.

---

## Step 5 — Confirm the base URL, then write the validation steps

The report exists so someone can go look. `url_candidates` in the collector output holds every URL
found in the README, `.env.example`, deploy config, and package scripts. Pick the most plausible
and confirm it with **one** `AskUserQuestion` — offering the candidates you found plus "local dev"
and "not deployed yet" as options. One question, not an interview; and skip it entirely if the user
already told you the environment.

If `AskUserQuestion` is unavailable, or the user is not present to answer, do not stall and do not
silently pick one: take the most defensible candidate, and **label the assumption inline in the
report** ("Base: `https://staging.acme-billing.test` — assumed from `README.md:5`; confirm before
sending"). A labelled assumption a reader can correct in two seconds is fine; an unlabelled one that
sends them to the wrong environment is how they conclude nothing shipped.

Then write steps a non-engineer can follow without help. Each step names where to go, what to do,
and **what they should see** — because a reader who does not know what "correct" looks like cannot
validate anything:

```
## Validate it yourself
Base: https://staging.acme.app  (sign in as an admin)

1. Go to /admin/invoices?status=overdue
   → The Status column now shows a red "Overdue" chip. Before today it was plain grey text.
2. Click any row.
   → A drawer slides in from the right. Previously this navigated to a full page.
3. Click the ⋯ menu → "Export CSV".
   → Downloads immediately. The 30-second wait is gone.
```

Order the steps so one pass through the app covers everything. Anything that cannot be validated in
a browser — a cron job, a migration, an internal API — goes in a short second list with how a
technical reader could confirm it instead (a query to run, a log line to look for).

---

## Step 6 — Write the report

Write markdown to `./reports/recap-YYYY-MM-DD.md` (add `-HHMM` if one already exists for the day;
never overwrite a previous recap). Then publish the same content as an Artifact so it can be handed
to the PM as a link.

**For the Artifact: load the `artifact-design` skill before writing the HTML** — it calibrates the
design investment and covers the theming and structure requirements. The section contract below is
the *content*; the design skill governs the *presentation*. Title the Artifact as a name, not a
summary ("Billing Recap · Sep 1", not "Delivery recap of what shipped today"), and give it a stable
favicon. When updating an earlier recap rather than writing a new one, redeploy to the same file
path so the link the PM already has keeps working.

Use `references/report-structure.md` for the full section-by-section contract, the status legend,
and a worked example. Read it before writing — it is what keeps two runs of this skill producing
the same document rather than two different essays.

The shape, in brief:

1. **Headline** — one sentence a PM could paste into Slack.
2. **TL;DR** — 3–6 outcome bullets, no jargon.
3. **What shipped** — per deliverable: what changed for the user, where to see it, evidence,
   confidence.
4. **Validate it yourself** — the numbered walkthrough from Step 5.
5. **UI surfaces impacted** — table of route → what changed → who sees it.
6. **Backend & data changes** — table of change → kind → effect → evidence.
7. **Not yet committed** — only when the working tree is dirty.
8. **Changed, but effect unconfirmed** — the honest section.
9. **Risks & follow-ups** — only what is evidenced.
10. **Appendix** — commits, sessions, wiki updates, and the noise you excluded.

Write for someone with no context on the codebase. Expand acronyms on first use, name features the
way the product names them, and keep file paths out of the body — they belong in the evidence
column and the appendix, where a tech lead will look for them and a PM can ignore them.

### Length is a feature, not an afterthought

A recap that does not get read has failed, whatever else is true of it. So calibrate hard, and
treat the ten sections as *permitted* sections rather than a checklist to fill:

| Window contained | Target | What that means in practice |
|---|---|---|
| 1–2 deliverables | Half a page | TL;DR, one or two shipped items, validation steps, appendix. Fold the empty sections into a single line each ("No database changes. Nothing uncommitted."). |
| 3–6 deliverables | 1–2 pages | The full contract, but each deliverable stays under six lines. |
| A week of substantial work | 2–3 pages | Group deliverables into themes; the appendix absorbs the detail. |

Three specific economies, because they are where these reports bloat:

- **Include only the status icons you actually used.** A legend explaining five statuses in a
  report that uses two is pure overhead paid by every reader.
- **Tell each story once.** If the same change is the headline, a TL;DR bullet, a shipped item, a
  validation step, a table row, *and* a risk, the reader is reading it six times and will start
  skimming — which is when they miss the one line that mattered. Each section should add something
  the previous ones did not.
- **Empty sections collapse to one line.** "No database changes in this window" is complete. Do not
  build a table to say nothing.

A recap that takes longer to read than the work took to do trains people to stop reading recaps.

---

## Step 7 — Close out

- Tell the user where the markdown landed and hand them the Artifact link.
- If a wiki vault exists (`wiki/`), offer to ingest the recap per the project's Wiki-First
  Mandate and log it in `wiki/_log.md`. Offer — do not do it unprompted.
- If the window contained work the user might not want in a report going upward (an experiment
  that was reverted, an outage), point it out rather than deciding for them.

This skill is read-only with respect to application code. It writes its own report, and nothing
else. It does not commit, does not push, and does not fix anything it noticed along the way — if it
found a real defect, say so and let the user decide whether to run `/bespoke-agentics:defect-intake`.

---

## Honesty rules

These are the ways a delivery recap goes wrong. They are worth stating explicitly because each one
is a *plausible-sounding* sentence that happens to be false, which is exactly the kind of error that
survives review.

- **Never infer a business rationale from a diff.** If no commit message, session prompt, ticket,
  or wiki page says *why*, then why is unknown. Describe the change and stop.
- **Never report intent as delivery.** A session prompt saying "add CSV export" plus a half-written
  handler is not a shipped CSV export. Check that it landed, or list it as in progress.
- **Never present uncommitted work as shipped.** It is on one machine. Label it.
- **Never claim a UI change is visible without tracing it to a route.** "Users will now see…" is a
  claim about rendering, and rendering is checkable.
- **Distinguish "I verified this" from "this is what the code implies".** Both are legitimate; only
  one is a fact.
- **A window with nothing in it is a valid report.** Say the window was quiet and ask whether to
  widen it.
