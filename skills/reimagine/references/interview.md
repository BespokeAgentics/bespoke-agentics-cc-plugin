# Gallery interview — reaction, critique, hybridization, winner

Read before Phase 5. For preview craft, round mechanics (≤4 questions,
rebuild between rounds, structural before aesthetic), the four contradiction
shapes, and the ledger law, read the parent skill's `references/interview.md`
**in place** — all of it applies. This file covers only what a variant gallery
adds.

## The arc

Four kinds of round, in order. A small surface may compress reaction+critique
into one round; never skip hybridization's *offer* or the winner confirmation.

**1 — First reaction.** Hand over the URL, invite grid view and comment mode
(`✎` or `c` — comments arrive tagged with their pane), start `await-feedback`
as a background task unless the channel is live. Ask: gut ranking, immediate
kills, and one "what did each get right?" — deliberately shallow. The point is
to learn where the user's eye went before analysis papers over it.

**2..n — Per-variant critique.** Driven by the surviving variants: what works,
what breaks, and **what to steal** — the steal list is the hybrid feedstock and
the most valuable answer in the whole interview. Use shared-axis flips as round
material ("now look at all four empty" costs one control flip and routinely
reverses a ranking). Refinements edit panes in place. Contradiction hunting is
mandatory *across variants*, not just across answers: "keep A's inline filters"
and "keep C's collapsed toolbar" can each be sensible and still not coexist —
surface it, name what breaks, offer resolutions.

**3 — Hybridization.** Offer 2–3 hybrid recipes as ASCII-previewed options
("A's density + C's grouping + Current's toolbar") plus "pure winner, no
hybrid". **A chosen hybrid is rebuilt as a real pane, never hand-waved**: emit
`reimagine-v2.html` containing Current + the hybrid + its strongest parent —
killed variants drop from panes but stay in the manifest as `retired: true` so
the record survives. Then one confirmation round against v2. The user judges
the hybrid as a rendered thing; a hybrid that exists only as a sentence is a
spec bug waiting to be discovered by the implementer.

**4 — Winner.** Confirm the winner, and confirm a rejection reason for each
loser — *drafted from critique-round evidence, not asked cold* ("B lost on the
empty state and the label overflow — fair?"). Then offer the handoff: the
winner can go to `interactive-wireframe --slug <slug>` for fine-grained
settlement (thresholds, sticky behaviour, per-role states) when it needs one;
offered, never auto-run.

## Browser comments

Same triage law as the parent — change → rebuild · question → `reply` into the
page's thread · approval → decision row — with one addition: the payload's
`variant` field routes each comment to its pane automatically. Fold comments
into the next round; a browser comment and a terminal answer are the same
interview. In grid view the user can comment on a *non-active* pane — trust
the payload's `variant`, not the current `rv` state.

## Gallery checks run during rounds

Keep the comparison honest while it is happening, not after: after each
build/rebuild run `__wf.markup()` page-wide, per-pane contrast on each
variant's 2–3 key text pairings, `__wf.focusables('#rv-<id>')` per pane, and
the tier proxies from `directions.md`. A variant failing AA or nesting buttons
is not disqualified — it is *named in the round* ("C's muted rows are 3.9:1,
below AA — fixable with the darker grounded grey; should I?"). Users pick
differently when they know which options are carrying a defect.

## When to stop

Stop when a winner (or hybrid) is confirmed, every loser has a recorded reason,
and cross-variant contradictions are resolved or recorded. The remaining
unknowns go to the spec's Open questions — the fine-grained settlement of the
winner is the parent skill's job, not a reason to keep this interview running.
