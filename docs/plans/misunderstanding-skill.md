# `misunderstanding` — Skill Spec

**Created:** 2026-08-28
**Status:** Draft
**Type:** Quick Spec
**Target:** `skills/misunderstanding/SKILL.md` (bespoke-agentics plugin)

---

## Summary

A user-invoked Claude Code skill for the moment a plan, wiki claim, doc, or prior turn has led the
agent to infer something wrong. It reconstructs the inference chain behind the flagged belief,
interviews the user with specific, source-quoted questions via `AskUserQuestion`, corrects the
artifact that seeded the bad inference, dispositions the work already built on it, and resumes with
a corrected restatement. It never self-triggers and never commits.

The premise: by the time a misunderstanding is noticed, the wrong belief has usually already
produced decisions and code. Re-explaining in prose fixes the conversation but leaves the bad claim
in the source and the contaminated work in the tree — so the same error returns next session.

---

## Scope

### In Scope

- Reconstructing an **inference ledger**: belief → source (quoted, `file:line` or turn) → type
  (stated vs. inferred) → downstream artifacts → confidence.
- Scoping to the flagged belief plus its **blast radius**: siblings drawn from the same source, and
  beliefs the correction invalidates.
- A bounded `AskUserQuestion` interview (≤4 questions per call, ≤3 rounds) where every question
  quotes its source and states the agent's current belief as a selectable option.
- **Correcting the source artifact** when it lives in this repo (plan, wiki page, spec, comment).
- **Inventorying contaminated work** and presenting per-item keep / revise / revert — user decides.
- A **proportional written record**, routed by the same logic as `defect-intake`.
- Feeding the corrected belief into the **knowledge-loop store** when one exists.

### Out of Scope

- Self-triggering on detected confusion or contradiction. Invocation is the user's call.
- Sweeping the whole session for every unverified assumption.
- Editing external or user-supplied content (reported, never edited).
- Auto-reverting work. Auto-committing anything.
- Hunting for *new* misunderstandings the user did not flag.

---

## Requirements

### Core Functionality

1. **Intake (Step 0).** Accept an optional hint argument (`"you misunderstood the auth flow"`,
   a `file:line`, a quoted claim). With no argument, ask what was misunderstood rather than
   guessing. Acceptance: a run with no argument never begins a ledger from speculation.

2. **Inference ledger (Step 1).** For each candidate belief, record: the belief in one sentence,
   the source with a **verbatim quote** and locator, whether it was **stated** in the source or
   **inferred** from it, what was decided or built on it, and confidence. Acceptance: every ledger
   row carries a quote; a row without one is a guess and is labeled as such.

3. **Blast-radius scoping (Step 2).** Include the flagged belief, beliefs sharing its source, and
   beliefs whose validity depends on it. Exclude everything else. Acceptance: the run states what
   it excluded and why.

4. **Targeted interview (Step 3).** `AskUserQuestion`, ordered by blast radius. Every question:
   quotes the source, leads with the agent's current belief as an option, offers the most plausible
   alternative readings, and is never open-ended. `multiSelect` where beliefs are not mutually
   exclusive. Acceptance: no question asks "what did I get wrong?" — the user already said that;
   the skill's job is to convert it into answerable specifics.

5. **Source correction (Step 4).** Locate the artifact that produced the bad inference and fix or
   annotate the misleading claim. Wiki pages follow the wiki-first rules: **raw sources are never
   modified** — the correction is noted on the wiki page with a link back to the original. External
   content is reported with the exact misleading line, never edited.

6. **Work disposition (Step 5).** List every file, edit, and decision traceable to the wrong
   inference. Present keep / revise / revert per item. Never auto-revert. Never commit.

7. **Proportional record (Step 6).** In-conversation summary always. A durable record only when the
   source was corrected or the misunderstanding was non-trivial, routed by
   `skills/defect-intake/references/documentation-targets.md`. Content: the wrong belief, its
   source, the user's correction, and the disposition of affected work.

8. **Knowledge-loop handoff (Step 7).** When a knowledge store exists (`wiki/knowledge/` or
   `./knowledge/`), write the corrected belief per the `knowledge-loop` extract conventions.
   Silently skip when absent — never scaffold a store as a side effect.

9. **Resume (Step 8).** Restate the corrected understanding in one paragraph, list what changed,
   and continue the interrupted work.

### Business Rules

| Rule                        | Description                                                                                                                 |
| --------------------------- | --------------------------------------------------------------------------------------------------------------------------- |
| No self-trigger             | Invoked only on explicit user request. Mentioning confusion is not an invocation.                                            |
| Quote or it didn't happen   | Every belief and every question cites the source text that produced it.                                                      |
| Stated ≠ inferred           | A misread of an explicit statement and an inference from silence are different defects and are labeled differently.          |
| Surface contradictions      | When the user's correction contradicts a source artifact, say so and ask which governs. Never silently reconcile.            |
| Confirmed beliefs are done  | A belief the user confirms is recorded as confirmed and not re-asked in later rounds.                                        |
| No misunderstanding is a win | If the inferences check out, say so plainly and resume. A verified non-misunderstanding is a successful run.                 |
| Never commits               | The user decides when work becomes a commit.                                                                                 |

---

## Technical Approach

### Architecture

- Single skill: `skills/misunderstanding/SKILL.md`, prose-directive house style, ~150–250 lines.
- **No command wrapper.** Per project `CLAUDE.md`, capabilities that ship as a skill get no
  `commands/*.md` file; invoked as `/bespoke-agentics:misunderstanding`.
- Frontmatter: `name` + a `description` block written for retrieval — the "invoke only when the
  user asks" clause stated explicitly, with trigger phrases ("you misunderstood", "that's not what
  I meant", "you inferred that wrong", "clarify before you continue", "run misunderstanding").
- Depth material in `references/` only if a step exceeds ~40 lines inline. Documentation routing is
  **referenced**, not duplicated, from `defect-intake`.

### Data Model

The inference ledger, rendered as a markdown table in-conversation (no persisted schema):

| Field        | Content                                                     |
| ------------ | ----------------------------------------------------------- |
| `belief`     | One sentence, the agent's current understanding             |
| `source`     | Verbatim quote + `file:line`, wiki page, or conversation turn |
| `type`       | `stated` \| `inferred` \| `assumed-from-silence`            |
| `downstream` | Files, edits, decisions produced under it                   |
| `confidence` | `confirmed` \| `probable` \| `uncertain`                    |

### Key Implementation Notes

- Interview limits are harness limits: ≤4 questions per `AskUserQuestion` call, ≤4 options each,
  first option is the recommendation.
- Question construction borrows `interactive-wireframe`'s contradiction hunting and
  `defect-intake`'s blast-radius classification — cite both in the skill's "related skills" note.
- Registration on ship: entry in project `CLAUDE.md` command table + skills tree, keywords in
  `.claude-plugin/plugin.json`, version bump in `plugin.json` and `marketplace.json`.

---

## Edge Cases & Error Handling

| Scenario                                                | Behavior                                                                                            |
| ------------------------------------------------------- | ---------------------------------------------------------------------------------------------------- |
| Invoked with no argument                                | Ask what was misunderstood. Do not sweep the session for candidates.                                 |
| Conversation was compacted; the source turn is gone     | Say so, rebuild from artifacts on disk, label anything reconstructed from memory as unverified.       |
| The agent's inference turns out correct                 | Report it plainly with the quote, resume. No record written.                                          |
| Source is a raw pipeline output / transcript            | Never edit. Note the correction on the wiki page and link back to the original.                        |
| Source is external (a pasted doc, a vendor spec)        | Report the misleading line verbatim; offer no edit.                                                    |
| User's correction contradicts a source artifact         | Surface both, ask which governs, record the resolution in the source correction.                       |
| Contaminated work is already committed                  | Inventory it, name the commits, present revise / revert-forward options. Never rewrite history.        |
| Many beliefs affected                                   | Order by blast radius, cap at 3 interview rounds, and report what was left unasked rather than dropping it silently. |
| No knowledge store present                              | Skip Step 7 silently. Do not scaffold one.                                                             |

---

## Assumptions Made

1. Skill name is `misunderstanding`; the user's phrasing is the trigger vocabulary.
2. It ships as a skill only, no `commands/` wrapper — per the note in project `CLAUDE.md`.
3. House style is the `defect-intake` register: premise paragraph, numbered steps, hard lines
   stated as rules, tables for classification.
4. `defect-intake`'s `documentation-targets.md` is reusable across skills in the same plugin and
   should be referenced rather than copied.
5. The skill assists the *current* session's agent — it reads the live conversation, not a
   transcript file.
6. `AskUserQuestion` is the interview mechanism (the user wrote "AskQuestion tool"; the actual
   harness tool is `AskUserQuestion`).

---

_Quick spec generated through rapid elicitation with codebase-informed recommendations._
