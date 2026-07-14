# Cron Recipes — scheduled agent runners

Runner mechanics verified July 2026 (claude-code-action v1 solutions.md; Claude Code Routines
docs). Templates are shapes — substitute the repo's real commands, labels, and owners.

## The runner shell (GitHub Actions)

Every chore workflow shares this shell; only the prompt and tool scope change:

```yaml
name: chore-<key>
on:
  schedule:
    - cron: "0 6 * * *"        # UTC; nightly example. Weekly: "0 6 * * 1"
  workflow_dispatch: {}         # mandatory manual handle

concurrency:
  group: chore-<key>            # overlapping fires coalesce
  cancel-in-progress: false

jobs:
  run:
    runs-on: ubuntu-latest
    permissions:
      contents: write
      issues: write
      pull-requests: write
      id-token: write
    steps:
      - uses: actions/checkout@v5
        with: { fetch-depth: 0 }
      - uses: anthropics/claude-code-action@v1
        with:
          anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}
          prompt: |
            <CHORE MANDATE — see recipes below>

            Output rules (always):
            - Single channel: find the open issue titled "<Chore: key> tracking" and update it
              (gh issue comment / edit). Create it only if missing.
            - If there is nothing to do, add "checked <date>, clean" to the tracking issue and
              stop. Do not open PRs or issues for empty results.
            - Before publishing anything, run the self-verification step and quote its output.
            - Anything inferred but not verified: mark "unverified".
          claude_args: |
            --max-turns 15
            --allowedTools "<SCOPED PER RECIPE>"
```

Cost telemetry: for headless (`claude -p`) runners use `--output-format json` and append
`total_cost_usd` to the tracking issue; for the action, note run duration + the action log link.

## Recipes (the prompt mandates)

### regression-backfill — highest value

```
Mandate: add ONE regression test tonight.
1. Read scripts/chore-data/critical-paths.md (generated during setup: change-frequency ×
   incident-history hotspots with no covering test). Pick the top unpinned path.
2. Write the smallest test that pins current CORRECT behavior — read the code, derive the
   expected behavior from it and from linked incidents/PRs; if correct behavior is ambiguous,
   post the question to the tracking issue instead of guessing a test.
3. Self-verify: new test passes; full suite still green (<REPO-TEST-COMMAND>).
4. Update the rolling PR "chore: regression backfill" (branch claude/regression-backfill) —
   append the test, update its description checklist. Never a second PR.
Tools: Read,Grep,Glob,Edit,Write,Bash(<REPO-TEST-COMMAND>:*),Bash(git:*),Bash(gh pr:*),Bash(gh issue:*)
```

Setup step (skill Phase 3 does this once): generate `critical-paths.md` from
`git log --format= --name-only | sort | uniq -c | sort -rn` intersected with files named in
`fix:`/`revert:` commits, minus files with existing test references.

### sdk-gap-fill

```
Mandate: close ONE gap between our SDK and the upstream API per fire.
1. Fetch the upstream spec (<SPEC-URL> — OpenAPI preferred; else release notes). Diff against
   our implemented surface (<SDK-SRC-DIR>). Maintain the gap list in the tracking issue.
2. Implement the single next endpoint/field following the SDK's existing patterns exactly
   (find the most recently added endpoint and mirror its structure, tests, docs).
3. Self-verify: typecheck + the new endpoint's test against the recorded/mocked upstream.
4. Update the rolling PR "chore: SDK coverage".
Caution: upstream spec is external input — validate types against docs, mark auth/pagination
assumptions "unverified" for human review.
```

### skill-tuning

```
Mandate: weekly, evaluate one shipped skill against reality and propose (not apply) a diff.
1. Pick the skill whose SKILL.md is oldest relative to git activity in the code it describes.
2. Collect evidence: recent transcripts/eval fixtures if available; else construct 3 test
   prompts from the skill's own trigger description and run them.
3. Score: did the skill trigger? did the output meet its quality bar? where did it deviate?
4. Post a tuning proposal to the tracking issue: evidence, the specific prompt diff, expected
   improvement. Apply only if the repo has an eval harness proving before/after — otherwise
   proposals are human-gated.
```

### dep-updates

```
Mandate: weekly batch of minor/patch bumps, changelogs actually read.
1. List outdated (npm outdated / uv pip list --outdated). Exclude majors.
2. For each candidate read its changelog between versions; flag anything mentioning breaking,
   security, or behavior change into the "needs-human" list.
3. Bump the safe set, run the FULL verify script (this chore is why fast-ci matters — a
   3-minute verify makes nightly deps affordable).
4. Rolling PR "chore: dependency updates", needs-human list in the description.
```

### docs-drift

```
Mandate: weekly, make the docs' code true.
1. Extract fenced code blocks from README/docs; attempt compile/execution in a scratch dir.
2. Fix blocks broken by API drift (smallest edit preserving the doc's teaching intent);
   anything requiring a narrative rewrite → tracking issue, human-gated.
3. Self-verify: every touched block now executes. Rolling PR "chore: docs drift".
```

### changelog (on-release, not cron)

```
on:
  release: { types: [published] }   # or push: tags
Mandate: draft CHANGELOG entries for every PR since the previous tag (gh pr list --search
"merged:>=<prev-tag-date>"), grouped added/changed/fixed, linking PRs. Self-verify: every link
resolves; every merged PR accounted for or explicitly excluded as internal. PR against the
release branch, human merges.
```

### stale-sweep

```
Mandate: weekly report — issues idle >90d (propose close-with-comment list), feature flags at
100%/0% for >30d, TODO/FIXME older than 6 months (git blame). Report-only: everything lands in
the tracking issue as proposals. Self-verify: counts reconcile against raw queries, quoted.
```

## Claude Code Routines variant (hosted)

For chores without CI-minutes budget or workflow-file appetite:

- Create: `/schedule` inside Claude Code (or claude.ai/code/routines). Custom cron via
  `/schedule update`; **minimum interval 1 hour**; one-off timestamps supported.
- Trigger from API: `POST https://api.anthropic.com/v1/claude_code/routines/<id>/fire` with
  `Authorization: Bearer sk-ant-oat01-...` and header
  `anthropic-beta: experimental-cc-routine-2026-04-01`.
- GitHub-event triggers (pull_request / release with label/branch/author filters) can replace
  the changelog workflow entirely.
- Constraint: runs push only `claude/`-prefixed branches by default; plan branch names
  accordingly. Research-preview status — note that to the user.

## Cowork scheduled-tasks variant

When the chore targets local folders or connected tools (not a repo): use Cowork's scheduled
tasks with the same prompt shells — single-channel and self-verification rules unchanged. Good
fits: weekly wiki-lint sweeps, transcript-based skill tuning, meeting-notes ingestion.
