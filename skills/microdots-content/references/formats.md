# Content formats

Four formats, one research pass. The research (SKILL.md Step 2) is identical;
only the shape of the output changes.

## 1. Work recap / blog post

Time-scoped narrative of shipped work. The default when the ask names a window.

Structure:

```
# <Title — the theme of the window, not "Weekly update">
<Dek: one sentence, what happened and why it matters>

## The short version          — 3-5 bullet KPI band (commits, dots touched,
                                plans shipped) — every number from a command
## <2-4 narrative sections>   — grouped by theme, NOT by commit order.
                                Each section: what changed → why → the
                                interesting decision or trap hit
## What's next                — from wiki/plans/active/, labeled in-flight
```

- A window is a story only if you find its theme. Ten commits about the nav
  capsule is one section titled "The nav became a capsule", not ten bullets.
- Commit hashes appear inline in mono where a claim rests on them.
- One diagram maximum unless the window genuinely spans systems.

## 2. Changelog / release notes

Terse, structured, per-change. No narrative.

```
# Changelog — <window>

## <area>                     — microdots/<name>, host, platform, runtime, wiki
- <hash> <imperative summary, one line>
```

- Group by area, order areas by amount of change, order entries newest first.
- Preserve the commit's conventional-commit type when it has one.
- Merge commits and formatting-only commits are omitted — say at the top how
  many commits the window held and how many the log lists.
- No diagrams.

## 3. Feature deep-dive

One MicroDot or capability, explained in depth. Not time-scoped.

```
# <Name — what it is in five words>
<Dek: the problem it exists to solve>

## The problem                — before-state, concrete
## How it works               — contract first (it IS the public surface),
                                then the flow; the natural diagram home
## The decisions              — from the plan page: what was tried, rejected,
                                and why. This section is the reason to read.
## Where it stands            — gaps and open questions, honestly, from the
                                wiki's gap/question pages
```

- Read `contract.ts` before any other source file — describe the surface, then
  the implementation.
- "The decisions" without a plan-page source is speculation — if no plan page
  exists, say the history is unrecorded rather than reconstructing it.

## 4. Social / short-form

Derived from an existing research pass — never researched independently.

- Up to 3 variants in one `.social.md` file, separated by `---`.
- Each variant standalone: ≤ 280 characters, or a 2-4 post thread with each
  post ≤ 280.
- Lead with the concrete artifact (the number, the mechanism, the trap), not
  the announcement of the artifact.
- No hashtag spam — at most one, only if it is a real term of art.
- Every claim must appear in the parent piece. Social copy compresses; it does
  not add.
