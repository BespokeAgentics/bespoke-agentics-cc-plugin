---
name: micro-interactions
description: "Generate a grounded set of micro-interaction ideas for an existing app's user flows and ship them as ONE playable HTML prototype before anything is built. Reads the app (running URL and/or code, DESIGN.md, the motion that already ships), defines a small motion vocabulary (4–6 motions, including the ones that ship, with one signature derived from the app's own rules), then generates 25–40 ideas per app, each one tied to a real trigger, a real function and a reduced-motion path, each with its own replayable demo built from the app's real tokens and labels. The page adds a step-through walkthrough of one realistic journey, filters by flow and motion, an impact/effort matrix with an ordered first batch, and a guardrails list. Use when someone says 'come up with micro-interactions for this app', 'add delight/feedback/motion to these flows', 'prototype interaction details before we implement', 'what should animate here', or 'make the state changes feel alive'. Writes no production code; read-only on the app. Not for a full visual redesign (use reimagine), not for settling one screen's layout (use interactive-wireframe), not for auditing usability (use ux-audit)."
disable-model-invocation: true
---

# Micro-interactions

Point it at an app; get back a prototype of what its flows could feel like.

The premise: **"add some micro-interactions" in prose gets a list of effects; a page
where every idea plays, in the app's own tokens, next to the function it would change,
gets a decision.** And the ideas only hold together if they share a grammar, so the
skill picks a small motion vocabulary first and builds every idea from it.

Three properties do the work:

1. **Grounded.** Every idea cites a real trigger, a real label and a real function
   (`where`), and renders with the app's real tokens. An idea that cannot cite one is
   cut, not softened.
2. **A vocabulary, not a pile.** 4–6 motions, the shipped ones first, one signature
   derived from a rule the app already has. Every idea names the motions it uses, so
   building one motion once serves many ideas.
3. **Playable and honest.** Each idea has its own replayable demo; a Reduced toggle
   replays them all under `prefers-reduced-motion`; behavior changes hiding inside
   motion ideas are flagged for a product decision.

The runtime that renders the page is shared and tested (`assets/runtime/`); per project
the model writes only content. A worked example ships in `examples/worklens/` (37 ideas,
6 flows, 5 motions); read it before writing your own.

## Arguments

`/bespoke-agentics:micro-interactions [<url>] [--flows "a, b"] [--out <dir>] [--ideas N] [--no-serve]`

- `<url>`: the running app to read (optional; without it, read code only and say so).
- `--flows`: restrict to named flows. Default: discover 4–7.
- `--out`: output folder. Default: the project's plan location (see Phase 6), else
  `./micro-interactions/`.
- `--ideas N`: target count (default 25–40; never pad to reach it).
- `--no-serve`: build and check, but do not start a server or open a browser.

Paths in this file are relative to this skill's directory (`<skill>` below). Run commands from the
project root; pass the output folder as a path from there.

## Phase 0: preflight

1. Resolve the output folder (`--out`, then the project's plan rule in `CLAUDE.md` /
   `AGENTS.md`, then `./micro-interactions/`). If a prototype already exists there,
   ask: update it or start a new folder.
2. Note what you may not touch. This skill writes **only** inside the output folder
   (and the project's wiki/plan pages in Phase 6). It never edits app source, never
   submits forms or sends messages in the running app, never commits.
3. If the user or the project asks for a session/plan page (a wiki, `plans/`), open it
   now so the work can be resumed.

## Phase 1: discovery

Read `references/discovery.md` and produce `<out>/discovery.md`: design authority,
tokens, flows (who causes each state change, where its outcome lands), running-app
screens, code anchors, conflicts, not seen.

- With a URL: drive it read-only with the browser tool the harness provides (Playwright
  MCP, or Claude in Chrome when the user wants their own browser). Screenshot each
  flow's main surface and every drawer/dialog it opens, and copy 2–4 real screens into
  `<out>/assets/` as JPEG ≤ 1200 px wide (macOS: `sips -s format jpeg -s formatOptions 74
  -Z 1200 in.png --out out.jpg`; elsewhere: `magick in.png -resize 1200x -quality 74 out.jpg`,
  or keep the PNG and say so).
- Without one: read the view code and mark discovery "from code, not seen running".

**Checkpoint (one line to the user):** the flows found and the motion already shipping.
Continue unless they object; do not wait for an answer to a list they did not ask for.

## Phase 2: vocabulary and ideas

Read `references/ideation.md`. Then:

1. Write the motion vocabulary: shipped motions first (`status: "ships"`), then new
   ones only for jobs no shipped motion does. 4–6 total. Choose and justify the signature.
2. Walk every flow's state changes through the seven questions; write 5–8 ideas per
   flow with every field filled.
3. Mark the first batch (6–10) and order it so shared work comes first.
4. Write the guardrails from the app's rules plus the defaults.
5. Choose one journey for the walkthrough (4–7 steps) that fires the first batch.

Put it all in `<out>/data.js` (start from `assets/template/data.js`: its first line,
`window.MI = window.MI || {};`, must stay) and the copy in `<out>/page.json` (start from
`assets/template/page.json`).

## Phase 3: build the prototype

Read `references/authoring.md`. Write, in the output folder:

- `tokens.css` from `assets/template/tokens.css`, every value from discovery.
  Self-host the app's font next to it when its license allows.
- `stage.css` for any mini-app shape the runtime lacks (keep it small).
- `demos-1.js`, `demos-2.js` (split around 400 lines): one demo per motion
  (`MI.primDemos.<id>`) and one per idea (`MI.demos.<id>`), using the runtime helpers.
- `walk.js`: `MI.walk` with the mock app (`build`) and one function per step (`run`).

Then run:

```bash
python3 "<skill>/scripts/build.py" <out>
```

It copies the runtime to `<out>/runtime/`, fills `<out>/index.html`, and checks the
contract (fields, ids, motion/flow references, a demo for every idea and motion, walk
ids, unescaped `<`, unfilled placeholders). **Fix every FAIL and rerun until it prints
`check: clean`.** Do not hand-edit `index.html` or anything under `runtime/`; change the
project files and rebuild.

## Phase 4: verify in a browser (bounded)

With `--no-serve`, skip this phase and report "browser check not run" in Phase 5.

Serve the folder over HTTP (fonts and images need it), **in the background** so the
session is not blocked, and note the PID to stop it at handover if the user does not
need it:

```bash
python3 -m http.server <free port> --bind 127.0.0.1 --directory <out>   # run in background
```

One batched round, then at most one confirm round:

1. Desktop (1440×900) and phone (390×844), light and dark.
2. In the page, check: no console errors; no horizontal overflow at 390 px
   (`document.documentElement.scrollWidth <= innerWidth`); every stage plays without
   "Demo failed" (`document.querySelectorAll('.stage[data-demo]').forEach(MI.playStage)`);
   the walkthrough plays, steps, and **jumps** to the last step cleanly.
3. Look at screenshots of: the top (motion cards), the walkthrough mid-journey, and a
   catalogue section. Usual defects: text clipped in a demo, a control overlapping a
   demo's docked bar, labels overflowing tiles, a jump that leaves stale nodes behind.
4. Toggle Reduced and replay one demo of each motion: meaning must survive.

Fix everything found in one batch, rebuild, confirm once, stop.

## Phase 5: hand over

- Open the page for the user (their browser when available, per the harness rules;
  otherwise give the URL and the serve command). Say which server is still running and
  how to stop it (`kill <pid>`).
- Report in this shape, briefly:
  - what the page has (counts; the signature motion and why);
  - the first batch in build order;
  - **behavior changes** hidden in ideas, as a list needing the user's yes;
  - what was not seen (flows read from code only, conflicts found);
  - the one next action ("pick ideas to build, or say 'first batch'").

## Phase 6: record

If the project keeps plans or a wiki, write a plan page that links the prototype:
context (what was read), decisions (vocabulary, signature, first batch and why),
the idea table by flow, phases to implement (shared motion first), verification, risks.
Append to its index/log per the project's rules. If it has no such convention, the
output folder's `discovery.md` and `index.html` are the record; say so.

## Rules

- **Read-only on the app.** No edits to app source, no form submits, no commits.
- **No invented tokens, labels or functions.** Unknown → cite what you saw or cut it.
- **Never pad.** A small app with 14 good ideas beats 30 with filler.
- **Reduced motion is designed, not dropped.** Every idea's `reduced` says what stays.
- **The runtime is shared.** Never patch a project's copied `runtime/` folder (the next
  build overwrites it). A runtime defect is fixed in the plugin repo's
  `skills/micro-interactions/assets/runtime/` and the example rebuilt; from any other
  project, report it to the user with the file and the fix instead of editing the
  installed plugin copy, which an update replaces.
- **One celebration at most.** Reserve bursts for a rare, consequential act.

## Files

| Path | What |
|---|---|
| `assets/runtime/` | Shared page + motion runtime (CSS, `mi-core.js`, `mi-kit.js`, `mi-walk.js`) |
| `assets/template/` | `index.html` (placeholders), `page.json`, `tokens.css`, `data.js` starters |
| `scripts/build.py` | Copy runtime, fill the page, check the contract (stdlib only) |
| `references/discovery.md` | How to read the app, tokens, flows, anchors |
| `references/ideation.md` | The motion vocabulary and the seven questions per state change |
| `references/authoring.md` | Writing data, demos and the walkthrough against the runtime API |
| `examples/worklens/` | A complete worked example (a live work board): build it to see the target |
