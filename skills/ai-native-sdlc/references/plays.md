# The play catalog

Sixteen plays across six stages. Each entry: what changes, prerequisites (the adoption dependency
graph — a play is only scaffolded after everything it lists), assessment probes (what `assess`
looks for and how it scores), scaffold output (what `adopt` writes; sources in `templates.md` /
`scaffolds.md`), and the measure of success.

**Clay plays** — no prerequisites, start anywhere: `P1`, `B3`.

Dependency graph, flattened into a safe adoption order:

```
B3 claude-md  ──►  T1 feedback-loop ──►  B2 auto-mode
   │          ──►  B4 skills ──► B5 hooks-guardrails ──► D2 approval-gates ──► D3 cicd
P1 intent ──► P2 spec ──► B1 plan-mode ──► B6 parallel        T2 evals ─────► M1 close-loop
                              └──────────► D1 pr-review ──► M2 scans          M3 on-call
```

(`T2` needs `B3`+`B4`/`B5` to exist — they are the configuration it regression-tests — plus CI.
`M1` needs `D3` + `T2` + `P1`. `M3` needs `D3` and is mostly platform setup outside the repo.)

**Scoring rule for mixed-visibility plays**: several plays combine repo-visible probes with
"⚪ + ask" sub-probes (branch protection, hosted-service connections, session habits). Score the
play on its repo-visible evidence and carry each unverifiable sub-probe as a caveat in the
evidence column — one score cell per play, never a blended or guessed score. Note that a 🟡 can
rest on prose alone: `B4` is 🟡 when a policy lives only in `CLAUDE.md` prose even with zero
`.claude/skills/` — the knowledge exists, its operational form doesn't.

---

## Stage 1 — Plan

### P1 · capture-intent

- **What changes**: ideas, tickets, and incident findings all enter as a committed `intent.md` —
  human-readable, version-controlled, immediately consumable by the next stage. The originator
  brainstorms with Claude; the product owner reviews and accepts.
- **Prerequisites**: none (clay). Needs a decision on the intent home and who may write to it.
- **Probes**: an `sdlc/`, `intents/`, or configured home containing `intent.md` files; an intent
  template in `.claude/skills/` or docs. 🟡 if ad-hoc intent-like docs exist without a home or
  template.
- **Scaffold**: the intent home directory with a `README.md` stating the acceptance rule (who
  accepts, what acceptance means — the merge or closing review IS the recorded decision), and the
  `intent.md` template (templates.md §1).
- **Measure**: share of work items whose origin is a committed `intent.md` with a recorded acceptor.

### P2 · requirements-and-design

- **What changes**: Claude drafts `spec.md` from the accepted `intent.md` with the organization's
  skills applied as constraints; the product owner reviews rather than writes. Concerns —
  especially contradicting policies — are flagged in the spec, not discovered weeks later.
- **Prerequisites**: P1. B4 makes it much stronger (skills are the constraints).
- **Probes**: `spec.md` files paired with intents; a spec template; a slash command or CI job that
  produces specs on intent acceptance. 🟡 for specs without flagged-concerns sections.
- **Scaffold**: `spec.md` template (templates.md §2) and, where the CI play is adopted, a note in
  the pipeline scaffold for the intent-merge → spec-draft trigger.
- **Measure**: specs reviewed (not written) by the product owner; concerns resolved before
  engineering sees the spec.

---

## Stage 2/3 — Build

### B1 · plan-mode-default

- **What changes**: engineers start sessions in plan mode, feed in `intent.md` + `spec.md`, and
  iterate until the plan names the files that change, the order, and the tests that prove it.
  The accepted plan is committed as `plan.md`; the eventual diff is checked against it (D1).
- **Prerequisites**: P2 (a spec to plan against); works degraded without it.
- **Probes**: committed `plan.md` files; a plan template; `CLAUDE.md` guidance to start in plan
  mode. ⚪ for the habit itself — session behavior isn't inspectable from the repo.
- **Scaffold**: `plan.md` template (templates.md §3) plus a `CLAUDE.md` section stating the
  plan-first convention and the sync rule (implementation departs → update `plan.md` in the same
  commit).
- **Measure**: an engineer who never saw the conversation could implement from `plan.md` alone.

### B2 · auto-mode

- **What changes**: with guardrails mature, auto-accept becomes the default for routine work —
  tight spec, small blast radius, code the tests already cover. Attention moves from watching
  edits to reviewing artifacts after longer autonomous sessions.
- **Prerequisites**: B3, B5, T1 — auto-mode without a tuned CLAUDE.md, hooks, and a feedback loop
  is just unsupervised risk.
- **Probes**: prerequisites' scores are the probe; B2 is 🔴 unless B3+B5+T1 are 🟢, then ⚪
  (a habit, not a file).
- **Scaffold**: nothing to write beyond a `CLAUDE.md` note on when auto-accept is sanctioned.
- **Measure**: routine-work sessions complete without per-edit prompts AND without gate failures.

### B3 · claude-md

- **What changes**: the context a new joiner needs — commands, conventions, architecture, the
  mistakes the team sees most — lives in a version-controlled `CLAUDE.md` the agent reads every
  session. Working rule: a mistake made twice goes in the file.
- **Prerequisites**: none (clay).
- **Probes**: `CLAUDE.md` at root. 🟢 needs build/test/lint commands AND conventions AND it stays
  near a page; 🟡 if it exists but misses commands or has clearly gone stale/bloated.
- **Scaffold**: generate or additively extend `CLAUDE.md` with the repo's real commands (Phase 0),
  a conventions section, and the "things Claude gets wrong" section seeded from the interview.
- **Measure**: corrections stop repeating; the file stays under roughly a page.

### B4 · skills-as-knowledge

- **What changes**: institutional knowledge that must be applied consistently (security standard,
  API convention, brand rule) becomes a versioned skill; policy changes are one central edit.
  Rule of thumb: skills for policy applied consistently; `CLAUDE.md` for repo context.
- **Prerequisites**: B3.
- **Probes**: `.claude/skills/*/SKILL.md` or plugin-distributed skills. 🟡 for policy living only
  in `CLAUDE.md` prose or wiki pages.
- **Scaffold**: ONE seed skill for the policy the interview names as most inconsistently enforced
  today, written from the policy owner's source of truth (templates.md §6 shows the shape). Test
  that it triggers by phrasing the task three different ways.
- **Measure**: the policy is applied without anyone pasting it into prompts; violations become rare.

### B5 · hooks-guardrails

- **What changes**: the deterministic layer behind skills. Build-phase hooks block edits to
  protected paths, keep credentials out of the diff, run the formatter after edits. Fast, scoped
  to the file that changed; heavy checks stay at commit/PR.
- **Prerequisites**: B4 (a skill worth backing) — or a protected path worth guarding.
- **Probes**: `.claude/settings.json` `PreToolUse`/`PostToolUse` hooks; `.claude/hooks/*`. 🟡 for
  hooks that only format (no protection).
- **Scaffold**: protected-paths hook + optional secrets guard (scaffolds.md §1–2), wired
  additively into `.claude/settings.json`, each verified against allow AND block fixtures.
- **Measure**: violations of the backed policy become impossible, not just rare.

### B6 · parallel-sessions-and-subagents

- **What changes**: one engineer drives several streams — parallel sessions in separate worktrees
  for independent tasks, subagents for recurring in-session jobs (verifier, researcher,
  simplifier). Ceiling = what one person can review properly.
- **Prerequisites**: B1 (the plan shows where work is independent), B5 (repo-level controls apply
  to every session).
- **Probes**: `.claude/agents/*.md` definitions. Worktree habits are ⚪.
- **Scaffold**: the verifier subagent (templates.md §5) adapted to the repo's run command, plus
  any recurring job the interview surfaces.
- **Measure**: streams in flight rise while review keeps up.

---

## Stage 4 — Test

### T1 · feedback-loop

- **What changes**: Claude can verify its own work — a single non-zero-on-failure target, listed
  in `CLAUDE.md` with healthy-output examples, and verification is part of "done". Bug fixes are
  failing-test-first; the loop is protected (the agent fixing code cannot weaken the check).
- **Prerequisites**: B3 (the commands live there).
- **Probes**: a verification block in `CLAUDE.md` (templates.md §4 shape); a single wrapped test
  target. 🟡 if the commands are listed **in `CLAUDE.md`** but the "run before reporting done"
  rule is absent; commands existing only in `package.json`/Makefile is 🔴 — the play's control is
  the block the agent reads, not the repo's ability to run tests.
- **Scaffold**: the verification block with the repo's real commands; where B5 is adopted, the
  test-file-protection hook (scaffolds.md §3) that blocks test edits during fix tasks.
- **Measure**: sessions fix their own mistakes before an engineer sees them.

### T2 · continuous-evals

- **What changes**: 20–50 real tasks with acceptance checks run in CI on a schedule AND on any
  change to `CLAUDE.md`/`.claude/**` — the configuration that steers the agent gets the
  regression testing code gets. Every production incident adds an eval.
- **Prerequisites**: B3/B4/B5 (something to regression-test), D3-adjacent CI plumbing.
- **Probes**: `evals/` with cases; a workflow triggered on `CLAUDE.md`/`.claude/**` paths.
- **Scaffold**: `evals/` skeleton with 2–3 seed cases drawn from recent git history, the check
  script contract, and the agent-evals workflow (scaffolds.md §4).
- **Measure**: a config change that drops the pass rate gets caught before merge.

---

## Stage 5 — Deploy

### D1 · pr-review-loop

- **What changes**: Claude reviews incoming PRs against `REVIEW.md` (bugs / security / compliance
  with `spec.md` + `plan.md`), addresses `@claude` comments on its own PRs, and findings feed back
  into `CLAUDE.md` on second occurrence. Humans judge intent and risk; branch protection still
  requires a code-owner approval — the agent that wrote the code cannot approve it.
- **Prerequisites**: P2 + B1 (the artifacts compliance is checked against); CI or the managed
  Code Review service.
- **Probes**: `REVIEW.md` at root; claude-code-action review workflow or managed-service evidence.
  🟡 for AI review without a written policy (uncalibrated nits).
- **Scaffold**: `REVIEW.md` (templates.md §7) with passes, the Important-vs-Nit line, nit cap, and
  exclusions — calibrated to the repo in the interview.
- **Measure**: human review time concentrates on behavior/intent; repeat findings stop repeating.

### D2 · approval-gates

- **What changes**: hooks that ASK — pausing an action until a named person approves. Release
  authorization is the clearest case; also change-management sign-off and protected-path edits.
  Non-negotiable gates live in managed settings engineers cannot switch off.
- **Prerequisites**: B5 (hooks infrastructure).
- **Probes**: gate-shaped hooks (deploy/production matchers, approval env checks). 🟡 for gates in
  team settings when the org needs managed settings.
- **Scaffold**: the production-gate hook matched to the repo's REAL deploy commands (scaffolds.md
  §5) with the named release owner, wired and block-path-tested.
- **Measure**: every allow/block is logged; no production-shaped action proceeds without the named
  approval.

### D3 · cicd-integration

- **What changes**: `claude -p` runs non-interactively in the pipeline — read-only judgment first
  (triage failed builds, summarize flaky tests), then write steps behind existing gates (lint
  fixes, doc updates arrive as PRs; no route to main). Sandboxed, short-lived tokens, deployment
  exposed as scoped MCP tools, autonomy tiered by environment, rollback rehearsed.
- **Prerequisites**: D1, D2.
- **Probes**: workflows invoking `claude -p` / claude-code-action beyond review; branch-protection
  evidence via `gh` when available (else ⚪).
- **Scaffold**: a read-only triage step in the existing pipeline (scaffolds.md §6) — the safe
  first move; write steps and MCP deployment are documented as next steps, not scaffolded blind.
- **Measure**: the agent acts up to the production gate and cannot pass it.

---

## Stage 6 — Maintain

### M1 · closing-the-loop

- **What changes**: a deterministic, version-controlled watch script monitors one metric with
  rolling bands; 1σ logs, 2σ invokes Claude read-only to diagnose, 3σ lets it propose — a PR into
  the review gate or a pre-approved runbook, never direct action. The diagnosis is written as
  `intent.md`, and the loop feeds itself. Detection never involves the model.
- **Prerequisites**: D3, T2, P1.
- **Probes**: `bands.yaml`-shaped config; a scheduled watch workflow; unit tests on the detector.
- **Scaffold**: `bands.yaml` for the interview-chosen metric + the detection-script contract and
  trigger workflow skeleton (scaffolds.md §7). The script itself is real code the team owns —
  scaffold it with tests or not at all.
- **Measure**: a breach becomes a triaged `intent.md` without anyone starting the loop; dismissals
  tune the bands.

### M2 · recurring-scans

- **What changes**: security scanning runs on a schedule with no human in the invocation path
  (Claude Security hosted, or scheduled scan jobs); findings carry confidence ratings, dismissals
  carry reasons, bounded patches go through the PR gate, wider findings become `intent.md`.
- **Prerequisites**: D1 (findings need the review gate).
- **Probes**: scheduled scan workflows; Claude Security connection isn't repo-visible (⚪ + ask).
- **Scaffold**: mostly platform setup — document the connection steps and the triage rule
  (dismiss-with-reason; fixed vulnerability class → T2 eval) in the adoption report.
- **Measure**: scan history reads as an audit record: found, fixed, consciously accepted.

### M3 · on-call-with-tag

- **What changes**: Claude Tag joins incident channels under its own identity — first responder,
  channel history as the audit trail, post-mortems written to a version-controlled lessons file.
  Bounded fixes arrive as PRs; larger work becomes `intent.md`.
- **Prerequisites**: D3 (the PR route), M1 patterns. Platform setup outside the repo.
- **Probes**: a lessons/post-mortem file convention. Tag membership is ⚪ + ask.
- **Scaffold**: the lessons file home + entry template; the rest is documented setup steps.
- **Measure**: incidents get a first responder immediately; lessons accumulate where future
  investigations read them.
