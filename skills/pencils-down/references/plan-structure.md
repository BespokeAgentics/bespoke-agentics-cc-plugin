# Plan structure — the section contract

`<out>/pencils-down-plan.md` has these twelve sections, in this order, with these headings. Empty
sections collapse to one line ("No features cut."); they are never omitted, because a reader
checking "was anything cut?" should find the answer where they expect it.

The template is `assets/templates/pencils-down-plan.md`. Frontmatter is fixed — downstream
tooling (wiki ingest, orchestrators) reads it.

```yaml
---
type: plan
kind: pencils-down
project: <manifest name or directory name>
pencils_down: YYYY-MM-DD
ship: YYYY-MM-DD
capacity: "<people> × <fraction>, <n> working days"
fits: true | false | "after N moves"
assumed_count: <n>
generated: YYYY-MM-DD
sources: [plans, commits, wiki, interview]
---
```

## 1. The sentence

The value proposition, verbatim, in a blockquote. One line beneath it: where it came from
("stated in interview" or "derived from README:3 — `[assumed]`").

## 2. The dates

A four-row table: Pencils down · Ship · Working days remaining · Capacity assumed. Then one
sentence: the arithmetic's verdict (fits / fit after N moves / does not fit).

## 3. The line

One paragraph, present tense, addressed to whoever opens this file after the date:

> After **<pencils down>**, no new capability enters this project. Work permitted: the Finish
> rows below until their acceptance criteria pass; the Disable and Cut rows; every task in the
> go-live checklist; outreach. Anything else is written into § 7 and waits.

## 4. Finish

Workstreams in build order. Each:

```
### WS-n · <Feature>  — <distance> · <days> days · cumulative day <k>
Serves: ✅ <clause from the sentence it serves>
Depends on: WS-m | —
Acceptance: <one checkable statement a stranger could verify>
Evidence: <sha>, <file:line>
Notes: <only if there is something a builder must know>
```

Cumulative days let the reader see the day on which the plan runs out of road. Dependencies first;
any flag system a Disable relies on is a WS here before the Disables.

## 5. Disable

One block per row:

```
### <Feature>
Mechanism: flag `<name>` (exists, default off) | route `<path>` removed | nav entry `<component>` removed | label "experimental"
Proof: <what to look at to confirm it is hidden>
Known-limitations line: "<the sentence that goes in the README>"
Roadmap: yes → § 7 | no
Evidence: <file:line>
```

## 6. Cut

One block per row:

```
### <Feature>
Removes: <paths, or "left for dead-code-sweep">
Un-promises: <doc path:line> — "<the line that currently promises it>" → <edit>
```

## 7. Deferred (the roadmap)

A list, reused verbatim as the README's Roadmap section. Each item: feature · acceptance criterion
· why it waited. No dates unless the user gave one.

## 8. Cut to fit the date

The moves from the arithmetic, as a table: Feature · From → To · Days saved · Who decided
(user / `[assumed]`). "No moves needed." when it fit first time.

## 9. Go-live preparation

A pointer to `go-live-checklist.md` plus the counts (🟢 n · 🟡 n · 🔴 n · ⚪ n) and the three
highest-leverage tasks inline.

## 10. Outreach

A pointer to `outreach/plan.md` plus: channels, the launch-day post's first line, and the one
claim the posts lean on hardest (so a reviewer checks that one first). "Skipped (`--no-outreach`)."
when skipped.

## 11. Assumptions

Every `[assumed]` label in the plan, collected, each with what the evidence-best reading was and
what would change if it is wrong. The collector's `notes` array follows, verbatim.

## 12. Appendix

The ambiguity register with resolutions (question · readings · resolved to · by whom). Commits in
the window by count per author. Plans consulted with paths.

## `feature-ledger.md`

Written separately, frontmatter `type: ledger, kind: pencils-down`, one markdown table with the
seven ledger columns, sorted by disposition (Finish, Trim, Disable, Cut, Defer) then by feature
name. It is the diffable artefact; two runs on the same repo should produce the same rows.

## Length

The plan is read by the person who has to execute it, on the day they execute it. Finish blocks
are complete; everything else is as short as truth allows. A project with four features produces a
two-page plan. A project with forty produces a long ledger and a plan that still fits in ten pages,
because the Finish section is the only one that has to be detailed.
