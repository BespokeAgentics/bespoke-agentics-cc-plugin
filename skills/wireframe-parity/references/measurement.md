# Phase 2 — Measured parity

Read before Phase 2 (skipped under `--no-browser`). The job: measure the served wireframe and the running app with the **same injected probe**, per state, and diff the numbers against each other and against the spec's frozen Verification snapshot. Numbers beat two screenshots.

## Setup

1. **Serve the wireframe** with `interactive-wireframe`'s script (do not reinvent it):
   ```sh
   "$WIREFRAME_SKILL_DIR/scripts/serve-wireframe.sh" start wireframes/<slug>
   ```
   It prints a `http://127.0.0.1:PORT/` URL, sends `no-store`, and reuses a live server. `file://` fails under browser automation — always serve.
2. **Confirm the app** at `APP_URL` loads (read-only; never submit forms or mutate data).
3. **Inject `assets/wf-probe.js` into BOTH pages** via the browser tool's script evaluation (`javascript_tool` / `evaluate`). Paste the file contents; it sets `window.__wfProbe`. Injecting the same code into both sides is the whole point — the wireframe's built-in `__wf` is *not* used for the diff, so there is no apples-to-oranges risk.
4. **Drift check, once:** `__wfProbe.methods()` on the wireframe should be a superset of the scaffold's `__wf` method names for the assertions you use (`bands`, `contrast`, `markup`, `focusables`, `rect`, `seq`). If the scaffold's `__wf` has changed, note it — the probe may need re-syncing.

## Always call env() first

```js
__wfProbe.env()   // { trustworthyForBehaviour, visibilityState, viewport, reducedMotion, ... }
```

`trustworthyForBehaviour:false` means the tab is backgrounded — scroll events, rAF, transitions and `.focus()` silently no-op, so any behavioural (`seq`) result is a **measurement artifact, not a divergence**. Foreground the tab (a screenshot does it) before trusting behavioural rows. Record `viewport` on both sides: a geometry difference at different viewport widths is a responsive difference, not a parity gap.

## Per state, measure both sides

For each state in `intended-model.md` (each has a wireframe hash URL + an app-state description):

1. **Wireframe:** navigate to its hash URL, re-inject the probe if the page reloaded, run the assertions the spec's Contract/Verification care about.
2. **App:** drive to the equivalent state (navigate the route; apply the role/interaction Phase 1 located). If the state needs an auth session or role you cannot reach, **label it "not measured — requires <role>"** and move on — never assume it.
3. **Measure the same calls on both**, mapping selectors through the region↔zone vocabulary (wireframe `#surface > header` ↔ the app's real header selector from `grounding-map.md`):

| Assertion | Call | Diff rule |
|---|---|---|
| Band geometry / contiguity | `bands([...])` | Edge sequence within **±2px** per boundary; `contiguous` must match the contract's requirement (if the contract says one sticky element, app `contiguous` must be `true`). |
| Contrast | `contrast(sel)` | App must meet the **same AA/AAA verdict** as the wireframe/spec — not the identical ratio. A pass→fail flip is a divergence; a ratio change that stays AA is not. |
| Markup validity | `markup(scope)` | `nestedInteractive` (the `button button` count) and `danglingAriaControls` must be **0** if the spec's Verification recorded 0. New violations are divergences. |
| Focusables | `focusables(scope)` | `offScreen` must stay empty if the spec verified a focus guard. |
| Label / enum fidelity | `texts([...])` | App-rendered strings must equal the real labels ("Internal Review", not `in_review`). |
| Design token | `token('--accent', sel)` | The app's computed token should match the wireframe's `:root` value (from the grounding cache). A different accent hex is a divergence. |
| Behaviour | `seq(steps, observe)` | Only when `trustworthyForBehaviour:true`. The step table must match the spec's behavioural rows. |

## Record the diff

Write `{ANALYSIS_DIR}/measured-parity.md`: one section per state, a table `check · intended (wireframe) · spec-frozen · as-built (app) · Δ · verdict`, where verdict is `pass` (within tolerance), `drift` (outside tolerance but not a contract break), or `diverge` (breaks a contract invariant or flips a pass→fail). Then a "not measured" list of the states/checks you couldn't reach, each with *why*.

## Honesty rules

- **A number you didn't measure is "not measured", never a pass.** A false green retires a check nobody ran.
- **Tolerance is stated, not hidden:** ±2px geometry, same-AA contrast, contiguity-as-required. Anything tighter is the user's call (they declined strict pixel parity).
- **Selector mapping is evidence.** When wireframe `#topbar` maps to the app's `header.app-bar`, record that mapping — a wrong mapping produces a phantom divergence.
- On `--depth deep`, hand each `drift`/`diverge` to Phase 2.5 before it reaches the report.
