# Capture — agent-browser, Playwright CLIs, and the verify loop

Verified July 2026 against vercel-labs/agent-browser README and Playwright source/docs.

## agent-browser (default capture stack)

Rust CLI purpose-built for coding agents. Install:

```bash
npm install -g agent-browser      # or: brew install agent-browser | cargo install agent-browser
agent-browser install             # downloads Chrome for Testing on first run
agent-browser install --with-deps # Linux/CI system deps
```

### The core loop

```bash
agent-browser open http://localhost:3000
agent-browser snapshot                     # accessibility tree with refs @e1, @e2 — the
                                           # machine-readable "what's on screen"
agent-browser click @e2
agent-browser fill @e3 "test@example.com"
agent-browser wait --text "Welcome"        # also: --url "**/dash", --load networkidle, --fn "js"
agent-browser screenshot evidence/dash-after-login.png --full
agent-browser errors                       # uncaught JS exceptions — the cheapest real check
agent-browser close
```

More: semantic locators (`find role button click --name "Submit"`), `get text/url/title/count`,
`is visible/enabled/checked`, `console`, `network requests --status 4xx`, HAR recording,
`eval <js>`, and `batch "open …" "snapshot -i" "screenshot out.png"` to run a sequence in a
single process invocation (use `batch` in scripts — much faster than separate calls).

### Before/after — the reviewer's favorite

```bash
agent-browser screenshot evidence/route-before.png --full        # on main / baseline
# ...apply the change...
agent-browser screenshot evidence/route-after.png --full
agent-browser diff screenshot --baseline evidence/route-before.png   # pixel diff
agent-browser diff snapshot  --baseline evidence/route-before.txt    # structural diff
```

`screenshot --annotate` overlays numbered element labels — useful when the agent needs to
*reference* elements in a comment ("the CTA is element 4").

### Isolation for parallel agents

```bash
export AGENT_BROWSER_SESSION=$(agent-browser session id --scope worktree)  # worktree-stable
agent-browser --session "$AGENT_BROWSER_SESSION" open http://localhost:$PORT
```

One session per agent/worktree — no shared cookies, no fighting over the same tab. Auth reuse:
`state save`/`state load` (optionally AES-256-GCM encrypted at rest), `--profile`.

## Playwright equivalents (when Playwright is the incumbent)

```bash
# One-liner screenshots, no test file needed:
npx playwright screenshot --full-page --viewport-size="1280,720" http://localhost:3000 evidence/home.png
npx playwright screenshot --device="iPhone 11" --color-scheme=dark \
  --wait-for-selector="#app" http://localhost:3000 evidence/home-mobile-dark.png
npx playwright pdf http://localhost:3000/report evidence/report.pdf
```

Useful flags: `--load-storage`/`--save-storage` (auth state reuse), `--save-har`,
`--user-agent`, `--timezone`. The newer persistent-session **Playwright Agent CLI**
(`npm i -g @playwright/cli` → `playwright-cli screenshot/snapshot/pdf`) mirrors agent-browser's
model if the team prefers all-Microsoft.

**Traces** — the richest evidence for test failures:

```js
// playwright.config: trace: 'on-first-retry'
```

```bash
npx playwright show-trace trace.zip     # local viewer; or drag-drop at trace.playwright.dev
```

Traces are zips (screenshots + DOM + network + console per step) — store as CI artifacts, link
from the evidence comment.

## Evidence convention

```
evidence/
  <run-id>/                  # branch name or CI run id
    manifest.json
    home-default.png
    home-default.diff.png    # only when a baseline diff ran
    checkout-error-state.png
    console-check.txt        # output of `agent-browser errors`
```

`manifest.json` — the machine-readable half (agents consume this; humans get the PR comment):

```json
{
  "commit": "abc1234",
  "captured_at": "2026-07-13T18:20:00Z",
  "target": "http://localhost:49155",
  "tool": "agent-browser 0.x",
  "viewport": "1280x720",
  "checks": [
    { "name": "console-errors", "result": "pass", "detail": "0 uncaught exceptions" },
    { "name": "diff:home-default", "result": "pass", "detail": "0.0% pixels changed" }
  ],
  "captures": ["home-default.png", "checkout-error-state.png"]
}
```

Naming: `<route-or-flow>-<state>.png`, kebab-case, no timestamps in filenames (the manifest and
directory carry time; stable names make baselines diffable).

## scripts/evidence.sh (shape)

```bash
#!/usr/bin/env bash
set -euo pipefail
RUN_ID="${1:-$(git branch --show-current)}"
TARGET="${TARGET_URL:-$(scripts/dev-stack.sh url default 2>/dev/null || echo http://localhost:3000)}"
OUT="evidence/$RUN_ID"; mkdir -p "$OUT"
export AGENT_BROWSER_SESSION=$(agent-browser session id --scope worktree)

routes=("/:home-default" "/dashboard:dash-default")   # generated from the interview
for r in "${routes[@]}"; do
  path="${r%%:*}"; name="${r##*:}"
  agent-browser batch \
    "open $TARGET$path" \
    "wait --load networkidle" \
    "screenshot $OUT/$name.png --full"
done
agent-browser errors > "$OUT/console-check.txt" && echo "console: clean"
agent-browser close
# manifest written by a small node/python helper or inline jq — include commit, target, checks
```

Determinism rules (fix these before enabling diffs as gates): fixed viewport, explicit
`--color-scheme`, `wait` until animations/data settle, mask genuinely-live regions, same
browser build via `agent-browser install` pinning in CI.
