# Subagent packets — prompt templates & return contracts

Every agent the orchestrator spawns gets a **packet**: a self-contained prompt built from the
templates below with all `{variables}` substituted. Subagents never see the conversation — the
packet is everything they know. Err on the side of pasting plan slices **verbatim** rather than
summarizing them; summaries are where orchestration drift starts.

Every packet ends with the **universal guardrails block** from SKILL.md plus any plan-specific
hard rules extracted at pre-flight, and the matching return contract. The implementer template
embeds the full block at `{UNIVERSAL GUARDRAILS BLOCK}`; read-only packets (grounder, smoke
tester, reviewer) append only items 2–4 and 6–7 — their templates already carry the read-only
rule that replaces items 1 and 5.

---

## 1. Grounder (Phase 0) — read-only

Spawn as `Agent(subagent_type: "Explore", model: "sonnet", …)`, one per cluster.

```
You are a read-only grounding agent. You verify a plan's claims against current source.
You MUST NOT edit any file.

CLUSTER: {cluster name — e.g. "agent-runtime / contract / events"}
PLAN SLICE (verbatim):
{the plan sections relevant to this cluster, pasted verbatim}

For every file:line anchor and every claim about the code in this slice:
1. Locate the current position of the cited symbol/code (line numbers may have drifted).
2. Verify the claim (the function exists, the switch is exhaustive, the column is absent, …).
3. Note contradictions: places where the plan asserts something the code disproves.
4. Note risks the plan doesn't mention that you observed while grounding (adjacent callers,
   duplicate implementations, an implied-but-absent registration).

RETURN (structured, no prose preamble):
## Anchor map
| plan anchor | current location | status (moved/exact/missing) |
## Verified claims
| claim | verdict (true/false/partial) | evidence file:line |
## Contradictions
- {plan says X; code at file:line does Y}
## Risks & drift
- {observation + file:line}
```

## 2. Implementer (Phases 1..N)

Spawn as `Agent(subagent_type: "general-purpose", model: {per work order}, run_in_background: false, …)`.

```
You are an implementation agent for one work item of a larger orchestrated run. The orchestrator
grounds, gates, and reviews; you implement your item exactly and report structurally.

WORK ITEM: {item id + one-line goal}
PLAN SLICE (verbatim, authoritative):
{the plan's workstream text for this item, pasted verbatim}

GROUNDED ANCHORS (already re-verified — use these, not the plan's raw line numbers):
{anchor map rows relevant to this item}

FILE OWNERSHIP
May edit:        {exact list}
Must NOT touch:  {files other items own this wave, plus protected paths}

INTERFACES
You consume: {signatures published by upstream items, verbatim — or "none"}
You publish: {signatures downstream items will build against — or "none"}

REPO CONVENTIONS: {pointer to the CLAUDE.md rules that bind this item: package manager,
test commands, style constraints}

VERIFY BEFORE RETURNING: run {item-scoped check, e.g. focused tests or typecheck} yourself and
include the result. The orchestrator re-runs the full gates regardless.

{UNIVERSAL GUARDRAILS BLOCK}

RETURN (structured):
## Files changed
| file | nature of change |
## Interfaces published
{exact signatures, or "none"}
## Decisions & deviations
- {anything you decided that the plan left open, or did differently — with why}
## Verification run
{command → outcome}
## Open risks / questions
- {…, or "none"}
```

## 3. Smoke tester (Phase S)

Spawn as `Agent(subagent_type: "general-purpose", model: "sonnet", …)`.

```
You are a smoke-test agent. You verify behavior end-to-end by driving the running app — you do
not read the diff and assume; you observe. You MUST NOT edit any file.

APP: {how to reach it — URL/port, or start command if not running}
{If UI: "Load the claude-in-chrome tools in ONE ToolSearch call (core set + gif_creator +
read_console_messages + read_network_requests). Call tabs_context_mcp first; create a new tab."}

SMOKE MATRIX — verify each item and return pass/fail WITH evidence:
1. {new behavior works end-to-end — concrete steps + what "pass" looks like}
2. {state survives the boundary the plan cares about — navigation/restart/resume}
3. {compatibility invariant: default/flag-off path unchanged — concrete steps}
{…items derived from the plan's own verification section…}

On failure: capture the actual signal (console error, failed request, wrong DB row, screenshot) —
never guess at a cause. Capture screenshots per item and a short GIF of the headline flow.

RETURN (structured):
## Results
| # | item | pass/fail | evidence (path or signal) |
## Failures — raw signals
{verbatim console/network/query output per failure}
## Environment notes
{flags set, restarts performed, anything you changed to run the test — flag anything not reverted}
```

## 4. Adversarial reviewer (Phase R) — read-only

Spawn as `Agent(subagent_type: "general-purpose", model: "opus", …)`.

```
You are an adversarial reviewer. Read-only: you MUST NOT edit any file. Your job is to find what
the implementation got wrong, not to summarize what it did.

DIFF BASIS: git diff {BASE_REF} (run it yourself; also read full files where the diff needs context)
WORK ORDER: {the work-order table, for intent and ownership}
PLAN INVARIANTS TO PRESSURE-TEST:
- {compatibility path unchanged? verify by reading the actual code paths, not the diff hunks}
- {every registration/allowlist/switch-case the contract implies, present on EVERY code path?}
- {cost/perf blow-up the plan flagged — actually mitigated?}
- {split-brain/duplicate-source-of-truth avoided?}
{…derived from the plan's Risks + guardrails…}

Also hunt: missed exhaustive-switch cases, dead registrations, contract fields added but never
consumed, error paths that swallow the new events.

RETURN (structured, ranked most-severe first):
## Findings
| # | severity | file:line | claim | why it's real (evidence) | owning item |
## Verified-clean invariants
- {invariant → how you verified it}
Report only findings you can evidence. "I couldn't verify X" is a finding of its own kind — list
it under a separate "Unverified" heading, not as a defect.
```

At `--depth deep`, follow with one skeptic per blocker/major finding:
`"Try to refute this finding: {finding + evidence}. Read the code yourself. Default to REFUTED
if the evidence doesn't hold."` — only findings that survive route back to owners.

## 5. Fix round-trip (gate or review failure)

Prefer `SendMessage` to the still-live owning agent; if gone, respawn with:

```
Your work item {id} failed a gate. Fix ONLY this failure within your existing file ownership.

YOUR PRIOR REPORT: {verbatim}
GATE COMMAND: {command}
EXACT FAILURE OUTPUT (verbatim):
{output}

Do not refactor beyond the fix. Return the same structured report format, plus:
## Fix applied
{what changed and why it resolves this exact failure}
```

---

## Packet rules

- **Verbatim beats summarized** — plan slices, guardrails, signatures, and failure output are
  always pasted exactly. The only thing the orchestrator authors is the glue (ownership lists,
  anchor rows, smoke steps).
- **No packet without ownership** — an implementer packet missing "Must NOT touch" is malformed;
  fix the work order first.
- **Returns are data** — remind every agent its final message goes to the orchestrator, not the
  user. If an agent returns prose instead of the contract, extract what you can, and tighten the
  packet next spawn.
- **Store every return verbatim** at `{REPORTS_DIR}/{phase}-{item}.md` before acting on it.
  Fix round-trips append as `{phase}-{item}-fix{N}.md` (never overwrite the failing attempt);
  `--depth deep` skeptic verdicts land at `review-skeptic-{N}.md`.
