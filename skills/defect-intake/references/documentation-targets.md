# Where a defect fix gets documented

Read this at Step 6 of the intake. The goal is to put the record where someone will actually find
it when they hit the same code — which is a different place in every repo, and picking wrong means
the step was wasted effort.

## Contents

- [Find the convention before inventing one](#find-the-convention-before-inventing-one)
- [Destinations, in priority order](#destinations-in-priority-order)
- [Repos with a wiki](#repos-with-a-wiki)
- [Repos with ADRs](#repos-with-adrs)
- [Repos with a changelog](#repos-with-a-changelog)
- [Repos with no convention](#repos-with-no-convention)
- [The code itself](#the-code-itself)
- [What to write](#what-to-write)
- [Proportionality](#proportionality)

## Find the convention before inventing one

Do not create a new documentation location. A fix recorded in a file the team does not read is
indistinguishable from an undocumented fix, and a new stray `NOTES.md` at the repo root is worse
than nothing because it fragments the knowledge that already has a home.

Look, in this order:

1. The project's `CLAUDE.md` / `AGENTS.md` — these frequently state the documentation workflow
   directly, including required log rows or page updates. If it does, follow it exactly; it
   outranks everything else here.
2. `CONTRIBUTING.md`, `docs/README.md`, or a `docs/` index.
3. The shape of the repo: `docs/wiki/`, `docs/adr/`, `decisions/`, `CHANGELOG.md`, `plans/`.
4. Recent history — `git log --stat -20` shows what files real fixes touched alongside code. If
   every bugfix commit also touches `CHANGELOG.md`, that is the convention.

## Destinations, in priority order

When more than one exists, prefer the one closest to the code's own knowledge base rather than the
one that is easiest to append to.

## Repos with a wiki

A wiki is usually the source of truth, and usually has schema rules that a lint step enforces —
which means an ad-hoc page will fail CI or get reverted. Read the wiki's own schema and process
docs before writing.

Typical obligations, all of which are easy to half-do:

- Update the affected component / feature / plan page with the fix and its reasoning, rather than
  creating a new page for a bug that belongs to an existing subject.
- Record newly-discovered risks under the page's `## Risks` heading and unresolved questions under
  `## Open Questions` — a defect frequently reveals both, and those sections are where the next
  session looks.
- Append the activity-log row if the wiki has one, using its documented schema exactly.
- Run the wiki's lint command afterward.

If the wiki has a page for the subsystem but the defect is small, extend the existing page. New
pages are for new subjects.

## Repos with ADRs

Use an ADR only when the fix embodies a decision that constrains future work — a changed contract,
a rejected alternative approach, a deliberate tradeoff. Routine bugfixes are not decisions and
should not become ADRs; diluting the ADR directory with bugfix notes makes the real decisions
harder to find.

## Repos with a changelog

Add the entry in the file's existing style and section (Unreleased / Fixed, or whatever it uses).
Changelogs are user-facing, so write the symptom in terms a consumer of the software would
recognize — not the internal cause. If the root-cause reasoning is worth preserving and does not
belong in a user-facing changelog, pair the changelog line with a code comment (below).

## Repos with no convention

Do not invent a docs tree. Prefer, in order:

1. A comment at the fix site explaining *why* the code is now this way (see below).
2. The test itself — a well-named test with a clear assertion documents the defect permanently and
   is enforced, which no prose is. `rejects_expired_token_even_when_cached` records more than a
   paragraph would.
3. The PR/commit body, if the user later commits — mention that you have written it there for them
   rather than committing yourself.

## The code itself

The most durable documentation of a defect is usually a short comment at the fix site plus the
regression test, because both travel with the code and neither can drift out of sight.

Write the comment to explain the non-obvious constraint, not the change:

```
// Trailing whitespace must survive normalization here — the upstream export pads
// fixed-width fields, and trimming silently merged distinct SKUs (see regression
// test `preserves_padded_sku_boundaries`).
```

Not `// Fixed bug where SKUs merged` — that describes an event in history, which the next reader
cannot act on. The constraint is what stops them from reintroducing it.

Never leave a `TODO` or `FIXME` as the documentation of a defect you decided not to fix. That is
deferral, and Step 2 of the skill covers what to do instead: escalate in the conversation.

## What to write

Regardless of destination, the content is the same four things:

- **Symptom** — what was observably wrong.
- **Root cause** — the actual mechanism, not the first plausible theory.
- **Fix** — what changed, with file references.
- **Why it was wrong** — the reasoning that generalizes. This is the highest-value part and the
  most commonly omitted, because it is the only part that prevents the *class* of defect rather
  than the instance.

If a defect was verified as *not* a defect (Step 1 killed it), that is still worth recording when
the code is misleading enough that the next reader will also suspect it. A short comment saying why
the surprising thing is correct saves a future investigation.

## Proportionality

Match the depth of the record to the cost of rediscovering it. A null check that took two minutes
to find needs a test and nothing else. A concurrency bug that took an hour to understand deserves
the full write-up, because the next person pays that hour again otherwise.

Over-documenting has a real cost too: it buries the important records in noise and trains readers
to skim. When in doubt, write less prose and a better test name.
