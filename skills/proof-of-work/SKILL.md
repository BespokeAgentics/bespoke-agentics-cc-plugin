---
name: proof-of-work
description: >
  Give coding agents the means to prove their work instead of asserting it: installs and wires
  browser-driving + screenshotting tooling (vercel-labs agent-browser with snapshot/diff
  baselines, Playwright screenshot/trace CLI), an evidence directory convention, cloud asset
  storage for hot-linkable images (S3/R2 presigned URLs vs GitHub artifact zips), and PR-comment
  evidence templates — so "I fixed the layout" arrives with before/after pixels, console-error
  checks, and a trace. Use when the user says "agents should screenshot their changes", "prove
  the UI works", "attach evidence to PRs", "set up agent-browser", "where do agent screenshots
  go", "verify visually", or invokes /agentnative:proof-of-work. Pairs with hermetic-deploy
  (something running to point the browser at) and issue-to-agent (evidence attached to repros).
args:
  - name: mode
    description: "`plan` | `implement` (default). `plan` writes the evidence-stack proposal to ./plans/; `implement` interviews, installs, and wires it."
    required: false
  - name: scope
    description: "Optional: `local` (agent-side tooling + conventions only), `ci` (CI capture + storage only), or `both` (default)."
    required: false
---

<role>
You are building the trust infrastructure for agent work. An agent's claim of success is
worthless to a reviewer at exactly the moment it matters — when the reviewer wasn't watching. The
fix is structural, not rhetorical: give agents capture tools cheap enough to use after every
change, a place to put evidence where reviewers actually see it, and conventions that make
evidence comparable over time (baselines, naming, retention). The test of your work: a reviewer
can judge a UI change from the PR alone — before/after images, zero-console-errors check, a
clickable trace — without checking out the branch. And the agents themselves iterate better,
because a screenshot they take is feedback they can see.
</role>

<context>
The user invokes this via `/agentnative:proof-of-work [mode] [scope]`, or implicitly when asking
how agents can verify or demonstrate UI work.

Tool mechanics live in `references/capture.md` (agent-browser, Playwright CLIs, the
verify-loop); storage and publishing live in `references/storage.md` (artifact vs S3-presign
trade-off, PR comment templates, retention). The stack, top to bottom:

1. **Capture** — `agent-browser` (Rust CLI, npm/brew/cargo; purpose-built for agents:
   accessibility-tree `snapshot` with `@e1` refs, `screenshot --full --annotate`,
   `console`/`errors`, `network requests --status 4xx`, and crucially `diff screenshot
   --baseline` / `diff snapshot --baseline` for before/after). Playwright's CLIs
   (`npx playwright screenshot`, the newer `playwright-cli`, trace files) where Playwright is
   already the repo's test stack.
2. **Convention** — an `evidence/` layout with stable names and a manifest, so runs are
   comparable and CI can publish mechanically.
3. **Storage** — GitHub Actions artifacts v4 (free, auth-gated zips — fine for traces/HAR) vs
   S3-compatible presigned URLs (hot-linkable images that render inline in PR comments — what
   reviewers actually look at). Most teams want both: images to the bucket, bulky
   traces to artifacts.
4. **Publishing** — a PR comment template the agent (or CI step) fills: claim → evidence →
   how-to-reproduce. One updated comment per PR, not a stream.

The economics run on fast capture: a screenshot that costs two seconds gets taken after every
edit; the verify loop (change → screenshot → check console → assert text) becomes the agent's
inner loop, not a final ceremony.
</context>

<pipeline>

## Phase 0 — Detect the surfaces

1. **UI stack** — web app? Storybook? Which dev-server command and port? (Hermetic-deploy's
   stack script, if present, is the canonical way to get a running target.)
2. **Existing capture** — Playwright installed (reuse its browsers/config)? Existing screenshot
   tests or visual-regression tooling (don't duplicate Chromatic/Percy — integrate)?
3. **Storage available** — bucket + credentials in CI secrets? R2/MinIO? Nothing yet?
4. **Where agents run** — locally (Claude Code/Cowork sessions), in CI (claude-code-action
   workflows from issue-to-agent), or both — this sets `scope`.

## Phase 1 — Interview

AskUserQuestion:

1. **Storage target** — S3/R2 bucket (recommended when reviewers need inline images), artifacts
   only (zero new infra), or local-only `evidence/` committed per branch (small teams; caution
   on repo size — prefer git-ignored + published). Bucket naming/retention if applicable.
2. **Evidence classes** — screenshots only; + console/network checks; + traces; + snapshot
   diffs as review gates.
3. **Baseline policy** — where do "before" images come from: captured from main by CI
   (recommended, always fresh) vs committed baselines updated deliberately (visual-regression
   style).
4. **Privacy line** — production-like data on screen (see sim-data) is fine; real user data in
   screenshots uploaded to a bucket is not. Confirm what the app might display.

## Phase 2 — Install and wire capture

1. Install agent-browser (`npm i -g agent-browser && agent-browser install --with-deps` in CI
   images; document local install). If Playwright is the incumbent, wire its equivalents
   instead — one capture stack, not two.
2. Create the evidence convention (see `references/capture.md`): `evidence/<branch-or-run>/`
   with `manifest.json` (what, when, against which commit/URL, tool versions), stable names
   (`<route>-<state>.png`), git-ignored locally unless the interview chose committed baselines.
3. Write `scripts/evidence.sh` (or a justfile target) wrapping the verify loop so every agent
   and CI job captures identically: start/attach to the app, wait healthy, per-route:
   `screenshot --full`, `errors` (fail on uncaught exceptions), optional `diff screenshot
   --baseline`. Session-isolated (`--session` per run) so parallel agents don't collide.
4. Document it in CLAUDE.md/AGENTS.md if present: *when you change UI, run
   `scripts/evidence.sh` and cite the output in your PR/comment* — the convention only works if
   agents discover it.

## Phase 3 — Wire storage + publishing (scope: ci or both)

Per `references/storage.md`:

1. CI step: after tests, upload `evidence/**` — images to the bucket with presigned GETs
   (7-day default), traces/HAR to `actions/upload-artifact@v4`.
2. PR comment step: create-or-update a single "Evidence" comment: before/after image table
   (presigned URLs render inline), console-check result, trace artifact link, repro command.
3. Baseline job on `push: main` (if the interview chose CI-captured baselines): capture the
   route set, write to `baselines/<route>.png` in the bucket.
4. Secrets: bucket credentials as CI secrets; never in the compose file or scripts.

## Phase 4 — Verify

Prove the whole chain once, for real:

1. Run `scripts/evidence.sh` against the running app; confirm images exist, manifest is valid,
   `errors` returns clean (or correctly fails on an injected `console.error`).
2. Push a throwaway branch changing something visible; confirm CI captures, uploads, and the
   PR comment renders inline images from presigned URLs.
3. Diff check: rerun against an unchanged app — `diff screenshot --baseline` reports no
   difference (deterministic rendering: fixed viewport, `--color-scheme`, animations settled
   via `wait`; flaky diffs are worse than no diffs, so fix determinism before shipping).
4. Retention sanity: presign expiry ≥ typical PR review lifetime; artifact retention-days set.

</pipeline>

<evidence_contract>
Bake into every generated prompt/workflow — a claim about observable behavior is complete only
with:

1. **The artifact** — screenshot/diff/trace named per convention, linked or inlined.
2. **The check** — the mechanical assertion that ran (`errors` clean, `wait --text` succeeded,
   diff within threshold), with its actual output quoted.
3. **The recipe** — the exact command a human runs to see it live.

"Looks right to me" without all three is an assertion, not evidence.
</evidence_contract>

<degradation>
- **No UI** (API/library repo) — evidence becomes: test output, coverage deltas, benchmark
  runs, `curl` transcripts against the hermetic stack. Same contract, different artifacts; say
  so and skip browser tooling.
- **No bucket, no appetite for one** — artifacts-only: images still uploaded, reviewers click
  through a zip; note the inline-render loss explicitly.
- **agent-browser unavailable** (install blocked) — `npx playwright screenshot` one-liners +
  `npx playwright show-trace`; the loop survives, annotation/diff conveniences degrade.
- **Chromatic/Percy already present** — don't rebuild visual regression; wire agent capture to
  feed it and keep this skill's scope to local verify + PR evidence.
- **Non-deterministic UI** (animations, live data) — settle waits, mask regions in diffs, or
  demote diffs to advisory; a flaky gate teaches everyone to ignore it.
</degradation>

<wiki_integration>
When a wiki vault exists: record the evidence conventions (layout, storage, retention, baseline
policy) as a wiki page — future agents must find it — and log the operation in `wiki/_log.md`.
</wiki_integration>

<quality_bar>
- The full chain demonstrated once end-to-end before declaring done (Phase 4.2 actually ran).
- Deterministic captures: two runs of an unchanged app diff clean.
- One evidence comment per PR, updated in place.
- No credentials in tracked files; no real user data in uploaded pixels.
- Evidence usable by both audiences: inline for humans, machine-readable manifest for agents.
</quality_bar>
