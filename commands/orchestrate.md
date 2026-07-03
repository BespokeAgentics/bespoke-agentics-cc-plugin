---
name: "bespokeagentics:orchestrate"
description: "Fable-driven multi-agent orchestration: pass a plan file (or a raw task prompt) and the session model acts as orchestrator — grounds the plan against real source, decomposes it into model-assigned workstreams with strict file ownership, delegates implementation to Opus/Sonnet subagents, gates every phase on verification it runs itself, smoke-tests the result, runs an adversarial review over the diff, and reports faithfully. The orchestrator never writes production code. Given a raw prompt, it drafts and confirms a plan first."
argument-hint: "'<plan-path-or-task>' [--depth quick|standard|deep] [--dry-run] [--no-confirm] [--no-smoke] [--no-review] [--single-model opus|sonnet|haiku] [--resume [<slug>]] [--force]"
allowed-tools: Skill(orchestrate), Agent, AskUserQuestion, SendMessage, Bash, Read, Write, Edit, Glob, Grep, ToolSearch
---

# Orchestrate

Run the `orchestrate` skill: act as the orchestrator for a managed, gated, multi-agent
implementation of a plan. **The orchestrator delegates all production code to subagents — it
grounds, gates, reviews, and reports.**

## Arguments

Parse from `$ARGUMENTS`:

```
'<plan-path-or-task>' [--depth quick|standard|deep] [--dry-run] [--no-confirm] [--no-smoke]
                      [--no-review] [--single-model opus|sonnet|haiku] [--resume [<slug>]] [--force]
```

- `<plan-path-or-task>` (required) — a readable file is treated as the authoritative plan; any
  other text is a raw task prompt, which triggers a draft-plan-and-confirm phase first.
- `--depth quick|standard|deep` (default `standard`) — grounding fan-out width, review rigor
  (`deep` adversarially verifies findings), and smoke-matrix size.
- `--dry-run` — stop after the grounded work order; spawn no implementer.
- `--no-confirm` — skip the work-order confirmation gate (still stops on behavior-changing
  ambiguity).
- `--no-smoke` / `--no-review` — skip the smoke-test / adversarial-review phase.
- `--single-model <m>` — force all subagents to one model (default roster: Opus for
  contract-shaped/high-risk work + review, Sonnet for mechanical work + smoke driving).
- `--resume [<slug>]` — continue a prior run from its `.orchestrate/<slug>/` state (most recent
  run when no slug given).
- `--force` — ignore existing run state and start fresh.

## Process

Invoke the `orchestrate` skill and forward `$ARGUMENTS`. The skill will:

1. **(Plan Draft)** — raw-prompt input only: draft a plan, save it per the project's plans
   convention, and get explicit confirmation before anything else — the confirmed plan is the
   contract for the whole run.
2. **Pre-flight** — record git state (pre-existing changes are preserved; feature branch if on
   default), read the repo's `CLAUDE.md` conventions, discover the gate commands
   (typecheck/lint/test/build), read the plan in full.
3. **Ground** — read-only Sonnet agents verify every `file:line` anchor and claim against current
   source → corrected anchor map, contradictions, risks → `work-order.md` (waves, owners, model
   assignments, exact file ownership).
4. **Gate G0** — one AskUserQuestion batch confirms the work order and resolves the plan's open
   questions and any plan-vs-code contradictions. `--dry-run` ends here.
5. **Implementation waves** — parallel-safe items run concurrently (disjoint files + no
   unpublished interface dependency), everything else sequenced; each agent gets a verbatim packet
   (plan slice, grounded anchors, ownership, guardrails, return contract). After each wave the
   orchestrator runs the gates itself and routes exact failures back (max 2 round-trips per item).
6. **Smoke** — a Sonnet agent drives the running app (claude-in-chrome for UI) against a matrix
   derived from the plan: new behavior end-to-end, state across boundaries, and the default-path
   compatibility invariant — pass/fail with evidence.
7. **Review** — read-only Opus over `git diff` vs the recorded base ref, pressure-testing the
   plan's invariants; confirmed findings route back to owners and affected gates re-run.
8. **Close-out & report** — honor project wiki/log conventions if present, then a faithful final
   report: waves/owners, files changed, gate + smoke results with evidence, deviations from plan,
   residual risks. **Nothing is committed or pushed unless you ask.**

## Output

A resumable run record under `.orchestrate/<slug>/` (work order, per-agent reports, state), the
implemented diff on the working branch, and the final report. Interrupted or failed runs resume
with `--resume`.
