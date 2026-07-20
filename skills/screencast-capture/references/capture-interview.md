# Phase 0 — Capture planning interview

A vague "record my app" isn't yet a recording. Before touching the browser, turn the request into a
concrete **shot list** you can execute deterministically — the URL to open, the ordered steps to
perform, and how the output should look. Recording is cheap to re-run but annoying to babysit, so
spend a moment here to get it right.

Use whatever the user already gave you (`start-url-or-flow`, `--url`, `--overlays`, `--reel`/`--no-reel`)
and only ask about what's still missing. Prefer inference over interrogation — if the positional was a
URL and a one-line flow, you may already have enough; confirm rather than re-ask.

## The interview (AskUserQuestion)

Max 4 questions per call. Seed options from context (the URL's app, the repo you're in). "Other" is
always available — the user knows the demo they want better than you do.

**Q0 — Capture engine.** (single, skip if `--engine` was passed) Worth asking when the user cares about
fidelity or has mentioned graininess/resolution:
*"Quick tab capture — gif, zero-setup, ~1200px"* (default) · *"High-fidelity screen recording — native
resolution + bitrate; needs macOS Screen-Recording permission and records the whole monitor"*. Maps to
`ENGINE = chrome-gif | screen`. If `screen`, also settle **which monitor** (`--display` — offer to
identify it by capturing a test frame from each screen) and **quality** (`--crf`, default 18); the
permission gate is verified in pre-flight, not here.

**Q1 — What flow should I record?** (single, or skip if the positional already described it)
If the step sequence is unclear, ask for it in the user's words and offer a couple of shaped options,
e.g. *"A short happy-path walkthrough"* · *"A specific feature end-to-end"* · *"I'll give you the exact
steps"*. Capture the concrete steps as free text — you'll expand them into the shot list.

**Q2 — Starting URL & auth.** (single, or skip if `--url`/positional gave it)
Confirm the URL to open. Ask whether it needs a login you'll pause for: *"Yes, I'll log in during the
setup pause"* · *"No auth needed"* · *"It's already logged in in my browser"*. This sets expectations
for the manual gate — you never type the credentials yourself.

**Q3 — Look of the recording.** (single, **`chrome-gif` only** — skip if `--overlays` was passed, or if
`ENGINE=screen`, which draws the real cursor + native click flashes)
*"Click indicators only (recommended)"* · *"Clean — no overlays at all"* · *"Fully annotated (labels +
progress bar + watermark)"*. Maps to `OVERLAYS = clicks | clean | full`.

**Q4 — After recording?** (single, skip if `--reel`/`--no-reel` was passed)
*"Make the MP4, then ask me"* (recommended, the default) · *"Automatically turn it into a narrated
highlight reel"* · *"Just the MP4 / GIF, no reel"*. Maps to `HANDOFF = ask | always | never`.

If the user hasn't given a `capture-label`, infer a short kebab-case slug from the app + flow (e.g.
`acme-checkout-demo`) and confirm it in passing or just set it — it only names files.

## Persist `{OUT_DIR}/capture-plan.md`

Write the shot list you'll execute. This is the contract Phase 1 follows:

```markdown
# Capture plan — {CAPTURE_SLUG}

- Start URL: https://app.example.com/dashboard
- Auth: user will log in during the setup pause (no credentials typed by the agent)
- Engine: chrome-gif            (or: screen · display <idx> · crf 18 · crop auto)
- Overlays: clicks              (chrome-gif only)
- Handoff: ask
- Target: a ~30–45s happy-path walkthrough

## Shot list (in order)
1. Land on the dashboard; screenshot the populated state.
2. Click "New project" (top-right); wait for the modal.
3. Type "Q3 Launch" into the name field.
4. Click "Create"; wait for the redirect to the project view.
5. Open the "Settings" tab; scroll to the integrations section.
6. Screenshot the final state.

## Notes
- Skip: billing page (has real card data on file) — do not navigate there.
```

Keep the shot list tight and literal — each numbered step is one or two browser actions plus a
screenshot. Call out anything sensitive to avoid (pages with real personal/financial data). Then set
`CAPTURE_SLUG`, report the plan back in one line, and proceed to load the browser tools.
