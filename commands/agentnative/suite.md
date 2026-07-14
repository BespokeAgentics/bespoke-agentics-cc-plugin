---
name: "agentnative:suite"
description: "Orchestrate the Agent-Native Engineering suite end to end: probe the repo across all six dimensions (CI speed, hermetic deploy, sim data, proof-of-work, label-dispatched agents, chore crons), write a 🟢/🟡/🔴 readiness scorecard with evidence, then — gated behind an interview that picks dimensions, modes, and budget — dispatch the individual skills in dependency order (fast-ci → hermetic-deploy → sim-data → proof-of-work → issue-to-agent → chore-crons), persisting state so an interrupted or repeated run skips what already landed. Use when the user says 'make this repo agent-native', 'set up the whole agent suite', 'where do we stand on agent readiness', or wants the six skills sequenced instead of run piecemeal."
argument-hint: "[mode: assess|run] [dimensions: 'fast-ci,hermetic-deploy,...'] [--resume]"
allowed-tools: Skill(fast-ci), Skill(hermetic-deploy), Skill(sim-data), Skill(proof-of-work), Skill(issue-to-agent), Skill(chore-crons), Agent, AskUserQuestion, Bash, Read, Write, Edit, Glob, Grep
---

# Agent-Native Suite

Sequence the six Agent-Native Engineering skills against this repo: assess readiness, confirm a
plan, then run the skills in dependency order. You are the conductor — the individual skills own
their own pipelines, interviews, and quality bars; this command decides *whether*, *in what
order*, and *tracks what landed*. Do not duplicate their work or second-guess their internals.

## Arguments

Parse from `$ARGUMENTS`:

```
[mode: assess|run] [dimensions] [--resume]
```

- `mode` (optional, default `run`) — `assess` stops after the scorecard; `run` continues into
  interview + dispatch.
- `dimensions` (optional) — comma-separated subset to consider (`fast-ci`, `hermetic-deploy`,
  `sim-data`, `proof-of-work`, `issue-to-agent`, `chore-crons`). Defaults to all six.
- `--resume` — load `.agentnative/suite-state.json` and continue from the first unfinished
  dimension, skipping the assessment of anything already recorded as landed.

## Why this order

The chain is a dependency argument, not a preference: **fast-ci** first because every later
skill's verification loop runs through the checks it accelerates; **hermetic-deploy** second
because proof-of-work needs something running to point a browser at and sim-data needs an
instance to seed; **sim-data** third because evidence screenshots and smoke runs only mean
something over realistic data; **proof-of-work** fourth, consuming the running seeded instance;
**issue-to-agent** fifth because dispatched agents inherit all of the above (fast verify, own
instance, real data, evidence conventions); **chore-crons** last because unattended scheduled
agents should be trusted only after the supervised ones have earned it. The interview may
reorder or skip — record any deviation and its rationale in the scorecard.

## Phase A — Assess (read-only)

Probe each dimension cheaply — greps and file reads, no subagent fan-out unless the repo is
huge. Score 🟢 landed / 🟡 partial / 🔴 absent, each with one line of evidence:

| Dimension | 🟢 signals (examples) | 🔴 signals (examples) |
|-----------|----------------------|----------------------|
| fast-ci | TS7/oxlint/oxfmt/uv/ruff in configs; `merge_group` triggers; <3-min fast lane | tsc≤6 + ESLint + Prettier + pip; E2E/matrix jobs on `pull_request` |
| hermetic-deploy | `scripts/dev-stack.sh` or equivalent; compose `name:`; no fixed host ports; healthchecks | no compose; `"5432:5432"`; host-assumed services |
| sim-data | `seeds/<scenario>/` with manifests; deterministic seed contract | hand-typed fixtures; empty dev DB |
| proof-of-work | agent-browser/Playwright capture wired; `evidence/` convention; PR evidence comments | no capture tooling; assertions without artifacts in recent PRs |
| issue-to-agent | claude-code-action workflows on issue events; `agent:*` labels | no issue automation |
| chore-crons | scheduled workflows with self-verification + tracking channels | no `schedule:` triggers; visible neglected tail |

Also capture the two numbers that anchor everything: current `git push`→green estimate (from
workflow topology) and whether an agent can get a running instance today (yes/no/partially).

Write the scorecard to `./plans/agentnative-suite.md`: per-dimension color, evidence,
recommended mode (`audit`/`plan` vs `implement`), and the proposed order with any
repo-specific reordering rationale. Initialize or update `.agentnative/suite-state.json`:

```json
{
  "assessed_at": "<ISO date>",
  "order": ["fast-ci", "hermetic-deploy", "sim-data", "proof-of-work", "issue-to-agent", "chore-crons"],
  "dimensions": {
    "fast-ci": { "score": "🔴", "status": "pending", "mode": "audit-and-implement", "notes": "" }
  }
}
```

In `assess` mode, present the scorecard and stop.

## Phase B — Interview (one gate, before any dispatch)

One AskUserQuestion pass covering: which 🔴/🟡 dimensions to take on now (recommend at most
2–3 per session — each skill has its own interview and the user's attention is the scarce
resource); per-dimension mode (read-only audit/plan vs implement); order confirmation or
override; and session budget (stop after N dimensions / N hours of agent work). 🟢 dimensions
are skipped unless the user opts in for a re-audit.

## Phase C — Dispatch

For each selected dimension in confirmed order:

1. Mark `in_progress` in the state file.
2. Invoke the skill via its Skill tool with the chosen mode as its argument. Let the skill run
   its own interview and quality bar — do not pre-answer its questions or suppress its gates.
3. On completion: record `landed` (or `audited` for read-only modes) with the skill's report
   path and one-line outcome in the state file and scorecard.
4. On failure or a skill's own verification refusing to pass: record `blocked` with the reason,
   **stop the chain**, and ask the user — never continue building on a layer that didn't land.
5. Between dimensions, honor the session budget from Phase B.

## Close-out

Update `./plans/agentnative-suite.md` with the final per-dimension status table, what changed
this session, what remains, and the recommended next session's slice. When a wiki vault exists,
log the run in `wiki/_log.md` per the wiki-first mandate. Report faithfully — blocked and
deferred dimensions included, no rounding up to "done".

## Degradation

- **Non-GitHub repo / no CI** — dimensions degrade per their own skills' rules; the scorecard
  notes which worked paths are adapted rather than verified.
- **No `.agentnative/` write access** — keep state inside the scorecard file itself (a
  `## State` section) so `--resume` still works.
- **User invokes mid-suite in a fresh session** — `--resume` reads state; if the state file and
  reality disagree (e.g. dev-stack.sh deleted since), re-probe that dimension before trusting it.
