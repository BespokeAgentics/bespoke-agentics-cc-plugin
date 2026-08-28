---
name: misunderstanding
description: >
  User-invoked correction of a wrong inference — the plan step you read too generously, the wiki
  claim that was stale, the doc that implied something it never said, the earlier turn you took as
  settled. Invoke only when the user explicitly asks ("run misunderstanding", "you misunderstood",
  "that's not what I meant", "you inferred that wrong", "stop and clarify before you continue",
  "/misunderstanding"); this skill does not self-trigger on the mere smell of confusion, because
  deciding that something was misunderstood is the user's call, not an inference. It reconstructs
  the inference chain behind the flagged belief — each belief paired with the verbatim source text
  that produced it, and labeled as stated, inferred, or assumed from silence — scopes to that
  belief's blast radius, then asks specific, source-quoted questions via AskUserQuestion so the
  user corrects the reading rather than re-explaining from scratch. It corrects the artifact that
  seeded the bad inference, inventories the work already built on it and lets the user disposition
  each item, records the correction where that repo keeps durable knowledge, feeds the corrected
  belief into a knowledge store when one exists, and resumes with a corrected restatement. It never
  auto-reverts work and never commits.
---

# Misunderstanding

You built on something you got wrong. Not a bug in the code — a bug in the reading: a plan step
interpreted more broadly than it was written, a wiki page that described last quarter's system, a
requirement inferred from a silence that meant nothing at all. The user has just told you so.

The reflex is to apologize, restate, and carry on. That fixes the conversation and nothing else.
By the time a misunderstanding gets noticed it has usually already produced decisions and code, and
the claim that caused it is still sitting in the source, ready to mislead the next session exactly
the same way. So the work here is four things, in order: find out precisely which belief is wrong
and where it came from, get the correct reading from the user in specifics rather than prose, fix
the source, and disposition what was built on the error.

Three ideas govern the rest:

- **A misunderstanding is a chain, not a fact.** Something was said, you read it a particular way,
  and you acted. Any of those three links can be the broken one, and they need different fixes.
  Correcting the conclusion without finding the link that failed guarantees a repeat.
- **The user already told you that you're wrong. Your job is to make it answerable.** Asking "what
  did I misunderstand?" hands the work back to them. Asking "the plan says _'users can export'_ —
  I read that as any authenticated user; did you mean admins only?" costs them three seconds.
- **A wrong belief has a blast radius.** It rarely produced one decision. Everything drawn from the
  same source, and everything that depends on the wrong conclusion, is in scope. Everything else is
  not — this is a correction, not a session-wide audit.

---

## Step 0 — Take in what is being flagged

The invocation usually carries a hint: a phrase ("you misunderstood the auth flow"), a `file:line`,
a quoted claim, or a correction stated outright. Any of those is enough to start.

If it carries nothing at all, **ask what was misunderstood.** Do not sweep the conversation for
candidates and present a list of things you might have gotten wrong — that inverts the skill,
producing a self-audit the user then has to grade. This skill dispositions a known misunderstanding.

If the hint is vague ("something about the data model is off"), resolve it to a concrete belief
before continuing. One question is cheaper than a ledger built around the wrong thing.

---

## Step 1 — Build the inference ledger

Before asking anything, reconstruct how the belief got into your head. For the flagged belief and
each one in its blast radius (Step 2), record:

| Field        | What goes in it                                                                       |
| ------------ | ------------------------------------------------------------------------------------- |
| `belief`     | Your current understanding, one sentence, stated plainly enough to be wrong            |
| `source`     | **Verbatim quote** plus locator: `file:line`, wiki page, or which conversation turn    |
| `type`       | `stated` · `inferred` · `assumed-from-silence`                                         |
| `downstream` | What it produced — files, edits, decisions, other beliefs                              |
| `confidence` | `confirmed` · `probable` · `uncertain`                                                 |

Two fields do the real work.

**The quote.** A ledger row without the source text is a guess about your own reasoning. Go find
the line. If the source was a conversation turn that compaction has since eaten, say so and label
the row reconstructed-from-memory — do not paraphrase a quote you cannot produce.

**The type.** These are different defects with different fixes:

- `stated` — the source said it and you read it wrong. The fix is yours; the source is fine.
- `inferred` — the source implied it and you extended it. The source is probably ambiguous and
  should be tightened.
- `assumed-from-silence` — the source never addressed it and you filled the gap. The source has a
  hole, and the hole is what needs filling.

Present the ledger to the user as a table before the interview. Often they will correct a row on
sight and save you a question.

---

## Step 2 — Scope to the blast radius

In scope:

1. The flagged belief.
2. **Siblings** — other beliefs drawn from the same source. If a wiki page was stale enough to
   mislead you once, every other reading of that page is suspect.
3. **Dependents** — beliefs that only hold if the wrong one does.

Out of scope: everything else you inferred this session. Resist the pull toward a full assumption
audit; it turns a two-minute correction into an interrogation and buries the actual error in noise.

State what you excluded and why, in one line. If the user thinks the net should be wider, that is
their call to make with the exclusions visible.

---

## Step 3 — Interview, in specifics

Use `AskUserQuestion`. Order by blast radius — the belief that contaminated the most work first.
Cap at **4 questions per call**, **≤3 rounds**, ≤4 options each.

Every question must:

- **Quote its source.** "The spec says _'<verbatim>'_ …" A question without the source text asks
  the user to remember what they wrote, and they will remember it as what they meant.
- **Lead with your current belief as the first option**, stated as the recommendation, so
  confirming is one click.
- **Offer the plausible alternative readings** as the other options — the readings a competent
  person could have taken from the same words. Never open-ended, never "other (please explain)" as
  the only escape.
- Use `multiSelect` when the beliefs are not mutually exclusive.

For an `assumed-from-silence` row, the question is different in kind: the source says nothing, so
there is no reading to choose between. Ask for the missing rule directly, and offer the defaults
you would otherwise fall back to.

Between rounds, apply what you learned — a corrected belief usually collapses two later questions
into one, or reveals a dependent nobody had flagged. A belief the user confirms is **done**: mark
it `confirmed` and never re-ask it in a later round.

**Surface contradictions; do not reconcile them.** If the user's correction conflicts with what a
source artifact actually says, both cannot govern. Show both, quoted, and ask which one is right —
the artifact may be stale, or the user may be misremembering their own document. Silently choosing
the user's version and moving on is how the artifact stays wrong.

---

## Step 4 — Correct the source

The belief is now right. The thing that produced the wrong one is still there.

Locate the artifact and fix the specific claim — not a rewrite, the misleading line:

- **Plans, specs, docs in this repo** — edit the claim, or annotate it where the original wording
  matters for history. Keep the change small and cite it in your report.
- **Wiki pages** — follow the wiki-first rules. Update the page, keep `related:` links intact, and
  log the correction in `wiki/_log.md`. **Raw sources are never modified**: if the error came from
  a transcript, an export, or a pipeline output, note the correction on the wiki page and link back
  to the original rather than editing it.
- **External or user-supplied content** (a pasted document, a vendor spec, a third-party README) —
  **report, do not edit.** Quote the misleading line exactly so the user can fix it at the source.
- **An `assumed-from-silence` gap** — the fix is to add the rule the source was missing, not to
  edit anything that exists.
- **Your own earlier statement in the conversation** — nothing to edit. It gets corrected in the
  Step 8 restatement.

If the source is correct and you simply read it wrong, say that. No edit is warranted, and editing
a fine document to prevent a misreading you have already fixed makes the document worse.

---

## Step 5 — Disposition the work built on it

List everything traceable to the wrong belief: files created or edited, decisions taken, tests
written, plans generated. Be concrete — `file:line` where you can.

Present each item with a recommendation and let the user choose:

- **Keep** — the work is still correct under the corrected belief. Common, and worth saying out
  loud so nobody assumes the whole branch is poisoned.
- **Revise** — partially wrong; name what specifically changes.
- **Revert** — built entirely on the error.

**Never auto-revert.** The wrong belief and the code it produced are not the same thing; plenty of
work survives its bad premise, and throwing it away silently destroys correct work that happened to
be adjacent.

If contaminated work is **already committed**, name the commits and offer revise or revert-forward.
Do not rewrite history. **Never commit** — the user decides when work becomes a commit.

---

## Step 6 — Record it, proportionally

Always: the in-conversation summary in Step 8.

Write a durable record **when the source was corrected, or when the misunderstanding was
non-trivial** — non-trivial meaning a competent reader would have made the same mistake, or the
error survived more than a few turns before anyone noticed. A one-line misreading that produced
nothing needs no document.

The record holds four things: the wrong belief, the source text that produced it, the corrected
reading, and the disposition of the affected work. Where it goes is repo-specific — read
`skills/defect-intake/references/documentation-targets.md` for the routing (wiki page, ADR,
changelog, or a comment plus a test). Do not duplicate that logic here.

---

## Step 7 — Feed the knowledge store, if there is one

If a knowledge store exists — `wiki/knowledge/` or `./knowledge/` — write the corrected belief per
the `knowledge-loop` extract conventions, so a misunderstanding that recurs across sessions
accumulates toward a rule instead of being re-discovered each time.

If no store exists, **skip this silently.** Do not scaffold one as a side effect of a correction.

---

## Step 8 — Resume with a corrected restatement

Restate the corrected understanding in one paragraph, in your own words rather than by quoting the
user back to them — that is the only real proof the correction landed. Then, briefly:

- What the wrong belief was and which link in the chain failed (source, reading, or gap).
- What you changed in the source, with locations.
- The disposition of affected work.
- Where you recorded it, if you did.
- Anything still unresolved that you are waiting on them for.

Then continue the interrupted work.

---

## Hard lines

- **This skill does not self-trigger.** Someone sounding frustrated, a contradiction you noticed,
  two sources disagreeing — none of those are invocations. Say what you noticed and let the user
  decide whether to run it.
- **No unquoted question.** If you cannot produce the source text behind a belief, that itself is
  the finding: you inferred it from nothing.
- **A verified non-misunderstanding is a successful run.** If the ledger holds up and your reading
  was right, say so plainly with the quotes, and resume. Manufacturing an error to justify the
  invocation is worse than the invocation being unnecessary.
- **Never commits. Never auto-reverts.**

---

## Related skills

- `defect-intake` — the same discipline applied to a defect in code rather than in a reading;
  source of the blast-radius classification and the documentation routing this skill reuses.
- `plan-review` — pressure-tests a plan **before** it misleads anyone; this one runs after it did.
- `knowledge-loop` — where a recurring misunderstanding becomes a rule.
