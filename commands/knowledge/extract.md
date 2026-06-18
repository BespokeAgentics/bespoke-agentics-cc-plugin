---
name: "knowledge:extract"
description: "After a task: extract insights into the domain store — write facts, open or reinforce hypotheses (one distinct, dated, linked source per increment), auto-promote any hypothesis confirmed 3+ times, and auto-demote any rule new evidence contradicts."
argument-hint: "[<what you learned>] [--domain <slug>]"
allowed-tools: Skill(knowledge-loop), Read, Write, Edit, Glob, Grep, AskUserQuestion
---

# Knowledge Loop — Extract (after a task)

Close the loop: turn what just happened into durable knowledge and move it up the confidence
ladder (facts → hypotheses → rules) under strict evidence rules.

## Arguments

Parse from `$ARGUMENTS`:

```
[<what you learned>] [--domain <slug>]
```

- `<what you learned>` — optional summary; otherwise the skill harvests insights from the
  conversation, diffs, and any meeting/transcript in scope.
- `--domain <slug>` — file insights under a specific domain (a new domain is created if needed).

## Process

Invoke the `knowledge-loop` skill with `mode: extract`. It reads `references/loop-algorithm.md`,
then:

1. **Classifies each insight** — discrete observation → **fact** (`knowledge.md`); candidate
   generalization → **hypothesis** (`hypotheses.md`); evidence for/against an existing entry →
   a **counter increment**.
2. **Moves counters honestly** — increments only when the source is *distinct* from those already
   logged on the entry (counter-integrity guard); evidence against increments `contradictions`.
3. **Auto-promotes** any hypothesis at `confirmations ≥ 3` (distinct) and `contradictions = 0`
   into `rules.md`, evidence trail intact.
4. **Auto-demotes** any rule a new source contradicts back to `hypotheses.md` (`status: demoted`);
   marks a bridged wiki page `status: revisited` if one exists.
5. **Updates** `INDEX.md` counts and appends a line to `wiki/_log.md`.

Ends with a compact summary: what moved between layers, what was promoted/demoted, and the next
action (usually `/knowledge:promote` if a rule was born).

## Examples

```bash
/knowledge:extract "Acme's 22% discount went to the VP — that's the third time"
/knowledge:extract --domain onboarding
```

## Notes

- A free-text claim with **no linkable source** can be filed as a fact but **cannot** move a
  hypothesis/rule counter — promotion requires distinct, dated, linked evidence.
