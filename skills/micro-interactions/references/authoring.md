# Authoring: write the project files against the runtime

The runtime (`assets/runtime/`) is shared and never edited per project. A project is
seven files the model writes into the output folder; `scripts/build.py` copies the
runtime next to them and fills `index.html`.

| File | Holds | Start from |
|---|---|---|
| `page.json` | Page copy: title, lede, section intros, guardrails, footer | `assets/template/page.json` |
| `tokens.css` | The app's tokens mapped onto the runtime variables, the brand mark CSS, `@font-face` | `assets/template/tokens.css` |
| `stage.css` | Project-only mini-app shapes the runtime lacks (a dock, a capture card…) | empty file is fine |
| `data.js` | `MI.prims`, `MI.flows`, `MI.ideas`, `MI.firstOrder`; first line `window.MI = window.MI \|\| {};` | `assets/template/data.js` |
| `demos-*.js` | One demo per motion and per idea | `examples/worklens/demos-1.js` |
| `walk.js` | `MI.walk`: the mock app and its steps | `examples/worklens/walk.js` |
| `assets/` | 2–4 real screenshots (JPEG, ≤ 1200 px), favicon, fonts | — |

Load order (the template fixes it): `data.js` → `runtime/mi-core.js` → `runtime/mi-kit.js`
→ `demos-*.js` → `walk.js` → `runtime/mi-walk.js`.

## A demo

```js
MI.demos.C8 = (s, at) => {           // s: the stage element; at(ms, fn): schedule a step
  const p = MI.pad(s);                 // a centered column inside the stage
  const bar = B.status("flight", "Running · 0:00");
  p.appendChild(bar);
  MI.count(at, bar.lab, 0, 0, 2, 600, (n) => `Running · ${MI.elapsed(n)}`);
  at(1900, () => B.settle(bar, "ok", "Fast · just now"));
};
```

Rules:

- **Start from the state before the trigger**, show the trigger (`MI.press` on the
  control the person presses), then the motion, then the resting state. Total 2–6 s.
- **Use the app's real labels and data shapes** from discovery. "T-5 · Requests dock
  cancel" beats "Item 1".
- **Every motion goes through a helper** (`MI.tick`, `MI.latch`, `MI.flip`, …), never a
  hand-written `animate()` without a still path. Helpers check `MI.still(s)` and skip
  movement under Reduced, keeping color and text.
- **Escape `<`** in any text you put in `data.js` (`&lt;`); the build check catches it.
- Demos must not depend on each other or on timing outside their own `at()` calls.
  Every scheduled step is cancelled on replay.
- One demo per idea id and one per motion id: `build.py` fails on a missing demo, an idea
  demo with no idea, and a motion demo with no motion.
- Project-specific builders go at the top of a demos file: `B.capture = (img, title) => …`.

## The runtime API

**Stage and DOM:** `MI.h(tag, cls, html)` · `MI.pad(s)` · `MI.btn(label, "fill"|"")`
(label in `.lab`) · `MI.mark(state)` an SVG status mark, states `flight` (dashed ring)
· `retry` (dashed amber) · `ok` · `warn` · `bad` · `idle` · `MI.set(mark, state)`
· `MI.arrow` (SVG string) · `MI.img(name)` → `assets/<name>.jpg`.

**The five motions:**

| Helper | Does |
|---|---|
| `MI.tick(el, text, "up"\|"down")` | Replace text, roll it in from the direction of change |
| `MI.latch(el, hue, cls?)` | Hold a state hue and fade (`hue`: `accent` `green` `amber` `red`); `cls` `"m-wash"` for rows |
| `B.settle(row, state, label)` | Dashed ring → solid dot + ticked label (`row` from `B.status`) |
| `MI.ghost(s, fromEl, toEl, label)` | Handoff ghost from a control to where the request is tracked |
| `MI.echo(at, btn, text, ms, then?)` | Control answers in words, then reverts (or becomes `then`); `ms: 0` keeps it |

**Supporting:** `MI.flip(s, els, mutate, ms)` FLIP glide across a DOM change ·
`B.flipScale(s, el, mutate)` shared-element move with scale · `MI.swap(el, html)`
cross-fade a label in place · `MI.press(s, el)` show what was clicked (a teaching aid,
not product motion) · `MI.burst(s, el)` a rare celebration · `MI.type(at, el, text,
start, every)` returns end ms · `MI.count(at, el, start, from, to, step, fmt)` ·
`MI.elapsed(n)` → `0:42` · `B.enter(s, el, dy)` · `B.fade(s, el, to, ms)` ·
`B.hop(s, liveDots)`.

**Builders (`MI.b`, aliased `B`):** each returns an element with its parts attached.

| Builder | Parts |
|---|---|
| `B.tile(label, num, foot, progress?)` | `.v` number, `.f` footnote, `.p` progress fill: `t.p.style.setProperty("--w", "0.25")` (a 0–1 scale; add a `transform` transition to glide) |
| `B.card(id, title, pill, pillCls, foot)` | `.pill`, `.foot`, `.ttl` |
| `B.col(name, n, cls)` | `.body`, `.n`, `.head` (`cls`: `go` `warn` `ok` `bad`) |
| `B.hud(s, tickerHtml, count, { tab, chip })` | a bottom bar labelled in the app's words: `.ticker`, `.chip` (`.chip.v`, `.chip.dot`) |
| `B.status(state, label)` | `.mk`, `.lab` |
| `B.check(on)` · `B.live()` · `B.svgArrow(dir)` | checkbox · three live dots · arrow SVG |

**Primitive classes** (in `runtime/mi-stage.css`): layout `m-row m-col m-grow m-cols
m-list m-listrow m-box m-panel`; text `m-title m-small m-muted m-mono m-strong m-clip
m-eyebrow`; controls `m-btn(.fill .hot .wait) m-field(.focus) m-link m-pill(.ok .warn .bad
.go) m-check m-chip`; surfaces `m-card m-tile m-drawer m-drawer-head m-scrim m-hud
m-log m-logrow(.live)`; status `m-steps m-step(.on) m-step-line(.on) m-notice m-err
m-agent`; icons `m-arrow` (via `MI.arrow` / `B.svgArrow`). Anything else goes in the
project's `stage.css`.

## walk.js

```js
(() => {
  const { h, b: B } = MI;
  const W = (MI.walk = { width: 1000, height: 510 });
  W.intro = "Press Play. …";
  W.steps = [{ t: "An agent claims T-5", ids: ["B1", "A2"], say: "…" }, …];
  let el = {};
  W.build = (stage) => { el = {}; /* draw the mock app, keep named parts on el */ return el; };
  W.run = [
    (el, ctx) => { const { at, stage } = ctx; at(300, () => { /* step 1 */ }); return 3600; },
    …
  ];
})();
```

- `width`/`height` are the mock app's real size; the runtime scales it to fit.
- Each `run[i]` returns its duration in ms; Play waits that long plus 0.5 s.
- **Jumps fast-forward**: clicking step 5 rebuilds the app and runs steps 1–4 with
  `ctx.sync = true`, where `at()` runs at once and motion is off. So every step must
  only *change* state from where the previous step left it, never assume time passed.
  Helpers that keep their own DOM (a ticker) must check `ctx.sync` and skip transient
  nodes. See `examples/worklens/walk.js` `tickerSay`.
- Draw the mock app from the same builders and real labels as the demos, at a
  realistic density: the walkthrough should read as the app.

## page.json

Keys: `title`, `product`, `plan_href`, `brand_mark_html`, `favicon`, `h1`, `lede`,
`estimate`, `read_from`, `vocab_h2`, `vocab_p`, `walk_h2`, `walk_p`, `start_p`,
`guard_p`, `guard_never[]`, `guard_always[]`, `footer`, `demo_files[]`. Values are
HTML (use `<b>` and `<code>` sparingly). The lede states the count, that each idea
plays, and that nothing is implemented. `read_from` names what was read (`:3000 ·
2026-10-19`, or `code only · 2026-10-19`).
