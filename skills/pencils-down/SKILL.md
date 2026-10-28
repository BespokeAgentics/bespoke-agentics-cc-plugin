---
name: pencils-down
description: >
  Manual only (/bespoke-agentics:pencils-down). Sets a fixed "pencils down" date for a project —
  the day building stops and shipping starts — and produces the plan that gets it there. Reads the
  latest plans, commits, open work and wiki; builds a feature ledger of what is done, half-done and
  merely planned; interviews the user about intent and the core value proposition and resolves the
  ambiguities the evidence exposes; then dispositions every feature (Finish / Trim / Disable / Cut /
  Defer), checks the finish work against the days remaining, and writes a Pencils-Down plan with
  go-live preparation for the repository and documentation and a community outreach plan with
  drafted posts (via the community-outreach agent). Writes only under ./plans/pencils-down/; never
  edits application code, never posts anywhere, never commits.
disable-model-invocation: true
---

# Pencils Down

A project that is never finished is a project nobody can use. The usual reason is not that the
work is hard — it is that there is no date after which adding things is no longer allowed. Every
week brings one more feature that would make it "ready", and readiness recedes at exactly the speed
of building.

This skill installs that date. **Pencils down** is the day building stops. After it, the only
permitted work is shipping work: finishing what is already committed to, switching off what is not,
making the repository presentable to a stranger, and telling people it exists. The plan it produces
is a contract with the future about what will *not* be done.

Three commitments shape everything below.

**The core value proposition is the only judge.** Every feature is measured against one sentence
the user supplies: who this is for and what it does for them. A feature that does not serve that
sentence does not get finished because it is nearly done, and a feature that serves it does not
get cut because it is far away — it gets trimmed until it fits the time. "Ambitious" is not a
property of a feature; it is a property of a feature relative to a date.

**Disabling is a first-class outcome, not a failure.** Half-built work that ships enabled is a bug
report waiting to happen. Half-built work that is switched off cleanly — flag, hidden route, removed
nav entry, "experimental" label — is a roadmap item. The ledger distinguishes *cut* (delete it) from
*disable* (keep it, hide it) from *defer* (finish it after launch), because they cost different
things and say different things to users.

**Arithmetic beats optimism.** The plan is checked against the calendar. If the finish work exceeds
the days between now and pencils down, the plan does not ship a hopeful schedule — it goes back to
the ledger and moves things to Disable or Cut until it fits, and says so. A plan that cannot be
done is a plan to miss the date.

---

## Arguments

```
/bespoke-agentics:pencils-down ['<project-path>'] [--target <date>] [--ship <date>]
    [--out <dir>] [--window <n>d] [--channels <a,b,...>] [--no-outreach] [--resume]
```

- `<project-path>` — the repo to point at. Default: the current working directory.
- `--target` — the pencils-down date (ISO). If omitted, the interview asks; the default offered is
  **two weeks from today**, and the skill says so rather than inventing a date.
- `--ship` — the go-live date. Default: pencils-down + 7 days (the shipping week). It is never
  earlier than the target.
- `--out` — where the plan lands. Default: `<project>/plans/pencils-down/`.
- `--window` — how far back the evidence collector reads commits and transcripts. Default `90d`.
- `--channels` — outreach channels to draft for. Default: the agent infers from the project type
  and asks once; `--no-outreach` skips Step 7 entirely.
- `--resume` — continue from `<out>/state.json` rather than starting over; the interview is not
  repeated for anything already answered.

---

## Step 1 — Gather the evidence

Run the collector before reading anything by hand. It is stdlib-only and deterministic, and it
does the mechanical part so you spend judgment on the interesting part:

```bash
python3 <skill>/scripts/collect_state.py --repo <project-path> --window 90d \
  --out "$TMPDIR/pencils-down-state.json"
```

It emits one JSON document: repository identity and manifest metadata; commits in the window with
authorship, paths and WIP/TODO markers in messages; branches and how stale each is; uncommitted
work; every plan-shaped document it can find (`plans/`, `docs/plans/`, `ROADMAP*`, `TODO*`,
`PLAN*`, `*.plan.md`, open `specs/`); wiki presence and its most recently edited pages; `TODO`,
`FIXME`, `HACK`, `XXX` and `not implemented` markers with locations; feature-flag-shaped code;
tests and the test command; CI workflows; the go-live file inventory (README, LICENSE,
CONTRIBUTING, CHANGELOG, SECURITY, CODE_OF_CONDUCT, issue/PR templates, `.env.example`,
Dockerfile, release config); and a `notes` array of everything it could not read.

**Read `notes` first.** An absent wiki, a shallow clone, no tests, no manifest — these are facts
about the project that belong in the plan, not gaps to smooth over.

Then read what the collector only pointed at. Plans and roadmap documents in full — they record
intent, and intent is what the ledger is reconciled against. The last few substantive commits.
The README as a stranger would read it. When the project has more than a handful of areas, fan out
parallel `Explore` agents, one per area, asking each: what features live here, which are complete,
which are stubbed or guarded, and the `file:line` evidence. `references/evidence.md` lists what
each source is for and the trap each sets.

---

## Step 2 — Build the feature ledger

The ledger is the central artefact; everything after this step edits it. One row per feature or
capability a user would recognise — not per module, not per commit. For each, record:

| Column | Meaning |
|---|---|
| **Feature** | Named the way the product names it |
| **Serves the core?** | ⚪ until the interview supplies the value proposition; then ✅ / 🟡 partially / ❌ |
| **State** | `done` · `in-progress` · `stubbed` (UI or API exists, behaviour does not) · `planned` (document only) · `abandoned` (no commits in the window, plan says otherwise) |
| **Evidence** | Commits, files, plan sections, `file:line` for stubs |
| **Distance to done** | S (< half a day) · M (one to two days) · L (three to five) · XL (needs breakdown — and is a cut candidate by default) |
| **Disable cost** | How hard it is to switch off cleanly: flag exists / route removal / nav entry / entangled |
| **Disposition** | Blank until Step 4 |

Mark every disagreement between sources. A plan that says "shipping in v1" with no commits is a
disagreement. A commit message that says "done" against a handler that throws `not implemented` is
a disagreement. These are the ambiguities the interview exists to settle, so list them in a
separate **Ambiguity register** with the two readings and the evidence for each — the interview
asks about these, not about things the evidence already answers.

Do not disposition anything yet. Pre-grading distance-to-done is evidence work; deciding what
serves the core is the user's, and you do not have their sentence yet.

---

## Step 3 — Interview

Use `AskUserQuestion`, in rounds, following `references/interview-protocol.md`. The protocol
exists so two runs ask the same shape of question; read it before the first round.

**Round 1 — Intent.** Four questions, asked together:

1. *Who is this for, and what does it do for them — in one sentence?* Offer the best candidates
   you can derive from the README and plans, plus "none of these". This sentence becomes the
   judge for every row in the ledger; write it at the top of the plan verbatim.
2. *When is pencils down?* Offer the `--target` if given; otherwise two weeks, four weeks, and a
   date of their own. Explain in one line what the date means: after it, no new capability.
3. *What does "shipped" mean here?* Public repository · package published (npm/PyPI/crate) ·
   hosted and reachable at a URL · internal release to a named group. Multi-select.
4. *Who should hear about it, and where?* Offers derived from the project type (developer tool →
   HN, X, dev communities; SaaS → LinkedIn, Product Hunt, newsletter), plus "nobody yet".

**Round 2 — Ambiguities.** One question per entry in the ambiguity register, each quoting the
evidence on both sides, in the user's own project terms. Batch four per round; stop when the
register is empty or after three rounds, and carry the remainder forward as labelled assumptions.

**Round 3 — Contested dispositions.** Only after the value-proposition sentence exists. Apply the
rubric in Step 4 provisionally, then ask about the rows where it gives a disposition the user
might reject: anything `in-progress` with L/XL distance, anything ❌-serves-core that is `done`,
anything 🟡. Show the proposed disposition and the reason; let them override. Do not ask about
rows the rubric decides unambiguously — a `done` ✅ feature stays, a `planned` ❌ feature is cut.

If the user is not present (a scheduled run, or a round goes unanswered), do not stall: take the
reading the evidence best supports, label it `[assumed]` inline, and keep going. The plan says at
the top which answers were assumed.

Record every answer in `<out>/state.json` as you go, so `--resume` can skip what is settled.

---

## Step 4 — Disposition every feature

Apply `references/disposition-rubric.md`. The five outcomes, and the question that selects each:

| Disposition | When | What the plan commits to |
|---|---|---|
| **Finish** | Serves the core ✅, distance S/M, or L with time to spare | Acceptance criteria and a day budget |
| **Trim** | Serves the core ✅ but L/XL — the whole is too big, a slice is not | The slice that ships and the slice that moves to Defer, each named |
| **Disable** | Does not serve the core, or serves it 🟡, and is `in-progress` or `stubbed` | The mechanism (flag / route / nav / label), the proof it is hidden, and a roadmap line |
| **Cut** | Does not serve the core and is `planned` or `abandoned`, or disabling costs more than deleting | What is deleted and the plan/doc lines updated to stop promising it |
| **Defer** | Serves the core but cannot fit; or Trim's remainder | A roadmap entry with the acceptance criteria already written |

Every row gets exactly one. Every Disable row names a *mechanism that exists or is S-sized to add*
— "we'll hide it somehow" is not a disposition. Every Cut names the documents that currently
promise the feature, so the cut is complete when the promise is gone too.

Then do the arithmetic. Sum the Finish and Trim day budgets. Compare to working days between today
and pencils down, at the capacity the user stated (ask once in Round 1 if unclear; default one
person, full time, and label it). If the sum exceeds capacity by more than 20%, **do not write the
plan yet**: return to the ledger, move the lowest-serving L items to Disable or Defer, and show the
user the before/after in one `AskUserQuestion`. Repeat until it fits. The plan records every move
made here under "Cut to fit the date", because those are the decisions a future reader will
question.

---

## Step 5 — Write the Pencils-Down plan

Write `<out>/pencils-down-plan.md` from `assets/templates/pencils-down-plan.md` and the section
contract in `references/plan-structure.md`. Also write the ledger as its own file,
`<out>/feature-ledger.md`, because it is the thing people argue about and it should be diffable on
its own.

The shape:

1. **The sentence** — the value proposition, verbatim.
2. **The dates** — pencils down, ship, days remaining, capacity assumed.
3. **The line** — one paragraph stating what is and is not permitted after pencils down.
4. **Finish** — workstreams in build order with acceptance criteria and day budgets. Dependencies
   first; anything a Disable depends on (a flag system) before the Disables.
5. **Disable** — per feature: mechanism, proof, roadmap line.
6. **Cut** — per feature: what goes, which documents change.
7. **Deferred (the roadmap)** — this section is reused verbatim in the README's roadmap.
8. **Cut to fit the date** — the moves from Step 4's arithmetic.
9. **Go-live preparation** — Step 6.
10. **Outreach** — a summary; the detail lives in `outreach/`.
11. **Assumptions** — every `[assumed]` label, collected.
12. **Appendix** — the ambiguity register with resolutions, collector notes.

Order Finish workstreams so a slip loses the least: the items the value proposition cannot
survive without go first, and the day budgets are cumulative so the reader can see on which day
the plan runs out of road.

---

## Step 6 — Go-live preparation

Work through `references/go-live-checklist.md` against the collector's inventory and produce
`<out>/go-live-checklist.md`: one row per item, status 🟢 present / 🟡 present but stale or
inadequate / 🔴 missing / ⚪ not applicable, and the task that fixes it, sized S/M. Four groups:

- **Repository hygiene** — README a stranger can follow to a working install in ten minutes;
  LICENSE; CONTRIBUTING; CHANGELOG seeded from the ledger; SECURITY contact; issue and PR
  templates; `.env.example` complete against the env vars the code actually reads; no secrets in
  history (name the scan command, do not assume); default branch protected; stale branches listed
  for deletion.
- **Documentation** — quickstart; configuration reference; architecture note (one page, one
  diagram at most); **Known limitations** written directly from the Disable rows; **Roadmap**
  written directly from the Defer rows. The plan's dispositions *are* the documentation's honesty
  — do not write docs that promise what the ledger disabled.
- **Release mechanics** — version chosen and consistent across manifests; tag and release-notes
  procedure; CI green on the default branch; package publish dry-run (`npm publish --dry-run`,
  `uv build`, etc. — whichever applies); install-from-scratch verified in a clean directory.
- **Demo assets** — a screenshot or short recording of the core path. If none exists, the task
  points at `/bespoke-agentics:screencast-capture` and `/bespoke-agentics:highlight-reel` rather
  than describing a video that does not exist.

Verify rather than infer: open the README and try to follow it; run the test command; run the
publish dry-run if the toolchain is present. A 🟢 you did not check is a 🟡.

---

## Step 7 — Community outreach

Unless `--no-outreach`, assemble a brief and hand it to the **community-outreach** agent
(`agents/community-outreach.md`), launched with `Agent(subagent_type: "general-purpose")` and the
agent file's contents as its instructions. The brief — write it to `<out>/outreach/brief.md`
first, from `assets/templates/outreach-brief.md` — carries:

- The value-proposition sentence, verbatim, and the audience from Round 1.
- The **claims register**: every statement about the product the agent may make, each traced to
  the ledger (a `done` ✅ row) or the go-live checklist. Nothing else is sayable. No metrics the
  repo does not measure, no users it does not have, no quotes from people who did not say them.
- The Disable and Defer rows, so the posts can say "not yet" accurately.
- Ship date, channels, and any voice references found (prior posts, a brand or DESIGN document,
  `topics/writing`-style notes if the user points at them).
- Constraints: platform character limits, communities whose rules forbid self-promotion
  (the agent checks and says so), and anything the user asked not to mention.

The agent returns `<out>/outreach/plan.md` (channel sequence keyed to the ship date — teaser,
launch day, week-one follow-ups — with the rationale per channel) and one file per post under
`<out>/outreach/posts/`. **Read them before presenting them.** Check every factual claim against
the claims register; strike anything unregistered rather than softening it. The agent drafts;
nothing is posted by this skill or by the agent, ever.

---

## Step 8 — Close out

- Point the user at `<out>/pencils-down-plan.md` and list the other files once.
- Say in one line what the arithmetic concluded: fits / fit after N moves / does not fit at any
  disposition, in which case the date is wrong and the plan says so.
- Offer, do not perform: execution via `/bespoke-agentics:workstream-orchestrate` with this
  plan as input;
  `/bespoke-agentics:dead-code-sweep` after the Cuts land; `/bespoke-agentics:delivery-recap` on
  ship day; wiki ingestion per the project's Wiki-First Mandate when a vault exists.
- Leave `<out>/state.json` in place for `--resume`.

This skill writes under `<out>/` and nowhere else. It does not edit application code, does not
flip a flag, does not delete a branch, does not post, does not commit. The dispositions are
decisions recorded for someone to execute — possibly an orchestrator, possibly the user — and
recording them is the whole job.

---

## Honesty rules

- **The value proposition is the user's sentence, not yours.** If they did not supply one and you
  derived it, it is labelled `[assumed]` at the top of the plan, and every disposition that depends
  on it inherits the label.
- **A plan document is intent, not state.** Something listed in `ROADMAP.md` with no commits is
  `planned`, however confidently the roadmap phrased it.
- **A stub is not a feature.** A route, a button, or a handler that exists without the behaviour
  behind it is `stubbed`, and reporting it as `in-progress` because the file exists is how a
  Disable becomes a shipped bug.
- **Never let the schedule absorb the overflow.** If the work does not fit, the ledger changes;
  the day budgets do not shrink to make the sum come out.
- **A Disable without a mechanism is a wish.** Name the flag, the route, the nav entry, or the
  label — and whether it exists today.
- **Outreach says only what the ledger proves.** A post may not mention a capability that is not
  a `done` ✅ row, and may not cite a number the repository does not produce.
- **Say what you did not verify.** A go-live item you did not test is 🟡, and the plan's
  assumptions section is as much the payload as the workstreams.
