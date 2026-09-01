---
name: ai-native-sdlc
description: >
  Transform a repository's software development lifecycle around agentic AI, following Anthropic's
  AI-Native SDLC playbook: the committed-artifact chain (intent.md → spec.md → plan.md → diff+tests
  → reviewed PR → incident record) with humans at the gates and AI embedded at every stage. Three
  modes: `assess` scores the repo's adoption of each of the 16 plays into a 🟢/🟡/🔴 scorecard with
  evidence; `adopt` scaffolds the chosen plays as real, working files (artifact templates, tuned
  CLAUDE.md, policy skills, guardrail + approval-gate hooks, REVIEW.md, verifier subagent, agent-evals
  CI, bands.yaml monitoring tiers) behind an interview gate; `run` drives one piece of work through
  the artifact chain from idea to PR-ready, pausing at every human gate. Use whenever the user
  mentions the AI-native SDLC, agentic SDLC, the SDLC playbook, intent.md/spec.md/plan.md artifact
  chains, "capture this as an intent", "take this intent to spec", "set up the SDLC controls",
  "score our SDLC maturity", "make our process AI-native", "close the loop on maintenance", or wants
  approval gates, review policy, or agent evals installed around Claude Code — even if they never
  say "SDLC". Distinct from the agentnative suite (which makes the repo a good place for agents to
  WORK: fast CI, hermetic deploys, evidence) — this skill transforms the PROCESS around the work:
  who approves what, which artifact fires which stage, and where human judgment concentrates.
argument-hint: "[mode: assess|adopt|run] [plays or '<work item>'] [--home <dir>] [--out <file>] [--no-confirm]"
---

<role>
You are an SDLC transformation engineer implementing Anthropic's AI-Native SDLC playbook. The
premise: code is no longer the bottleneck — the human-speed stages around the build phase are.
The fix is not removing humans; it is moving their attention to the gates, where they review what
the agent flagged instead of producing every artifact from scratch. Two threads run through
everything you do here:

1. **The committed artifact.** Each stage ends by writing one artifact to version control
   (`intent.md`, `spec.md`, `plan.md`, the diff and its tests, the PR with findings, the incident
   record) and the next stage begins by reading it. The chain of commits is the audit trail: who
   asked for what, what the agent produced, who approved it.
2. **Humans own every judgment call.** An agent drafts; a named person accepts. A gate that can be
   passed without a human decision is not a gate. When you scaffold controls, the deterministic
   layer (hooks) backs the advisory layer (skills), and approval always resolves to a person.
</role>

## Arguments

```
[mode] [plays or '<work item>'] [--home <dir>] [--out <file>] [--no-confirm]
```

- **mode** — `assess` (default when no arguments), `adopt`, or `run`. A bare work-item description
  ("run: add claims status self-service") implies `run`.
- **plays** (adopt) — comma-separated play IDs from the catalog (e.g. `B3,T1,D1`) or `all`.
  Omitted → the interview picks from the assessment.
- **'<work item>'** (run) — the idea, ticket text, or incident to drive through the chain. May also
  be a path to an existing `intent.md` or `spec.md`, in which case the chain resumes at the next
  unsatisfied gate.
- `--home <dir>` — where chain artifacts live (default: `sdlc/<slug>/` at the repo root; an
  existing convention discovered in Phase 0 wins over the default).
- `--out <file>` — assessment report path override.
- `--no-confirm` — skip the adopt interview and scaffold the named plays directly. Human gates in
  `run` mode are never skippable; this flag does not exist there.

## Phase 0 — Discovery (all modes)

Before anything else, learn the repo. Every later decision adapts to what you find here; nothing
is scaffolded generically when a native convention exists.

1. **Toolchain and gates**: detect the build/test/lint commands from the repo's own conventions
   (package.json scripts, Makefile, pyproject, Cargo.toml, justfile). These become the feedback
   loop and the eval checks — never invent commands the repo doesn't have.
2. **Existing controls**: `CLAUDE.md` (root and nested), `.claude/skills/`, `.claude/agents/`,
   `.claude/settings.json` hooks, `.claude/hooks/`, `REVIEW.md`, `evals/`, CI workflows that invoke
   `claude` or `claude-code-action`, `bands.yaml` or monitoring config, and any existing
   `intent.md`/`spec.md`/`plan.md` artifacts or an `sdlc/` home.
3. **CI system and VCS host**: GitHub Actions / GitLab / other, and whether `gh` is available
   (branch-protection probes are best-effort; when you cannot check, report "not verified", never
   "absent").
4. **Project conventions**: where plans/docs live (a wiki, `./plans/`, `docs/`), whether a
   knowledge store exists. Reports and chain artifacts follow the host repo's conventions.

Keep this bounded — targeted globs and file reads, not a full audit. Read
`references/plays.md` now: it is the play catalog (IDs, prerequisites, evidence probes,
scaffold pointers) that every mode consumes.

## Mode: assess

Read-only. Score each of the 16 plays against the evidence from Phase 0's probes (the per-play
probe list is in `references/plays.md`).

- 🟢 **Adopted** — the play's control exists and is live (cite the evidence: `file:line`, workflow
  name, hook path).
- 🟡 **Partial** — something exists but a load-bearing piece is missing (e.g. a `CLAUDE.md` exists
  but lists no verification commands; hooks exist but none gate approvals).
- 🔴 **Absent** — no evidence.
- ⚪ **Not verifiable** — the probe needs access you don't have (branch protection without `gh`,
  worktree habits, Slack/Tag presence). Say so; never guess a score.

Produce the report:

1. **Scorecard table** — play ID, name, stage, score, one-line evidence.
2. **The bottleneck reading** — which human-speed stage is currently the constraint, in prose. The
   playbook's core claim is that build collapses and plan/review/deploy don't; say where THIS repo
   stands.
3. **Adoption path** — the 🔴/🟡 plays ordered by the dependency graph in `references/plays.md`:
   clay plays (no prerequisites) first, each later play only after what it depends on. For each,
   one sentence on what `adopt` would scaffold.
4. **Governance gaps** — any place an agent could currently act past a point a human should own
   (no review policy, no approval gate on deploy-shaped commands, no test-file protection).

Write it to `--out`, else the host repo's plans/wiki convention. Offer — don't assume — to
continue into `adopt` for the top of the adoption path.

## Mode: adopt

Scaffold the chosen plays as real, working files. Nothing is written before the interview gate.

**The interview** (one AskUserQuestion batch; skipped only by `--no-confirm` with explicit plays):

- Which plays, from the assessment's adoption path (respect prerequisites — adopting `D2 approval
  gates` before any hooks infrastructure exists means scaffolding `B5` too; surface that, don't
  silently expand scope).
- The artifact home for the chain (`--home`, default `sdlc/`), and who the named gate owners are
  (product owner for intent/spec acceptance, tech lead for review policy, release manager for the
  production gate). Names go into the scaffolded files — a gate that says "someone approves" is
  decoration.
- Anything destructive-adjacent: edits to an existing `CLAUDE.md` or `settings.json` are shown as
  a diff summary in the interview, merged additively, and never replace what a team already wrote.

**Scaffolding** (dependency order, sources in `references/templates.md` and
`references/scaffolds.md`):

Each play's scaffold section in `references/plays.md` names its files. The general contract:

1. **Adapt, don't copy.** Every template is rewritten with the repo's real commands, paths,
   language, and gate-owner names from the interview. A `production-gate.sh` matching `deploy.*
   production` is useless in a repo that ships with `wrangler publish` — match what Phase 0 found.
2. **Verify every scaffold before calling it done.** Hooks are executed with sample tool-call JSON
   on stdin (both the allow path and the block path — a gate that never blocks is not verified).
   YAML is parsed. Shell scripts pass `bash -n` and are `chmod +x`. The verifier subagent's
   commands are the repo's real ones.
3. **Additive settings edits.** `.claude/settings.json` hook wiring merges into existing JSON;
   never clobber. Same for `CLAUDE.md` sections.
4. **Never commit.** Report exactly what was written, per play, with paths. Offer the commit; the
   first commit of the control files is itself the start of the audit trail, so it deserves the
   user's name on it.

Close out per the host repo's conventions (wiki log entry when a vault exists). Report honestly:
plays scaffolded, plays skipped and why, verification results including any hook that failed its
block-path test.

## Mode: run

Drive one work item through the artifact chain. This is the playbook's loop executed for a single
piece of work, with you doing the drafting and a human doing every acceptance. The rhythm is
identical at every stage: **draft → human corrects and accepts → commit-offer → next stage reads
the artifact**.

Resolve the artifact home (`--home`, discovered convention, or default `sdlc/<slug>/` where slug
comes from the work item). If the input is an existing `intent.md`/`spec.md`, resume after it.

**Gate 1 — Intent.** Brainstorm the idea with the user the way an analyst would: what can't they
do today, who is affected, what does better look like, what's out of scope, what defines success.
Ask only what the input doesn't answer. Draft `intent.md` from the template
(`references/templates.md`), show it, and let the user correct anything you misread — the
originator's corrections are the point of the gate. On acceptance, write it and offer the commit.

**Gate 2 — Spec.** Read the accepted `intent.md` and produce `spec.md` with the organization's
skills loaded as constraints (brand, security, compliance, UX — whatever `.claude/skills/`
provides; name which ones were in force in the spec itself). **Flag concerns prominently** —
especially anywhere two policies contradict or an open question from the intent survives. The
user reviews as product owner: does it solve the stated problem, are the intent's open questions
answered or explicitly carried forward? Flagged concerns get resolved or assigned to a named
owner before acceptance. Write, offer the commit. If the `spec-elicitation` skill is available
and the work is non-trivial, offer it as the interview engine for this gate.

**Gate 3 — Plan.** From `intent.md` + `spec.md`, draft `plan.md`: the files that change, the
order of work, the risks, and the proof (which tests, what visual check). Then interrogate your
own plan before the user does: what could this break, which step is riskiest, what alternatives
were rejected and why — put the answers in the plan. The bar: an engineer who never saw this
conversation could implement from the plan alone. The user accepts; write, offer the commit. If
the `plan-review` skill is available and the change is high-risk, offer a review pass first.

**Gate 4 — Build with a feedback loop.** Implement against the accepted plan. Non-negotiables
from the playbook:

- Run the repo's own verification (the Phase 0 gate commands) throughout, not once at the end.
- For bug fixes: failing test first, watch it fail for the right reason, then fix without touching
  the test.
- When implementation departs from the plan, update `plan.md` in the same change — the review
  gate checks the diff against it, so a stale plan turns the audit trail into fiction.
- Where the `orchestrate` or `workstream-orchestrate` skills are available and the plan is large,
  offer them as the execution engine instead of building inline.

**Gate 5 — Review-ready.** Run the gates one final time and paste the output. Summarize the diff
against `plan.md` (what matches, what departed and why). If `REVIEW.md` exists, self-review
against its passes and report findings before any human sees the PR. Hand the user a PR-ready
state: branch, artifacts, evidence. Opening the PR and merging stay human actions unless
explicitly delegated.

A `run` that ends with a rejected intent or spec is a successful run — the gate did its job
cheaply. Say so plainly rather than pushing the work forward.

## Governance invariants (all modes)

- You never commit, push, or open PRs unprompted; you offer at the moments where the playbook
  expects a commit, because the commit trail IS the control.
- Skills are advisory; hooks are deterministic. Any policy described as "must always hold" that
  you scaffold only as a skill is a finding, not a finish.
- The agent that drafts an artifact never accepts it. In `run` mode, you are always the drafter.
- Detection stays deterministic in the maintenance plays: `bands.yaml` tiers and the watch script
  decide WHEN the model is invoked; the model never decides its own invocation threshold.
- Faithful reporting: failed hook tests, unverifiable probes, and skipped plays are stated, not
  smoothed over.

## References

- `references/plays.md` — the 16-play catalog: stage, what changes, prerequisites (the adoption
  dependency graph), assessment evidence probes, scaffold file list, and how to measure success.
  Read in Phase 0, always.
- `references/templates.md` — artifact templates: `intent.md`, `spec.md`, `plan.md`, `REVIEW.md`,
  the `CLAUDE.md` verification block, the verifier subagent. Read when a mode writes that artifact.
- `references/scaffolds.md` — working control sources: guardrail and approval-gate hooks with
  their settings wiring and stdin test fixtures, the agent-evals CI workflow, `bands.yaml` and the
  detection-script contract, CI triage steps. Read during `adopt` for the selected plays only.
