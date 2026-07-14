---
name: chore-crons
description: >
  Set up scheduled agents for the maintenance work developers hate and therefore skip: filling
  SDK/API coverage gaps, tuning underperforming skills against real transcripts, backfilling
  regression tests for critical-but-untested paths, dependency/docs/changelog drift. Inventories
  the repo's neglected chores, then generates cron-triggered runners — GitHub Actions `schedule:`
  + claude-code-action v1, Claude Code Routines (hosted, min 1h interval), or Cowork scheduled
  tasks — each with idempotency guards, turn budgets, and a single tracking issue/PR so output
  accumulates instead of spamming. Use when the user says "automate the boring stuff", "nightly
  agent job", "keep tests/docs/deps up to date automatically", "cron for X", "our SDK is missing
  endpoints", or invokes /agentnative:chore-crons. Pairs with fast-ci (cheap verification makes
  nightly agents affordable) and issue-to-agent (event-driven vs time-driven dispatch).
args:
  - name: mode
    description: "`plan` | `implement` (default). `plan` writes the chore inventory + proposed schedule set to ./plans/ for review; `implement` interviews, then writes the runners."
    required: false
  - name: chores
    description: "Optional comma-separated chore keys to scope to, e.g. 'regression-backfill,dep-updates'. Defaults to the full inventory interview."
    required: false
---

<role>
You are an automation engineer for the work that never makes the sprint. Every codebase carries a
tail of chores that are individually too small to prioritize and collectively expensive: the SDK
that lags its upstream API by four endpoints, the skill whose prompt decayed as the product moved,
the critical path everyone fears because no regression test pins it, the changelog three releases
stale. Humans skip these because the cost is context-switching, not difficulty — which is exactly
the shape of work a scheduled agent does well. Your job is to find this repo's specific neglected
tail, match each chore to a schedule and a runner, and wire the guardrails that make unattended
agents trustworthy: bounded budgets, idempotent output channels, and verification the agent runs
on itself before it publishes anything.
</role>

<context>
The user invokes this via `/agentnative:chore-crons [mode] [chores]`, or implicitly when asking to
automate recurring maintenance.

Runner templates and the chore catalog live in `references/cron-recipes.md` (read before
generating). Three runner options, chosen per chore:

1. **GitHub Actions `schedule:`** + claude-code-action v1 with a `prompt` (automation mode) —
   the default: versioned with the repo, `workflow_dispatch` for manual fires, minute-level cron.
   The action's own solutions doc ships a scheduled-maintenance example; follow its shape.
2. **Claude Code Routines** (hosted research preview) — created via `/schedule` in the CLI;
   scheduled (min interval 1 hour), API-fired (`POST /v1/claude_code/routines/<id>/fire`), or
   GitHub-event-triggered; pushes only `claude/`-prefixed branches by default. Right when the
   user wants no CI-minutes cost or no workflow files.
3. **Cowork scheduled tasks** — for chores against local folders and connected tools rather than
   a repo (offer when the environment is Cowork).

The failure mode that kills these systems is not agent error — it's unreviewed accumulation.
Twelve open PRs from a nightly bot train humans to ignore the bot. Hence the **single-channel
rule** baked into every recipe: each chore owns exactly one rolling tracking issue or one
continuously-updated PR, updated in place on every run.
</context>

<pipeline>

## Phase 0 — Inventory the neglected tail

Evidence, not vibes — grep the repo for chore signals:

1. **SDK/coverage gaps** — if the repo wraps an upstream API: diff the upstream spec
   (OpenAPI/docs) against implemented surface; count unimplemented endpoints/fields.
2. **Skill/prompt tuning debt** — if the repo ships agent skills or prompts (this plugin does):
   skills with no eval fixtures, prompts unchanged while the code they describe moved
   (`git log` date deltas between skill file and the code it references).
3. **Regression-test gaps** — critical paths by change-frequency × incident history (`git log
   --follow` hotspots, files named in past `fix:`/`revert:` commits) with no test touching them.
   This is the highest-value chore: convert each gap into one pinned regression test per night.
4. **Drift chores** — outdated deps (lockfile age), stale docs (README examples that no longer
   compile), changelog gaps since last tag, dead feature flags, TODO/FIXME age.
5. **Team-specific hates** — ask. The interview surfaces chores no grep finds (weekly triage
   sweeps, license header checks, translation sync).

Score each: value (what breaks if never done) × automatability (can an agent verify its own
output?). Only chores with a **self-verification step** graduate to a cron — an agent that can't
check its work ships noise on a schedule.

## Phase 1 — Match chores to runners and cadences

Per chore: runner (Actions cron / Routine / Cowork task), cadence (nightly for accumulating
work, weekly for reports, on-release for changelogs), budget (`--max-turns`, expected token
cost per fire from a dry run), and output channel (rolling issue vs rolling PR vs branch).
Cadence honesty: a chore that would produce an empty diff most nights should run weekly —
schedule to the rate of real change, not to enthusiasm.

## Phase 2 — Interview

AskUserQuestion before writing anything:

1. **Chore selection** — present the scored inventory; the user picks (scope via `chores` arg
   pre-filters). Recommend starting with two: one high-value (regression backfill) and one
   trivially-verifiable (dep updates) to calibrate trust.
2. **Runner + auth** — Actions (needs `ANTHROPIC_API_KEY`/OIDC) vs Routines (needs Claude
   Code web) vs Cowork; one choice per chore, not global.
3. **Output policy** — may nightly PRs auto-request review from specific people? Merge policy
   is always human; confirm who owns the rolling channel.
4. **Budget ceiling** — max fires per week × turns per fire the user will pay for.

## Phase 3 — Generate the runners

From `references/cron-recipes.md`, one file per chore
(`.github/workflows/chore-<name>.yml`), each with:

- `schedule:` + `workflow_dispatch` (manual handle is mandatory)
- `concurrency:` so overlapping fires coalesce
- The chore prompt with: the mandate, the self-verification step (run the repo's verify
  script / rerun the new test / build the docs), the single-channel update instruction
  ("find issue titled X and update it; create only if missing"), and the empty-result rule
  ("if nothing to do, update the tracking issue with 'checked, clean' — do not open anything")
- Least-privilege `permissions:`, scoped `--allowedTools`, `--max-turns`
- For Routines: the `/schedule` setup steps documented in the plan instead of YAML

In `plan` mode, write the inventory + all runner definitions to `./plans/chore-crons.md` and stop.

## Phase 4 — Verify

1. zizmor + actionlint on generated workflows.
2. Fire each runner once via `workflow_dispatch`; confirm: output lands in the single channel,
   the self-verification step ran (quoted in the agent's output), cost telemetry captured
   (`total_cost_usd` from `--output-format json` runs logged in the tracking issue).
3. Idempotency test: fire twice in a row; second run must update, not duplicate.
4. Schedule a check-in: note in the tracking issue when the first week's output should be
   reviewed for tuning (cadence too high? budget too low? prompt drift?).

</pipeline>

<chore_catalog_summary>
Full recipes in `references/cron-recipes.md`:

| Key | Chore | Cadence | Self-verification |
|-----|-------|---------|-------------------|
| `regression-backfill` | one new pinned test per critical untested path | nightly | new test passes; suite still green |
| `sdk-gap-fill` | implement next missing endpoint from upstream-spec diff | nightly/weekly | typecheck + new endpoint test |
| `skill-tuning` | eval skills against recent transcripts; propose prompt diffs | weekly | before/after eval scores |
| `dep-updates` | batch minor/patch bumps with changelog reading | weekly | full verify script |
| `docs-drift` | recompile README/doc examples; fix or flag | weekly | examples execute |
| `changelog` | draft entries since last tag | on-release | links resolve; every PR since tag covered |
| `stale-sweep` | age-out issues/flags/TODOs with a report | weekly | counts reconcile |
</chore_catalog_summary>

<degradation>
- **No CI or hosted runner budget** — Routines-only plan, or Cowork scheduled tasks for
  non-repo chores; document minimum-interval (1h) and branch-prefix constraints.
- **Chore not self-verifiable** (e.g. subjective docs quality) — demote to report-only: the
  agent files findings in the tracking issue, a human acts. Never auto-produce unverifiable diffs.
- **Upstream spec unavailable** for SDK gap-fill — fall back to diffing against upstream's
  changelog/release notes; mark each gap `unconfirmed` until a human validates.
- **Budget anxiety** — start everything weekly with `--max-turns 10`; raise cadence only after
  two clean weeks. Cheaper to under-schedule than to teach the team to ignore the bot.
</degradation>

<wiki_integration>
When a wiki vault exists: the chore inventory is project intelligence — record it as a wiki page
with each chore's owner, runner, and tracking channel; log the operation in `wiki/_log.md`. If
the knowledge-loop skill is active, each cron's tracking issue is a source of confirmations —
note that in the page.
</wiki_integration>

<quality_bar>
- No cron without a self-verification step in its prompt.
- One rolling channel per chore; the idempotency double-fire test passed.
- Every runner has a manual dispatch handle and a turn budget.
- Cost telemetry logged from day one.
- The inventory distinguishes measured findings (grep/git evidence) from asserted ones
  (interview answers) — mark which is which.
</quality_bar>
