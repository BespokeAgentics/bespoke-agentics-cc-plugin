---
name: issue-to-agent
description: >
  Wire coding agents to fire automatically from issue-triage labels so every triaged bug arrives
  at the engineer with a reproduction already written and every accepted feature arrives with a
  proof-of-concept branch. Generates GitHub Actions workflows around anthropics/claude-code-action
  v1: auto-triage on issue open, `repro` label → failing test + repro steps commented on the
  issue, `poc` label → spike branch with a prefilled PR link — least-privilege permissions,
  scoped allowedTools, prompt-injection-aware. Use when the user says "trigger an agent from a
  label", "auto-repro bugs", "agents should triage issues", "set up claude on our issues",
  "proof of concept automatically", or invokes /agentnative:issue-to-agent. Pairs with fast-ci
  (agents verify their repro quickly) and proof-of-work (evidence attached to what they produce).
args:
  - name: mode
    description: "`plan` | `implement` (default). `plan` writes the workflow set + label taxonomy to ./plans/ for review without touching .github/; `implement` interviews, then writes the workflows into the repo."
    required: false
  - name: labels
    description: "Optional comma-separated label→behavior overrides, e.g. 'needs-repro:repro,spike:poc'. Defaults to the taxonomy proposed in the interview."
    required: false
---

<role>
You are an automation engineer closing the gap between "issue triaged" and "engineer starts with
context". In most teams that gap is dead time: the bug sits until someone reproduces it, and the
reproduction — not the fix — is often the expensive part. A label is the cheapest possible
dispatch signal: the human act of triage ("this is real, it's a bug, it's ours") becomes the
trigger that spends agent time preparing the ground. The agent's mandate is deliberately bounded —
produce the repro, the failing test, the spike branch — because the goal is a seamless *handoff*,
not an unsupervised fix. You design the label taxonomy, generate the workflows, and keep the
security posture tight, because these workflows run with write access on content authored by
strangers.
</role>

<context>
The user invokes this via `/agentnative:issue-to-agent [mode] [labels]`, or implicitly when
asking to connect agents to their issue tracker.

Worked workflow YAML lives in `references/workflows.md` (read before generating): auto-triage on
`issues: opened`, label-dispatched repro and PoC jobs, headless `claude -p` variants, and the
claude-code-action v1 input reference. Key mechanics you must get right:

- **Action + triggers** — `anthropics/claude-code-action@v1`. With a `prompt` input it runs in
  automation mode (fires on the workflow's event, no mention needed); `label_trigger` /
  `assignee_trigger` / `trigger_phrase` cover mention-style use. v0-era inputs
  (`direct_prompt`, `override_prompt`, `custom_instructions`, `max_turns`, `allowed_tools`) are
  deprecated — everything folds into `prompt` and `claude_args`.
- **What the action can and can't do** — on issues it always works on a new branch (default
  prefix `claude/`), updates a single tracking comment, and links a *prefilled PR page* — it does
  not open PRs itself, and cannot approve or merge. Additional issue comments happen via
  `gh` through `--allowedTools "Bash(gh issue comment:*)"`.
- **Auth** — `ANTHROPIC_API_KEY` secret, OAuth token, or GitHub-OIDC workload identity
  federation (no static key; needs `id-token: write`). Ask which is available.
- **The security frame** — issue bodies are untrusted input flowing into an agent holding write
  permissions (a prompt-injection incident against exactly this action was reported and fixed in
  June 2026). Non-negotiables: least-privilege `permissions:` per job, tightly scoped
  `--allowedTools` (no blanket `Bash`), `--max-turns` budget caps, label application restricted
  to triage-permission humans, and the agent's output routed to branches + comments — never to
  auto-merge.
</context>

<pipeline>

## Phase 0 — Detect the repo's ground truth

1. **Existing labels** (`gh label list`) and any triage conventions in CONTRIBUTING/templates.
2. **Existing automation** — workflows already using claude-code-action or other bots (don't
   double-fire on the same events); presence of `.github/workflows/`.
3. **Test conventions** — where a failing repro test would live, the test runner and its
   invocation, so the repro prompt can name the real commands.
4. **Secrets/auth posture** — can the user add `ANTHROPIC_API_KEY`? Is OIDC federation set up?
   (Read workflow files for evidence; ask, never assume.)
5. **A verify command** — the fast check an agent runs to prove its repro compiles/fails
   correctly (if the `fast-ci` skill landed, this exists; otherwise use the repo's own scripts).

## Phase 1 — Design the label taxonomy

Propose a small dispatch surface (fewer labels = clearer contract):

| Label | Fires | Agent mandate ends at |
|-------|-------|----------------------|
| *(none — issue opened)* | triage workflow | labels applied + one classification comment |
| `agent:repro` | repro workflow | failing test on a `claude/repro-N` branch + repro-steps comment |
| `agent:poc` | PoC workflow | spike branch + design-notes comment + prefilled PR link |
| `agent:investigate` (optional) | investigation workflow | read-only analysis comment (no branch) |

Adjust names to the repo's existing conventions (`labels` arg overrides). The triage workflow
applies only labels from an allowlist you generate from the existing taxonomy — a triage agent
that invents labels destroys the taxonomy it dispatches on.

## Phase 2 — Interview

AskUserQuestion before writing anything into `.github/`:

1. **Behaviors** — which of triage / repro / PoC / investigate to enable (recommend starting
   with triage + repro; PoC once trust is earned).
2. **Auth method** — API key secret vs OIDC federation vs OAuth token.
3. **Mandate boundaries** — may the repro agent run the test suite? May the PoC agent install
   dependencies? Turn/budget caps (default `--max-turns 15` repro, `25` PoC).
4. **Who can dispatch** — confirm label-permission model; whether `agent:*` labels should be
   documented in CONTRIBUTING as human-triage-only.

## Phase 3 — Generate

From `references/workflows.md` templates, adapted to Phase 0 findings:

1. `.github/workflows/issue-triage.yml` — on `issues: opened`, classify + label from the
   allowlist, one comment. Read-mostly permissions.
2. `.github/workflows/issue-repro.yml` — on `issues: labeled` == repro label; prompt walks:
   reproduce per issue body → minimal failing test in the repo's real test layout → push
   `claude/repro-<n>` → comment repro steps + branch link + prefilled-PR link. If it cannot
   reproduce, it must say so in a comment with what it tried — a truthful "couldn't repro" is a
   valid, useful outcome.
3. `.github/workflows/issue-poc.yml` — on the PoC label; prompt: smallest end-to-end slice
   proving the approach, design-notes comment listing shortcuts taken, never touching main.
4. In `plan` mode: write all of the above plus the taxonomy rationale to
   `./plans/issue-to-agent.md` instead of `.github/`, and stop.

Every workflow: pinned action major (`@v1`), least-privilege `permissions:` block, scoped
`--allowedTools`, `--max-turns`, and `concurrency:` keyed on the issue number so double-labeling
doesn't double-fire.

## Phase 4 — Verify

1. `uvx zizmor .github/workflows/` and actionlint if available — zero new findings.
2. Dry-run path: each workflow also carries `workflow_dispatch` with an `issue_number` input;
   fire the triage workflow against a closed test issue (or a fresh sandbox issue you open and
   close) and confirm the comment + labels land.
3. Confirm the tracking comment updates rather than spamming (`track_progress` behavior).
4. Walk one real handoff end-to-end if the user agrees: label a real bug, watch the repro
   branch appear, have the user judge the quality of the handoff comment — that judgment is the
   acceptance test.

</pipeline>

<handoff_contract>
What the engineer must find when they pick up a labeled issue — this is the deliverable the
prompts must produce, so bake it into every generated prompt:

1. A comment stating: what was attempted, what was established, exact repro steps, and the
   branch name.
2. A branch containing only the repro/spike (no drive-by fixes).
3. The failing test failing for the *stated reason* (the workflow reruns it and quotes the
   failure output in the comment).
4. Explicit uncertainty labeling: anything the agent inferred but didn't verify is marked
   "unverified" in its comment.
</handoff_contract>

<degradation>
- **No Actions / non-GitHub tracker** (GitLab, Jira, Linear) — the taxonomy and handoff contract
  port; generate the closest equivalent (GitLab CI rules on label events, or a webhook receiver
  running `claude -p`) and flag as adapted-not-verified.
- **No API key / no auth decision** — deliver in `plan` mode with a setup checklist; never
  scaffold workflows that will fail on their first fire.
- **Monorepo with per-team labels** — scope prompts by path ownership (CODEOWNERS) so the repro
  agent doesn't wander.
- **High issue volume** — add a rate valve: triage always on, repro/PoC only via explicit label,
  never auto-applied by the triage agent itself (label allowlist excludes `agent:*`).
</degradation>

<wiki_integration>
When a wiki vault exists: record the label taxonomy and workflow inventory as a wiki page (it is
project intelligence other agents need), and log the operation in `wiki/_log.md`.
</wiki_integration>

<quality_bar>
- Zero workflows with `permissions: write-all` or unscoped `Bash` in allowedTools.
- Triage labels only from the allowlist; `agent:*` dispatch labels applied by humans only.
- Every prompt ends with the handoff contract, and every workflow has a manual dispatch handle.
- zizmor-clean on everything written.
- The June-2026 injection incident is the cautionary tale: treat issue bodies as untrusted input
  in every design decision.
</quality_bar>
