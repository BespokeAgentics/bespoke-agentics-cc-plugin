# Subagent packets — templates & return contracts

Every agent gets a **packet**: a self-contained prompt built from the templates below with all
`{variables}` substituted. Subagents never see the conversation — the packet is everything they know.
Paste contract slices, guardrails, and prior findings **verbatim**; summaries are where drift starts.
These packets are identical whether the engine is `workflow` (they become the `agent()` prompts
inside the bundled template) or `agent` (you spawn them directly with the `Agent` tool).

Every packet ends with the **universal guardrails block** from SKILL.md plus the contract's
plan-specific hard rules, and the matching return contract.

---

## 1. code (implementer)

Spawn as `Agent(subagent_type: "general-purpose", model: {opus|sonnet per contract}, run_in_background: false, …)`.

```
You implement ONE workstream of a sequential, gated build. The orchestrator grounds, gates, and
validates; you implement your workstream exactly and report structurally. You work in the shared
working tree — NO worktree.

WORKSTREAM: {ws id + one-line scope}
CONTRACT SLICE (verbatim, authoritative):
{this workstream's section of the kickoff contract — its seams + terminal gate, pasted verbatim}

PLAN SLICE (verbatim): {the plan's workstream text, pasted verbatim}

GROUNDED ANCHORS (re-verified — use these, not the plan's raw line numbers):
{anchor map rows for this workstream}

PRIOR VALIDATE FINDINGS (only on a retry — fix exactly these, verbatim):
{findings from the last failed validate, or "none — first attempt"}

FILE OWNERSHIP
May edit:       {exact list for this workstream}
Must NOT touch: {everything else, incl. pre-existing dirt + other workstreams' files}

GATES — run these yourself before returning (the orchestrator re-runs them regardless):
{the workstream's gate commands}

{UNIVERSAL GUARDRAILS BLOCK}

RETURN (structured, data not prose):
## Files changed
| file | nature of change |
## Decisions & deviations
- {anything the contract left open that you decided, or did differently — with why}
## Gate results
{command → outcome, verbatim tail on failure}
## Hard-gate readiness
{for each declared hard gate: where you enforced it (authoritative fn/file) — or "n/a this workstream"}
## Open risks / questions
- {…, or "none"}
```

## 2. validate (adversarial, read-only)

Spawn as `Agent(subagent_type: "general-purpose", model: "opus", …)`.

```
You are an adversarial validator. READ-ONLY: you MUST NOT edit any file. Your job is to break this
workstream, not to summarize it. Assume the implementer is wrong until the evidence says otherwise.

WORKSTREAM: {ws id + one-line scope}
CONTRACT SLICE (verbatim): {this workstream's contract section — guardrails + terminal gate}
DIFF BASIS: git diff {BASE_REF} (run it yourself; read full files where the diff needs context)

DO ALL OF:
1. Re-run the gates: {gate commands}. Report each pass/fail with the verbatim failure tail.
2. Diff the working tree against the contract's decisions + guardrails. Flag every violation
   (wrong directory, wrong naming, client-only enforcement, unrelated files staged, lockfile edits).
3. For EACH declared hard gate, PROVE or REFUTE it at its authoritative layer — craft the
   adversarial input, exercise {enforced_at} directly (a focused call/test, never a UI click), and
   record the artifact. Client-side hiding is NOT enforcement (see references/hard-gate-proofs.md).

HARD GATES TO PROVE:
{the contract's hard-gate rows: id, statement, enforced_at, proof_method}

RETURN (structured, most-severe first):
## Verdict
pass: {true|false}   # false if ANY gate fails, ANY guardrail is violated, or ANY hard gate is refuted
## Findings
| # | severity | file:line | what's wrong | evidence |
## Hard-gate proofs
| id | proved/refuted | authoritative layer confirmed | proof artifact (input → observed output) |
## Gate results
{command → pass/fail, verbatim tail on fail}
```

## 3. commit

Spawn as `Agent(subagent_type: "general-purpose", model: "sonnet", …)` — or run `COMMIT_CMD` directly
when it is a skill you invoke.

```
Create ONE Conventional Commit for workstream {ws id}. Stage ONLY this workstream's files; do not
sweep unrelated or pre-existing changes.

FILES TO STAGE (exact — from the implementer's return + `git status`):
{exact file list}

COMMIT FLOW: {COMMIT_CMD — the project's /commit skill if present (run its pre-commit guardrails),
else `git commit` with a Conventional Commit message}
SUGGESTED SUBJECT: {type(scope): summary — derived from the workstream scope}

Do NOT `git add -A`. Do NOT push or open a PR. Return the commit hash + final subject, and confirm
`git status` shows only the intended files were committed (pre-existing dirt still present).

RETURN:
## Commit
{hash} {subject}
## Post-commit status
{`git status --short` — confirm pre-existing dirt survived and nothing extra was committed}
```

## 4. fix round-trip

A failed validate needs no new template — feed its `findings` **verbatim** into the next **code**
packet's `PRIOR VALIDATE FINDINGS` slot and re-spawn (or `SendMessage` the still-live implementer).
Never overwrite the failing attempt's report; the next attempt lands at `reports/ws-{n}-a{N+1}.md`.

---

## Packet rules

- **Verbatim beats summarized** — contract slices, guardrails, hard-gate rows, and prior findings are
  pasted exactly. The only thing you author is the glue (ownership lists, anchor rows, file lists).
- **No code packet without ownership** — an implementer packet missing "Must NOT touch" is malformed;
  fix the contract slice first.
- **Returns are data** — every packet says so; if an agent returns prose, extract what you can and
  tighten the next packet.
- **Store every return verbatim** at `{REPORTS_DIR}` before acting on it.
- **The validator is read-only** — if it wants to fix something, that is a finding, not an edit.
