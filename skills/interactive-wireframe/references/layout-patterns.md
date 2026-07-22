# Layout patterns — the defects a wireframe catches

Read during Phase 2 when the surface involves sticky/scroll behaviour,
disclosure, or clickable rows carrying actions.

Each of these was a real bug found by building a wireframe rather than reasoning
about one. They are worth knowing in advance because each has a cheap structural
fix and an expensive debugging session.

---

## 1. Multiple sources of truth for one offset

**Symptom.** Bands that should be flush show a gap — sometimes. Page content
bleeds through the seam. Usually invisible at the top of the page.

**Cause.** A `fixed` element + an in-flow spacer + `sticky` rows whose `top`
comes from a JS-measured height is **three sources of truth for one number**.
They disagree the moment any of them changes: a font loads, a label wraps, a
banner appears.

**Fix — one sticky element, hidden by transform.**

```css
.stack { position: sticky; top: 0; z-index: 40;
         transition: transform 220ms cubic-bezier(.165,.84,.44,1) }
body.nav-hidden .stack { transform: translateY(calc(-1 * var(--band-1-h))); }
```

`transform` is not layout: zero reflow, the document height never changes, and
the bands are siblings in one box so they physically cannot separate.

**The constraint this creates:** every band inside the stack needs an **explicit
height token**, because the hide distance is computed from those tokens. A band
whose content sets its own height desyncs the translate from reality and
reintroduces the gap. Fixed tokens, never measured.

**Assert it:** `__wf.bands([...])` in both states — `contiguous: true` in each.

---

## 2. Scroll anchoring fights your scroll handler

**Symptom.** "The toggle stopped working." Expanding a panel closes it again
immediately — but only when the page is already scrolled, so it looks
intermittent and unreproducible at the top.

**Cause.** Expanding inserts content **above** the viewport. The browser's scroll
anchoring compensates by scrolling down the same amount to hold content still.
A handler comparing `scrollY` against a baseline reads that synthetic jump as a
real user scroll of ~400px and fires whatever that was meant to trigger.

**Fix — synchronous re-baselining.** An rAF or `setTimeout` baseline drifts
whenever frames are throttled, and frames are always throttled in a backgrounded
automation tab.

```js
function toggle(next) {
  S.open = next;
  render();
  void document.documentElement.scrollHeight;  // force layout: anchoring resolves NOW
  S.openedAtY = scrollY;                       // baseline where anchoring actually left us
  lastH = document.documentElement.scrollHeight;
}
// and on every scroll, absorb any height delta into the baseline
function absorbLayoutShift() {
  const h = document.documentElement.scrollHeight;
  if (h !== lastH) { S.openedAtY += h - lastH; lastH = h; }
}
```

The scaffold ships both as `WF.rebaseline(key)` and `WF.absorbLayoutShift(key)`.

**The alternative that sidesteps it entirely:** take the panel out of flow
(`position:absolute` overlay). Nothing shifts, so there is nothing to anchor —
at the cost of covering content. Worth shipping as a `variant` and letting the
user choose while scrolled.

---

## 3. A `<button>` cannot contain interactive children

**Symptom.** A row is clickable *and* carries buttons. In a mockup it works; in
real code the nested control has to become an inert `<span>` that no keyboard
user can reach.

**Cause.** `<button>` and `<a>` may not contain interactive descendants. This is
not a lint preference — the browser's own parsing and the accessibility tree
both break.

**Fix — the trigger is a sibling, not the wrapper.**

```html
<div class="row">                                   <!-- container, not a control -->
  <button class="row-toggle" aria-expanded="false" aria-controls="panel">
    identity · summary                              <!-- the disclosure surface -->
  </button>
  <div class="row-actions">
    <button>Edit</button><button class="primary">Approve</button>
  </div>
</div>
```

**Assert it:** `__wf.markup().nestedInteractive` is `[]`, both controls are real
`<button>`s, and clicking an action does not toggle the disclosure (a real
`stopPropagation` test, not an assumption).

---

## 4. Hidden-by-transform content stays tabbable

**Symptom.** Tabbing walks focus onto controls that are off-screen. Worse when
the hidden thing only returns under a condition the keyboard user cannot trigger
(e.g. "the nav returns only at scrollTop 0").

**Cause.** `transform`, `clip`, and negative offsets move things visually.
`display:none` / `visibility:hidden` / `inert` remove them from the tab order —
transform does not.

**Fix — reveal on focus.**

```js
[bandEl, crumbEl].forEach(el =>
  el.addEventListener('focusin', () => { if (S.hidden) { S.hidden = false; render(); } }));
```

**Assert it:** `__wf.focusables('#surface').offScreen` is empty, and
`__wf.focusIn('#hidden-band')` reveals the stack. (`element.focus()` is a no-op
in an unfocused document — dispatch the event.)

---

## 5. A pseudo-element painting over a positioned child

**Symptom.** A value inside a ring, gauge, or badge is invisible even though it
is in the DOM and the colour is right.

**Cause.** `::after` used as an inner disc paints **after** an unpositioned
sibling in the same stacking context.

**Fix.** Give the content `position:relative; z-index:1`, or draw the ring with
a border/gradient that leaves the centre unpainted.

---

## 6. Class-name collisions between chrome and utilities

**Symptom.** An unrelated inner element becomes sticky, or inherits spacing it
should not.

**Cause.** A generic utility name (`.stack`, `.row`, `.panel`, `.card`) used for
both a structural component and a layout utility.

**Fix.** Namespace structural classes distinctly (`.hstack` for the header
stack). Cheap to do, extremely annoying to debug.

---

## 7. Grid and flex children that refuse to shrink

**Symptom.** A panel overflows its container; ellipsis truncation never engages.

**Cause.** Flex and grid items default to `min-width:auto` — they will not shrink
below their content's intrinsic width.

**Fix.** `min-width: 0` on the shrinkable child (and `min-height: 0` in a column
layout) alongside `overflow:hidden; text-overflow:ellipsis; white-space:nowrap`.

---

## 8. Controls that disagree with the thing they control

**Symptom.** The overlay says stage 3; the surface renders stage 1. Touching any
control snaps it into agreement — which makes it look like a rendering bug.

**Cause.** State is applied on *change* but never on *init*.

**Fix.** Render from state once at mount. The scaffold does this in `WF.mount()`;
if you add controls outside it, do the same.

---

## 9. Priority-drop, not reflow, for narrow viewports

When a dense row must survive narrow widths, decide the **drop order** explicitly
and keep everything dropped available elsewhere (in the expanded panel, a menu, a
detail view). Write it as a ladder in the spec — it is directly testable:

```
1440   ⌄ Name [TYPE] ●─●─◐ Stage   │ Ref │ Score │ ⚑ owner │ [Edit] [Primary]
1180   ⌄ Name [TYPE] ●─●─◐ Stage   │ Score │ ⚑ owner │ [Primary]
 900   ⌄ Name [TYPE] ●─●─◐         │ ⚑ owner │ [Primary]
 600   ⌄ Name       │ ●●◐          │ [Primary]
```

Name what always survives (identity, ownership, the primary action) — that is the
real decision; the rest follows.

---

## 10. Reduced motion must keep every state reachable

```css
@media (prefers-reduced-motion: reduce) {
  .stack, .chevron, .panel { transition: none }
}
```

The behaviour still happens — it just happens instantly. A reduced-motion mode
that *removes* a state (rather than removing its animation) is a functional
regression, and it is easy to ship by accident when the animation was doing the
revealing.
