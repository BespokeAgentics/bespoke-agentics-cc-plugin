# Browser-verification playbook

Read before Phase 5. Measure the wireframe; do not eyeball it. A number belongs
in a spec — an impression does not.

## The hidden-tab problem — read this first

An automation tab is usually **backgrounded**, and a backgrounded tab is not a
paused tab: it is a tab where a specific set of things silently do nothing and
report success. Every behavioural "failure" you see is a suspect until you have
ruled this out. In the session this skill was distilled from, two test runs were
declared failures and re-debugged before anyone noticed the tab was hidden.

**Always start with `__wf.env()`** and read `trustworthyForBehaviour`:

```js
__wf.env()
// { visibilityState:"hidden", documentFocused:false,
//   trustworthyForBehaviour:false, viewport:{…}, scrollY:0, … }
```

If it is `false`, do not report any behavioural result without the workaround
below — and never report one as a defect.

| Symptom | Cause | Workaround |
|---|---|---|
| `navigate` fails on a local file | `file:///…` is rewritten to `https://file:///…` | Serve over HTTP (`scripts/serve-wireframe.sh`) |
| Scroll handlers never fire | Hidden tab delivers no scroll events | `__wf.scrollTo(y)` — sets position **and** dispatches the event |
| `requestAnimationFrame` never runs | rAF is throttled to zero in a hidden tab | Prefer synchronous logic; force layout (`__wf.env().docHeight`) instead of waiting a frame |
| A CSS transition appears frozen | Transitions do not advance past t=0 while hidden | `__wf.noMotion(true)`, measure the end state, `__wf.noMotion(false)` |
| `element.focus()` does nothing | Document is not focused | `__wf.focusIn(sel)` — dispatches a real `focusin` |
| Results change between two calls | Only a screenshot foregrounds the tab; it re-hides after | Take a screenshot immediately before a timing-sensitive check |
| **You rebuilt the file but the page is the old one** | **Navigating to the same path with a different `#hash` is not a navigation — nothing reloads** | **`location.reload()` after every rebuild.** Do not trust `navigate` to pick up a new build |
| The state does not match the hash you navigated to | Same cause: no reload, so nothing re-read the hash | The scaffold listens for `hashchange` and re-hydrates. If you hand-rolled the wireframe, add that listener |
| A `javascript_tool` call returns "blocked" | The payload contained a URL or query string | Never return `location.href`/`location.hash`; `__wf.env()` returns `path` only |

The rebuild-reload trap deserves emphasis because it fails *quietly and convincingly*: you rebuild,
navigate, measure, and get clean numbers — for the previous build. Every result after that point is
wrong in a way nothing on screen reveals. When in doubt, assert you are on the build you think you
are (`document.title`, or a version string in the surface).

The honest reporting rule: if a behaviour could not be verified with the tab
visible, write **"not verified — hidden tab"** in the spec rather than
"verified." A false green here is worse than a gap, because it retires a test
nobody ran.

## The four assertion families

### 1. Geometry — prove structure, not vibes

```js
__wf.bands(['#topbar', '#breadcrumb', '#projectnav', '#featurenav'])
// { rows:[{sel:'#topbar', top:0, bottom:44, gapToNext:0}, …], contiguous:true }
```

Run it in **both** states (at rest, and after the state change) — bands that are
contiguous at the top of the page and separated when scrolled is the classic
multiple-sources-of-truth bug, and it is invisible in a single screenshot.

```js
__wf.rect('#panel')                       // one element
__wf.scrollTo(400); __wf.bands([...])     // the same assertion, scrolled
```

### 2. Contrast — computed, never guessed

```js
['.pill-open', '.pill-closed', '.muted'].map(s => __wf.contrast(s))
// [{ sel:'.pill-open', fg:'#035530', bg:'#e7f2ec', fontSize:9.5,
//    large:false, ratio:7.8, AA:true, AAA:true }, …]
```

Composites alpha over ancestors and applies the WCAG large-text rule (≥24px, or
≥18.66px bold). Small text on a tint is where this fails, and it fails silently:
the colour looks fine, and it is 3.9:1.

### 3. Markup validity — what the mockup would force in production

```js
__wf.markup()
// { nestedInteractive:[], unnamedControls:[], danglingAriaControls:[],
//   toggleWithoutExpanded:[], duplicateIds:[], imagesWithoutAlt:0 }

__wf.focusables('#surface')
// { tabbable:6, notRendered:2, offScreen:[] }   ← this is a clean result
```

`notRendered` is content inside a collapsed disclosure (`display:none`): not in
the tab order, correctly ignored. `offScreen` is the finding — **rendered and
tabbable, but outside the viewport.** Keeping them separate matters: a check
that fires on every closed accordion gets tuned out, and the real defect goes
with it.

`nestedInteractive` is the one that bites. A clickable row that also carries
buttons is a `<button>` containing `<button>` — illegal, and the workaround in
real code is an inert `<span>` that no keyboard user can reach. Catching it in
the wireframe changes the structure before it becomes a permanent constraint.

`offScreen` focusables catch content hidden by transform or clip: it is still in
the tab order, so a keyboard user can focus things nobody can see. If the design
hides a band, it needs a `focusin` guard that reveals it.

### 4. Behavioural sequences — a table, not an impression

```js
__wf.seq(
  [ {scrollTo:0,   label:'rest'},
    {click:'#disclosure', label:'expand'},
    {scrollTo:600, label:'scroll while open'},
    {scrollTo:0,   label:'back to top'} ],
  () => ({ y: Math.round(scrollY),
           open: document.body.classList.contains('is-open'),
           hidden: document.body.classList.contains('nav-hidden') })
)
```

Returns one row per step, so a regression shows up as a row that changed. Put
the resulting table in the spec — it is the acceptance criteria, already written,
and each row maps to an e2e assertion.

## Verification checklist

Run this before writing the spec. Report each line as pass / fail / not-verified.

- [ ] `__wf.env()` captured; `trustworthyForBehaviour` recorded with the results
- [ ] Geometry asserted in **every** state the surface has (at rest, changed, scrolled)
- [ ] Contrast computed for **every** new text-on-tint pairing
- [ ] `__wf.markup()` clean, or each finding explained
- [ ] `__wf.focusables()` shows nothing reachable-but-invisible
- [ ] Each behavioural rule has a `__wf.seq()` table
- [ ] Reduced-motion checked: all states still reachable with motion off
- [ ] Every variant screenshotted via `WF.compare()`, comparison closed afterwards
- [ ] Narrow viewport exercised if the surface has a responsive rule
- [ ] Feedback path live: `__wfFb.comment('#surface h2','probe')` → entry in
      `.feedback.jsonl`; `reply --to` it → thread panel within ~2s
      (`references/live-feedback.md`)

## Screenshots

Screenshot **states, not pages**. One image per decided state, taken from the URL
that encodes it (the overlay mirrors state into the hash), so it can be
regenerated later. A screenshot of the default state proves nothing that a
description would not.
