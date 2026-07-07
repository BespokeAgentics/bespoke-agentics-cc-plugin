---
name: "bespokeagentics:agent-loop-audit"
description: "Audit (and optionally fix) an AI API/SDK integration for the event-loop defects that cause silent hangs, stalls, and deadlocks in managed-agent architectures: payload-before-listener races, idle treated as done instead of branching on stop_reason, unanswered requires-action tool approvals (server-side deadlock), undifferentiated error handling, no reconnect/resume or silence watchdog, and no interrupt+redirect steering path. Tiered rules: a stack-agnostic core catalog for any event-stream client plus an Anthropic-specific pack (user.message/user.interrupt, session.status.idle, stop_reason, agent/session/fan event families) that activates when an Anthropic SDK is detected. Writes a severity-rated, file:line-cited report with a per-surface loop-health matrix, then — gated behind an interview — applies the accepted fixes in place."
argument-hint: "[mode: audit|implement|audit-and-implement] [path]"
allowed-tools: Skill(agent-loop-audit), Agent, AskUserQuestion, Bash, Read, Write, Edit, Glob, Grep
---

# Agent-Loop Audit

Run the `agent-loop-audit` skill: audit an AI API/SDK integration's event loop against the
managed-agent control-surface rule catalog, then (by default) implement the fixes you accept —
matching the project's stack and conventions.

## Arguments

Parse from `$ARGUMENTS`:

```
[mode: audit|implement|audit-and-implement] [path]
```

- `mode` (optional, default `audit-and-implement`) — `audit` writes the read-only report only;
  `implement` applies fixes from an existing report without re-auditing; `audit-and-implement`
  audits, lets you choose what to fix, then implements.
- `path` (optional) — scope to a file, directory, or service. Defaults to every agent-loop
  surface the skill discovers.

## Process

Invoke the `agent-loop-audit` skill and forward `$ARGUMENTS`. The skill will:

1. **Detect** the stack — language (TS/JS, Python), AI SDKs, transport (SDK-managed vs raw
   SSE/WebSocket), frameworks, and existing error/retry/logging conventions. An Anthropic SDK
   activates the Anthropic rule pack; unknown vendors get the core catalog with vendor-specific
   findings flagged `unconfirmed-vendor`.
2. **Discover** every agent-loop surface: where tasks are dispatched and where (or whether)
   events are consumed — dispatch site, listener site, loop site, teardown site.
3. **Audit** each surface against the rule catalog (`EL*` lifecycle, `SR*` stop-reason semantics,
   `RS*` resilience & steering, `OB*` observability), severity-rating every finding with a
   `file:line`, the user-visible symptom it produces, and a fix pointer — written to
   `./agent-loop-audit.md` with a per-surface loop-health matrix.
4. **Interview** (in `audit-and-implement`) — frame intent (CRITICAL hang/deadlock class only vs
   also resilience best-practices vs also steering/observability), confirm each finding is real
   and in-scope. No edit before this gate.
5. **Implement** the accepted set in dependency order: listener-first initialization →
   stop-reason branching on idle (including answering pending tool approvals) → safe teardown →
   error differentiation, watchdog, reconnect/resume, idempotent tools → event-family decoding
   and layered surfacing.
6. **Verify** — the project's own typecheck/lint/tests, plus re-greps confirming each fixed
   anti-pattern is gone.

## Output

`./agent-loop-audit.md` (verdict 🟢/🟡/🔴, severity-grouped findings, loop-health matrix,
strengths, deferred items) and — only for accepted findings — in-place code fixes. Wiki-ingested
when a vault exists. The destructive step is always gated behind your explicit choice.
