# Artifact templates

Every template here is a shape, not a form to fill blindly. Adapt section names to the host
organization's vocabulary when the interview surfaces one, keep the load-bearing parts (author,
status, acceptance, open questions, flagged concerns), and always populate with the real repo's
commands, paths, and named owners from Phase 0 + the interview.

## §1 · intent.md

The entry artifact. Written in the originator's language — no formal spec-speak. Status moves
`draft → accepted` only by the named product owner; the accepting merge/review IS the recorded
decision.

```markdown
# Intent: <short name>
Author: <name> (<role/team>). Status: draft.

## Problem
What can't be done today, and who feels it. Concrete, observed, in the
originator's own words.

## Proposed outcome
What better looks like. Outcome, not implementation.

## Affected users and systems
People, teams, services, APIs.

## Constraints
Hard limits: data (e.g. no new PII), auth, compliance, budget, deadline.

## Open questions
Everything unresolved. These must be answered or explicitly carried
forward by spec.md — silence is not an answer.
```

## §2 · spec.md

Drafted by the agent from the accepted intent with the organization's skills loaded as
constraints; reviewed (not written) by the product owner. Lives beside its `intent.md` — the pair
records what was asked for and what was decided.

```markdown
# Spec: <name> (from intent.md <date>)
Status: draft. Skills in force: <list the policy skills that were loaded>.

## Summary
The change, in two sentences, tied to the intent's problem statement.

## Requirements
Numbered, testable. Each traces to the intent's problem or outcome.

## Design
How it lands in THIS codebase: components touched, data flow, API
shape. Cite real paths.

## Intent's open questions
Each one: answered here (how), or carried forward (why + owner).

## ⚠ Flagged concerns
The points an analyst would escalate — ESPECIALLY contradicting
policies ("brand requires X, accessibility standard requires Y").
Each concern names its policy owner. Resolve before engineering sees
this spec.

## Out of scope
Explicitly, so the plan doesn't grow it back.
```

## §3 · plan.md

Produced in plan mode from intent + spec; committed on acceptance. The bar: an engineer who never
saw the conversation could implement from this alone. Sync rule: implementation departs → update
`plan.md` in the same commit (the PR review checks the diff against it).

```markdown
# Plan: <name> (from intent.md <date>, spec.md <date>)

## Files that change
Real paths, (new) marked. One line each on what changes there.

## Order of work
Numbered steps in dependency order. Independent steps marked — they
can run as parallel sessions (play B6).

## Risks
What this could break; the riskiest step; known landmines (rate
limits, frozen packages, migration order).

## Rejected alternatives
What was considered and why not — the reviewer will ask.

## Proof
The tests that prove it (real test paths), the quantified target
("all four claim states covered"), the visual check if UI.
```

## §4 · CLAUDE.md verification block (play T1)

Append to the host `CLAUDE.md`, populated with the repo's REAL commands from Phase 0 and an
example of healthy output for each:

```markdown
## Verifying your work

- Build: <cmd> (healthy: "<expected tail of output>")
- Test: <cmd> (all green; never skip or delete a failing test)
- Lint: <cmd> (zero warnings)

Run all of these before reporting any task complete, and paste the
output. If a test fails, fix the code, not the test. For bug fixes:
write the failing test first, watch it fail for the expected reason,
commit it, then fix without editing the test.
```

## §5 · Verifier subagent (play B6) — `.claude/agents/verifier.md`

A fresh context window for the final check, so the verdict isn't colored by the assumptions that
produced the code. Report-only by design.

```markdown
---
name: verifier
description: Runs the app and checks the change works before the
  session reports done
tools: Bash, Read
---
Start the app with <repo's real run command>. Exercise the changed
behavior and the two nearest neighboring flows. Report what you ran,
what you saw, and any behavior that does not match plan.md. Do not fix
anything; report only.
```

## §6 · Seed policy skill (play B4) — `.claude/skills/<name>/SKILL.md`

Shape for the one policy the interview names. Frontmatter description says WHEN it triggers; body
says WHAT to do, as checkable steps; end with a deterministic check when one exists. Remember the
governance line: this is advisory — a policy that must ALWAYS hold also needs a hook (B5) or a
review pass (D1) behind it.

```markdown
---
name: <policy-slug>
description: Apply <the standard>. Use whenever <the concrete task
  contexts where it applies, phrased broadly enough to trigger>.
---
# <Policy name>

When you <do the relevant task>:
1. <Checkable rule with its threshold or enum>
2. <Checkable rule>
3. <What must never appear where — logs, errors, diffs>

Run <deterministic check script if one exists> and include its output
in your summary.
```

## §7 · REVIEW.md (play D1)

At the repo root; the review policy the AI reviewer runs. Calibrate the passes, the
Important-vs-Nit line, and the exclusions to the repo in the interview.

```markdown
# Review instructions

## Passes
Run three passes and tag each finding with its pass:
- Bugs: logic errors, broken edge cases, subtle regressions
- Security: injection risks, authentication gaps, <repo's data class>
  in logs
- Compliance: the change matches spec.md, plan.md and <the repo's
  design principles doc, if any>

## What Important means here
Reserve Important for findings that would break behavior, leak data or
breach a policy. Style and naming are nits.

## Cap the nits
Report at most five nits per review; summarize the rest as a count.

## Do not report
<Generated paths for THIS repo> and anything CI already enforces.

## Feedback rule
A mistake flagged for the second time gets its correction added to
CLAUDE.md as part of the review. Flag when a change makes CLAUDE.md
outdated.
```

## §8 · Lessons file entry (play M3)

```markdown
## <date> — <incident short name>
Channel/thread: <link>. Severity: <sev>. Resolved by: <name>.
What happened / root cause / fix (PR link) / what future
investigations should know. Eval added: <evals/<case> or why not>.
```
