# Interview protocol

The interview has one purpose: get from the user the things the evidence cannot supply — the value
proposition, the date, what "shipped" means, and the resolution of each place where the sources
disagree. It does not ask things the evidence already answers, and it does not ask for prose where
a choice will do.

Every question goes through `AskUserQuestion`. Options are derived from the evidence; the user can
always type their own. Four questions per round at most. Three rounds of ambiguity questions at
most — the rest become labelled assumptions.

## Round 1 — Intent (always asked, always together)

**Q1 · The sentence.** Header `Value prop`.
> In one sentence: who is this for, and what does it do for them?

Options: up to three candidate sentences derived from the README's first paragraph, the manifest
description, and the newest plan's stated goal — each labelled with where it came from
(`README:3`, `plans/v1.md § Goal`). Last option: "None of these — I'll write it."
If every candidate is weak, offer only "I'll write it" plus one honest attempt labelled
`derived — probably wrong`.

**Q2 · Pencils down.** Header `Target date`.
> When does building stop? After this date, no new capability — only finishing, disabling, and
> shipping work.

Options: `--target` if given (first, marked Recommended); "Two weeks from today (<date>)";
"Four weeks from today (<date>)"; "A specific date". Compute the dates; never write "two weeks"
without the resolved date beside it.

**Q3 · What shipped means.** Header `Ship = `. Multi-select.
> Which of these must be true on ship day?

Options: "Public repository anyone can clone"; "Package published (<registry inferred from the
manifest>)"; "Hosted and reachable at a URL"; "Internal release to a named group". Follow up only
if "hosted" is chosen and no deploy config exists — ask where.

**Q4 · Audience and channels.** Header `Outreach`. Multi-select.
> Who should hear about this on ship day, and where?

Options inferred from project type:
- Developer tool / library / CLI → "Hacker News (Show HN)", "X / Twitter", "Developer communities
  (Reddit, Discord, Dev.to)", "LinkedIn".
- Product / SaaS → "Product Hunt", "LinkedIn", "X / Twitter", "Newsletter / email list".
- Internal → "Internal channel (Slack / Teams / email)".
Always include "Nobody yet — skip outreach". Selecting it sets `--no-outreach`.

**Q5 · Capacity** — asked in Round 1 only if the project is clearly multi-contributor (more than
one author in the window) or the user has not stated it. Header `Capacity`.
> How much building time is there between now and pencils down?

Options: "One person, full time"; "One person, part time (~half days)"; "Two or more people";
"Let me say". Default when unanswered: one person, full time, labelled `[assumed]`.

## Round 2 — Ambiguities (from the register)

One question per register entry. Each question quotes both sides of the evidence in the project's
own terms, names the two (or three) readings, and offers each as an option. The header is the
feature name, truncated to 12 characters.

Template:
> `plans/v1.md:41` says "<quote>". The last commit touching this was `<sha>` on <date> and
> `<file>:<line>` still throws `not implemented`. Which is it?

Options are readings, not feelings: "It's in scope and I'll finish it"; "It was dropped — the plan
is stale"; "It's half-done on purpose — ship it hidden"; "Something else".

Prioritise: entries whose resolution changes a disposition first; entries that only change the
ledger's evidence column last. Stop at three rounds. Whatever remains is written into the ledger
with the evidence-supported reading and `[assumed]`.

## Round 3 — Contested dispositions (after the rubric runs)

Show, do not ask open-ended. For each contested row:

> **<Feature>** — proposed **<Disposition>** because <one clause from the rubric>. Keep it?

Options: "Yes, <Disposition>"; the two nearest alternatives from the rubric (e.g. for a proposed
Disable: "Finish it instead (+<n> days)" and "Cut it — delete the code"); "Let me explain".
Attach the day cost to every Finish alternative so the user sees what they are buying.

Contested means: `in-progress` with distance L/XL; `done` but ❌ serves-core; any 🟡; any row
where Round 2 overrode the evidence. Rows the rubric decides unambiguously are not asked about.

## Round 4 — Cut to fit (only if the arithmetic fails)

One question, repeated until it fits:

> Finish work totals **<n> days**; there are **<m> working days** at the stated capacity. To fit,
> I propose moving these to Disable/Defer: <list with days saved>. Agree?

Options: "Agree"; "Move different items (I'll say which)"; "Extend pencils down to <date that
fits>"; "Ship with the overrun — I accept the risk". The last option is recorded in the plan under
Assumptions as a stated risk acceptance, in the user's words, not as a fitted plan.

## Unattended mode

If a round goes unanswered, or the run is scheduled: take the evidence-best reading, label it
`[assumed]`, continue. Never block. The plan's Assumptions section lists every one, and the close-out
line says how many there were.
