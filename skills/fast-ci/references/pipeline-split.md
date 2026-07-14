# LN* — Lane Architecture: fast pre-merge, heavy post-merge

The principle: the pre-merge gate exists to make merging safe, not to prove everything. Checks an
agent reruns on every iteration must be near-instant; checks that need real services, browsers, or
minutes of wall-clock belong where they don't block iteration. Three lanes:

| Lane | Trigger | Contents | Blocking? | Budget |
|------|---------|----------|-----------|--------|
| **Fast** | `pull_request` + `merge_group` | typecheck (TS7), lint (oxlint), format-check (oxfmt), unit tests, affected-only builds | Yes — required checks | < 3 min |
| **Queue** (optional) | `merge_group` only | integration tests that *must* gate merges | Yes, but batched off the PR loop | < 10 min |
| **Post-merge** | `push: main` (or nightly) | full integration, E2E, browser suites, load smoke | No — alerts, not gates | whatever it takes |

## LN1 — Fast lane must answer both `pull_request` and `merge_group`

A merge queue creates a speculative merge commit and runs checks against it; required checks that
never report a status on `merge_group` **stall the queue silently**. Every required workflow needs
both triggers:

```yaml
# .github/workflows/fast.yml
name: fast
on:
  pull_request:
  merge_group:
jobs:
  verify:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5
      - uses: oven-sh/setup-bun@v2          # or setup-node + pnpm
      - run: bun install --frozen-lockfile
      - run: npx tsc --build --noEmit       # TypeScript 7 native
      - run: npx oxlint
      - run: npx oxfmt --check
      - run: bun test
```

Monorepos: front the steps with `npx turbo run typecheck lint test` (remote cache on) or
`nx affected` so unchanged packages are cache hits.

## LN2 — Integration lane moves to `merge_group` or `push: main`

```yaml
# .github/workflows/integration.yml
name: integration
on:
  merge_group: {}          # variant A: gates the queue, off the PR loop
  # push:                  # variant B: post-merge only
  #   branches: [main]
  workflow_dispatch: {}    # always keep a manual handle for verification
jobs:
  integration:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5
      # spin the hermetic stack (see the hermetic-deploy skill), run the slow suite
      - run: docker compose up -d --wait
      - run: bun run test:integration
```

Choosing A vs B: high merge volume or expensive-to-revert deployments → A (queue still gates,
PRs iterate freely). Small team, cheap reverts → B (fastest iteration, main occasionally red).
Merge queues are enabled in repo Rulesets; required checks must be reconfigured to the fast-lane
job names — **branch protection is settings, not YAML**; tell the user exactly which checks to
mark required if you can't change rulesets yourself.

## LN3 — Post-merge failure playbook (mandatory if anything becomes non-blocking)

Moving a check post-merge without a failure playbook just converts failures into surprises.
Minimum viable playbook, appended to the integration workflow:

```yaml
      - name: File failure issue
        if: failure()
        run: |
          gh issue create \
            --title "Post-merge integration failure on ${GITHUB_SHA:0:7}" \
            --label ci-failure \
            --body "Run: ${{ github.server_url }}/${{ github.repository }}/actions/runs/${{ github.run_id }}
          Commit: ${{ github.sha }} by ${{ github.actor }}. Policy: revert-first if not fixed within 1 hour."
        env:
          GH_TOKEN: ${{ github.token }}
```

Confirm the policy in the interview: revert-first (default recommendation), fix-forward with a
time box, or auto-revert automation. Pairs with the `issue-to-agent` skill: label `ci-failure`
can trigger an agent to produce the repro + bisect before a human ever looks.

## LN4 — Cache everything keyed on lockfiles

- `astral-sh/setup-uv@v8` with `enable-cache: true` + `cache-dependency-glob: "uv.lock"`.
- Node: cache the pnpm/bun store keyed on the lockfile hash (setup-bun/setup-node built-ins).
- Turborepo/Nx remote cache for task outputs.
- Playwright browsers, Docker layers (`docker/build-push-action` gha cache) for the slow lane.

## LN5 — The local mirror

Whatever the fast lane runs, agents must be able to run locally with one command and identical
results — otherwise CI stays the bottleneck. Provide `verify` (package.json script, justfile
target, or `scripts/verify.sh`) executing exactly the fast-lane steps, and reference it from
CLAUDE.md/AGENTS.md so agents discover it. Sub-second format/lint means agents can afford to run
it after every edit.

## Anti-patterns to flag

- **LN-A1**: E2E/browser suites required on `pull_request` (the classic 12-minute gate).
- **LN-A2**: required check missing the `merge_group` trigger (stalled queue).
- **LN-A3**: integration tests moved post-merge with no failure routing (silent red main).
- **LN-A4**: matrix builds (3 OS × 4 runtime versions) gating PRs when one representative cell
  would do — full matrix belongs post-merge or nightly.
- **LN-A5**: dependency install uncached, or resolved fresh (`pip install`, un-locked `npm i`)
  on every run.
