# Control scaffolds

Working sources for the deterministic controls. Adapt every matcher, path, and command to what
Phase 0 found — a gate that matches commands the repo never runs protects nothing. Every hook
ships verified: run it with the allow fixture AND the block fixture on stdin and show both
results. Settings edits merge additively into existing JSON.

**Hook contract recap**: PreToolUse hooks read the tool call as JSON on stdin. Exit 0 allows.
Exit 2 blocks, and stderr is shown to Claude — so every block message must explain itself and
name the route to approval.

## §1 · Protected-paths hook (play B5) — `.claude/hooks/protect-paths.sh`

Blocks Edit/Write to paths the team declared frozen (generated code, legacy packages, migration
history). Populate `PROTECTED` from the interview.

```bash
#!/bin/bash
# Blocks edits to protected paths. Owner: <name from interview>.
input=$(cat)
path=$(jq -r '.tool_input.file_path // empty' <<<"$input")
[ -z "$path" ] && exit 0
PROTECTED=("src/gen/" "v1/" "migrations/")   # ← from the interview
for p in "${PROTECTED[@]}"; do
  if [[ "$path" == *"$p"* ]]; then
    echo "Edits under $p are frozen (owner: <name>). Changes go through <route>." >&2
    exit 2
  fi
done
exit 0
```

Wiring (merge into `.claude/settings.json`):

```json
{
  "hooks": {
    "PreToolUse": [
      { "matcher": "Edit|Write",
        "hooks": [ { "type": "command",
          "command": "${CLAUDE_PROJECT_DIR}/.claude/hooks/protect-paths.sh" } ] }
    ]
  }
}
```

Fixtures — allow: `{"tool_input":{"file_path":"src/app/main.ts"}}` → exit 0.
Block: `{"tool_input":{"file_path":"src/gen/client.ts"}}` → exit 2, message on stderr.

## §2 · Secrets guard (play B5) — `.claude/hooks/no-secrets.sh`

PreToolUse on Edit/Write; scans the new content for credential shapes before it lands in the
tree. Keep the patterns few and high-precision — a noisy guard gets disabled.

```bash
#!/bin/bash
input=$(cat)
content=$(jq -r '.tool_input.new_string // .tool_input.content // empty' <<<"$input")
[ -z "$content" ] && exit 0
if grep -qE '(AKIA[0-9A-Z]{16}|-----BEGIN (RSA|EC|OPENSSH) PRIVATE KEY|ghp_[A-Za-z0-9]{36}|sk-ant-[A-Za-z0-9-]{20,})' <<<"$content"; then
  echo "This edit appears to contain a credential. Secrets go in <the repo's secret store>, never the diff." >&2
  exit 2
fi
exit 0
```

## §3 · Test-file protection during fix tasks (play T1)

Protects the feedback loop: an agent fixing code must not weaken the check on that code. Scoped
by an env var so normal test-writing work is unaffected — the fix workflow (SKILL.md Gate 4)
sets `SDLC_FIX_TASK=1` after the failing test is committed.

```bash
#!/bin/bash
# .claude/hooks/protect-tests.sh — active only during fix tasks
[ -z "$SDLC_FIX_TASK" ] && exit 0
input=$(cat)
path=$(jq -r '.tool_input.file_path // empty' <<<"$input")
if [[ "$path" =~ <the repo's test glob, e.g. (^|/)tests?/|\.test\.|_test\.py$> ]]; then
  echo "Fix task in progress: the failing test is the proof and cannot be edited. Fix the code. If the test itself is wrong, stop and say so." >&2
  exit 2
fi
exit 0
```

Alternative when the team prefers no env-var protocol: skip the hook and put the rule in
`REVIEW.md` — reject any fix diff that touches a test.

## §4 · Agent evals in CI (play T2)

`evals/` layout: one JSON per case (`{"prompt": ..., "checks": [...]}`), a `check.sh` that exits
non-zero when a check fails, and a workflow that treats agent configuration as code:

```yaml
# .github/workflows/agent-evals.yml
name: Agent evals
on:
  pull_request:
    paths: ['CLAUDE.md', '.claude/**', 'evals/**']
  schedule:
    - cron: '0 2 * * *'
jobs:
  evals:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: npm install -g @anthropic-ai/claude-code
      - name: Run eval suite
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
        run: |
          set -e
          for eval in evals/*.json; do
            claude -p "$(jq -r '.prompt' "$eval")" \
              --allowedTools "Read,Edit,Bash(<repo's test cmd>)" \
              --output-format json > result.json
            ./evals/check.sh "$eval" result.json
          done
```

Seed 2–3 cases from recent real work (git log is the source): a representative feature-shaped
task, a bug-fix-shaped task, and one policy case exercising the B4 skill. Each production
incident adds a case afterward — that rule goes in the adoption report. Gate config changes on
the results via branch protection on this check. GitLab equivalent: same loop in a scheduled
pipeline job with `rules: changes:` on the config paths.

## §5 · Production approval gate (play D2) — `.claude/hooks/production-gate.sh`

The ASK-shaped hook. Match the repo's REAL deploy commands (from Phase 0: `wrangler deploy`,
`terraform apply`, `kubectl apply`, `make deploy`, `gh workflow run release`, …) — the example
matcher below is only the playbook's illustration.

```bash
#!/bin/bash
# Production deploys require a named release authorization.
# Owner: <release manager from interview>.
cmd=$(jq -r '.tool_input.command // empty' < /dev/stdin)
if [[ "$cmd" == *"<deploy-cmd>"* && "$cmd" == *"<prod-marker>"* ]]; then
  if [ -z "$RELEASE_APPROVAL" ]; then
    echo "Production deploys need release authorization from <name>. Route: <ticket/approval process>. Set RELEASE_APPROVAL=<ticket-id> once granted." >&2
    exit 2
  fi
fi
exit 0
```

Wired under a `Bash` matcher like §1. Non-negotiable gates belong in managed settings (owned by
the platform/IT admin, not switch-off-able per engineer) — team `.claude/settings.json` is the
starting point; note the managed-settings upgrade in the adoption report. Block-path fixture:
a command containing both markers with `RELEASE_APPROVAL` unset must exit 2.

## §6 · CI triage step (play D3)

The safe first move — read-only judgment on failure, no write access:

```yaml
- name: Triage failed build
  if: failure()
  env:
    ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
  run: >
    claude -p "Read the build log at <path Phase 0 found>. Identify the
    most likely cause, say whether the failure looks flaky or real, and
    write a three-line summary for the PR thread." >> triage.md
```

Next steps to document (not scaffold blind): write steps behind branch protection (lint fixes,
doc updates, `@claude` comment fixes — always arriving as PRs), sandboxed execution with
short-lived scoped tokens and no production credentials by default, deployment exposed as
per-environment MCP tools, and a rehearsed single-command rollback — it must be proven in staging
before M1 is allowed to call it.

## §7 · Closing the loop (play M1) — `bands.yaml` + detector contract

Config first — the tiers are version-controlled and the model never sets its own threshold:

```yaml
metric: <chosen metric>            # e.g. ci_test_failure_rate, post_deploy_5xx_rate
baseline: rolling_30d
rules: western_electric            # catches slow drift as well as spikes
tiers:
  1sigma: { action: log }
  2sigma: { action: diagnose,
            tools: "Read,Grep,Bash(<read-only probe cmds>)" }
  3sigma: { action: propose,
            routes: [pull_request, "runbook:<pre-approved runbook id>"] }
```

Detector contract (the script the team owns): deterministic, no model in the detection path;
mean + stddev over the rolling window with the named rules; version controlled AND unit tested —
scaffold it with its tests or leave it as a documented next step, never as untested generated
code. Trigger layer: scheduled workflow / monitoring webhook / cron, invoking Claude stateless
(`claude -p` on a runner, or an Agent SDK service in a sandbox). At 2σ the invocation is
read-only diagnosis; at 3σ the only routes are a PR into the D1 gate or a pre-approved runbook.
The diagnosis is written as `intent.md` (templates.md §1) — anomaly + evidence, proposed outcome,
affected systems, open questions — and enters the queue the service owner triages (fix now /
schedule / dismiss; dismissals tune the bands). A shipped fix adds a T2 eval.
