---
name: "bespokeagentics:flow-dissonance"
description: "Live cognitive-dissonance audit of an app flow: drives the running app in Chrome as a user with a stated intent, pre-registers an expectation before every step, and records where the experience diverges — label-vs-behavior mismatches, silent successes, momentum breaks, dead ends, promise-vs-delivery gaps. Classifies gaps against the GE*/GV*/MB*/PV* catalog, grounds findings in this repo's source (file:line) when the app is local, validates them in an interview, and writes a severity-rated read-only report to ./reviews/. The app is attempted live — never judged from code or screenshots alone."
argument-hint: "['<flow-or-url>'] [--persona '<desc>'] [--depth quick|standard|deep] [--out <dir>] [--no-ground] [--gif]"
allowed-tools: Skill(flow-dissonance), Agent, AskUserQuestion, Bash, Read, Write, Glob, Grep, ToolSearch
---

# Flow Dissonance — live intent-vs-experience audit

Run the `flow-dissonance` skill: be the user. Form an intent, attempt the flow in the running
app step by step, pre-register an expectation before every action, and report — with evidence
from the walk ledger — everywhere the experience diverged from the intent.

## Arguments

Parse from `$ARGUMENTS`:

```
['<flow-or-url>'] [--persona '<desc>'] [--depth quick|standard|deep] [--out <dir>] [--no-ground] [--gif]
```

- `<flow-or-url>` (optional) — flow description, start URL, or both. Omitted → the skill inspects
  the app and proposes candidate flows to choose from.
- `--persona` (optional) — who is walking; otherwise elicited in the interview.
- `--depth` (optional, default `standard`) — `quick` single pass, `deep` re-drives every P0/P1 to
  prove reproduction before reporting.
- `--out` (optional, default `./reviews/`) — where the report and walk ledger land.
- `--no-ground` — experiential-only; skip `file:line` grounding.
- `--gif` — also record the walk as a GIF for visual evidence.

## Execution

Invoke the `flow-dissonance` skill and follow it end to end: Phase 0 preconditions (browser
tools, running app, fresh tab), Phase 1 flow framing (one AskUserQuestion round freezing persona,
intent statement, and success criterion), Phase 2 the pre-register→act→observe→delta walk with an
append-only ledger, Phase 3 catalog classification, Phase 4 grounding via parallel Explore
agents, Phase 5 the validation interview, Phase 6 the read-only report.

Hard rules the skill enforces — restated because they are the contract:

- **No walk, no findings.** If no app is running and none can be started, stop and offer
  `ux-audit` instead. Never synthesize findings from source reading.
- **EXPECT before ACT, always.** The ledger is append-only; an expectation written after the
  action is hindsight and cannot back a finding.
- **Never type credentials; never cross irreversible steps** (payments, sends, public posts)
  without asking. Walls and skipped steps land in the report's "Not walked" section.
- **The user's verdicts win.** Findings the interview marks "intended" stay in the register with
  that status — never re-argued, never silently dropped.
- **Read-only.** The application is never modified; the only artifacts are the ledger, optional
  GIF, and the report. Wiki-ingest the report when a vault exists.
