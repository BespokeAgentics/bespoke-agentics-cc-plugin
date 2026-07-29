---
name: flow-dissonance
description: "Live cognitive-dissonance audit of an app flow: drive the running app in Chrome as a user with a stated intent, pre-register an expectation before every step, and record where the experience diverges — label-vs-behavior mismatches, silent successes, momentum breaks, dead ends, promise-vs-delivery gaps. Classifies each gap against the GE*/GV*/MB*/PV* dissonance catalog, grounds findings in this repo's source (file:line) when the app is local, validates them in an interview, and writes a severity-rated read-only report to ./reviews/. Use whenever someone asks for a 'cognitive dissonance analysis', says 'walk the flow like a user', 'try the signup/checkout/onboarding flow and tell me what's confusing', 'does this flow make sense', 'friction audit', 'intent vs experience', 'use the app and critique it', or wants the app actually ATTEMPTED live rather than its code or screenshots reviewed. Distinct from ux-audit (heuristics over artifacts): this skill performs the flow and measures expectation vs. reality at each step."
---

# Flow Dissonance — live intent-vs-experience audit

## Premise

Cognitive dissonance in a product is the gap between what a user set out to do and what the
product actually put them through. It cannot be found by reading code or looking at screenshots —
those show the product's *side* of the conversation. It is found by **being the user**: forming an
intent, attempting the flow in the running app, and measuring, at every step, the delta between
what a reasonable person would expect next and what actually happened.

The load-bearing discipline is **pre-registration**. Hindsight makes every outcome look
predictable — if you act first and rationalize afterward, you will find nothing, because you (with
the full DOM, the codebase, and the docs) can explain anything. So the expectation for each step
is written down *before* the action is taken, and the finding is the recorded delta. The walk
ledger is the evidence; a finding without a pre-registered expectation is an anecdote.

Two corollaries:

- **Your own confusion is first-class evidence.** You have more context than any human user ever
  will. If *you* hesitate over which button maps to the intent, misclick, or get lost — record it.
  A human with less has it worse.
- **A walk that didn't happen produces guesses, not findings.** If no app is running and none can
  be started, stop and say so (offer the code-level `ux-audit` skill instead). Never synthesize a
  "walk" from reading source.

This skill is read-only with respect to the product: it never edits application code. Its only
outputs are the walk ledger and the report.

## Arguments

```
['<flow-or-url>'] [--persona '<description>'] [--depth quick|standard|deep]
[--out <dir>] [--no-ground] [--gif]
```

- `<flow-or-url>` — a flow description ("the checkout flow"), a start URL, or both. Omitted →
  discovery (Phase 1).
- `--persona` — who is walking (default: elicited in the interview).
- `--depth` — `quick`: single pass, no grounding, terse report. `standard` (default): full
  protocol. `deep`: every P0/P1 finding is re-driven to prove it reproduces before it is reported.
- `--out` — report directory (default `./reviews/`).
- `--no-ground` — skip codebase grounding; findings stay experiential.
- `--gif` — additionally record the walk with `gif_creator` as visual evidence.

## Phase 0 — Preconditions

1. Load the browser tools in ONE ToolSearch call (`tabs_context_mcp`, `navigate`, `computer`,
   `read_page`, `get_page_text`, `tabs_create_mcp`, plus `gif_creator` if `--gif`). Call
   `tabs_context_mcp` first. Claude-in-Chrome is the engine of record (it inherits the user's real
   sessions); if it is unavailable, fall back to the chrome-devtools MCP tools; if neither exists,
   stop and offer `ux-audit`.
2. Locate the running app, in order: a URL in the arguments → a dev server already listening
   (check the repo's dev script ports, then common ones: 3000, 5173, 8080, 4321, 8000) → offer to
   start the repo's dev command (ask first; starting servers changes machine state). Nothing
   runnable → stop honestly.
3. Create a fresh tab for the walk. Never reuse a tab the user is working in.
4. Create the evidence directory: `<out>/flow-dissonance-<slug>/` (slug from the flow name). The
   walk ledger lives at `<out>/flow-dissonance-<slug>/walk-ledger.md`.

## Phase 1 — Frame the flow

If the user named a flow, use it. Otherwise inspect the app's surface — the rendered nav, the
route map, the README, `package.json` name/description — and identify 2–3 candidate flows that
carry the product's core promise (signup, the primary object's create-and-use loop, checkout).

Then run ONE AskUserQuestion round covering, as needed:

1. **Flow choice** (only if discovering) — the candidates, each with a one-line "what a user would
   be trying to accomplish".
2. **Persona** — who is walking: first-time visitor, returning user, admin. The persona determines
   what counts as "reasonable expectation" and therefore the severity of every finding.
3. **Intent statement** — one sentence in the persona's voice: *"As a first-time visitor, I want
   to create an account and reach a screen where I can start using the product."* Propose a
   phrasing; let the user correct it.
4. **Success criterion** — what "done" observably looks like. Freeze this BEFORE walking; the
   end-of-walk thread test (and rule PV4) is measured against it.

Write the frozen frame (persona, intent, success criterion, start URL) as the ledger's header.

## Phase 2 — The walk

Drive the flow one interaction at a time. For every step, append to the ledger **in this order**:

```
### Step N
- INTENT: what the persona wants at this moment
- EXPECT: what they would expect the next action to do   ← written BEFORE acting
- ACT: the single interaction taken (control, its exact on-screen label)
- OBSERVE: what actually happened — verbatim on-screen text, where you landed, what changed
- DELTA: match | partial | dissonant   (+ one line on the gap, if any)
```

The ledger is **append-only**. Never revise an EXPECT after acting — if your expectation was
wrong in an interesting way, that is the data. Write EXPECT from the persona's knowledge, not
yours: what would someone who has never seen this codebase predict from what is on screen?

**Persona discipline.** Interact only through what the UI visibly exposes. No URL-bar jumps to
routes the UI never linked, no acting on DOM knowledge a user wouldn't have. If the only way
forward is such a trick, that IS a finding (GE1 or MB3) — record it, then use the trick solely to
continue the walk, marked `[non-user assist]` in the ledger.

**Walls and hazards:**
- Login/consent walls: pause and ask the user to log in themselves — never type credentials.
  Record the wall's position in the flow.
- Do not trigger JS `alert`/`confirm` dialogs (they freeze the automation). If a flow step would,
  note it as evidence and warn the user before proceeding.
- Destructive or outward-facing steps (real payments, sending email, posting publicly): stop at
  the brink, record the step as `not walked — irreversible`, and ask before crossing.
- If a step errors or you are stuck after ~3 honest attempts: record it (likely MB3), recover the
  way a user would (visible Back/retry), or end the walk there. A truncated walk with an honest
  ledger beats a completed walk that cheated.

**End-of-walk thread test.** Re-read the whole ledger and answer three questions in writing:
1. Was the frozen intent delivered — does the final OBSERVE satisfy the success criterion?
2. What is the total attention tax — count of `partial`/`dissonant` steps a user paid on the way?
3. Did any step change what the persona would now believe the product *is*? (That belief-shift is
   where PV findings live.)

## Phase 3 — Classify

Read `references/dissonance-catalog.md` in full. Convert every `partial`/`dissonant` delta and
every thread-test failure into findings:

- Exactly one rule ID per finding (GE1–GE4, GV1–GV4, MB1–MB5, PV1–PV4); when two fit, the catalog's
  tie-break applies (classify where the gap *opened*).
- One finding per root cause — steps sharing a cause merge into one finding with multiple evidence
  entries.
- Severity per the catalog's scale: P0 intent-breaking, P1 trust-eroding, P2 attention-tax —
  costed against the interview's persona, not a power user.
- Plain defects (crashes, broken images) that aren't dissonance go to a separate "Observations
  (not dissonance)" list — reported, never inflated into findings.

On `--depth deep`, re-drive the relevant step once for each P0/P1 before it may be reported: a
one-off render hiccup is not dissonance. Mark each `reproduced` or `not reproduced — downgraded`.

## Phase 4 — Ground (skip on `--no-ground` or `--depth quick`)

Determine whether the driven app is this repo's app (the dev server came from this repo, or
distinctive on-screen strings from the ledger appear in the source). If it is not, label the run
`experiential-only` and skip to Phase 5.

If it is: launch parallel `Explore` agents — one per finding cluster — each given the finding's
verbatim on-screen text anchors and asked to locate the responsible component, handler, or copy
string at `file:line`. Attach results to findings. A finding whose anchor can't be located stays
in the report labelled `not grounded` — never guess a location.

## Phase 5 — Validate (interview)

Present the findings in AskUserQuestion batches (≤4 per round, P0s first). For each: **real** /
**intended behavior** / **out of scope**, plus a priority check on the P0s. When the user says a
finding is intended, do not argue — record it as `reviewed: intended` (it stays in the report's
register with that status, because "intended" today is still worth a line of institutional
memory). The report reflects the user's verdicts, not raw suspicion.

## Phase 6 — Report

Write `<out>/flow-dissonance-<slug>.md` (read-only; the app is never modified). Structure:

```
# Flow Dissonance — <flow name>
Verdict: 🔴 dissonant | 🟡 friction | 🟢 coherent      ← 🔴 any confirmed P0; 🟡 any P1; 🟢 else
One paragraph: was the intent delivered, and at what cost.

## The intent            — persona, intent statement, success criterion, start URL, date, depth
## Walk summary          — steps walked, deltas (match/partial/dissonant counts), thread-test answers
## Findings              — grouped P0 → P1 → P2; each:
   [RULE-ID] Title — severity, interview status (confirmed | intended | out of scope)
   Evidence: step N, EXPECT vs OBSERVE quotes (verbatim), [gif/screenshot ref if any]
   Grounding: file:line | not grounded | experiential-only
   User impact: one sentence in the persona's terms
   Fix direction: one sentence (direction, not implementation)
## Step ledger           — the full table: step | intent | expected | actual | delta
## Observations (not dissonance) — defects and oddities seen but not classified
## Not walked            — branches not taken, walls not crossed, irreversible steps skipped. Honest.
## Definition of coherence — checklist: every step's outcome predictable from its label · every
   action visibly confirmed · no known info re-asked · every terminal state has a next move ·
   the end state satisfies the frozen success criterion
```

Close out per project conventions: if a wiki vault exists, ingest the report and add a `_log.md`
entry. Then **offer** (never assume): open the confirmed P0s as tasks, or hand the report to
`ui-issue-to-plan`/`orchestrate` for a fix plan.

## Degradation

| Missing | Behavior |
|---|---|
| No browser tools at all | Stop before Phase 2; offer `ux-audit` (code/screenshot heuristics) instead |
| No running app, none startable | Stop honestly; never simulate the walk from source |
| Login wall the user can't clear | Walk what is reachable; everything behind it goes to "Not walked" |
| App is not this repo's | Run `experiential-only` (no grounding); say so in the report header |
| `--gif` capture fails | The text ledger stands alone; note the capture failure |

## Boundaries with sibling skills

- `ux-audit` evaluates artifacts (code, screenshots, recordings) against Nielsen/Norman heuristics
  — it never touches the running app. This skill only claims what it experienced live.
- `ui-issue-to-plan` starts from a *human's* narrated recording; this skill generates the
  experience itself.
- `data-ui-craft` fixes display craft on data-dense surfaces; this skill audits flows and writes
  no production code.
