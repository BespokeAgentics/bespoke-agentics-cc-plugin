# Gallery scaffold — anatomy, scoping, measurement, sync obligation

Read before Phase 3 (build). The gallery is one self-contained HTML file derived
from the parent skill's wireframe scaffold; this file explains what is different
and which rules keep its measurements honest.

## Why a derived scaffold, not the parent's

The parent's `variant` axis is an exclusive **body class over one shared markup
tree** — it can express a Restyle and nothing else. Restructure and Rethink
variants have *different DOM*, so the gallery renders each variant as a **real
sibling pane** and switches/arranges panes instead of toggling classes. That is
the one structural divergence; everything else is inherited.

## The four REPLACE regions

| Region | What goes in it | The rule that matters |
|---|---|---|
| 1 — TOKENS | One shared `:root`, real values, path-cited | ONE block for all variants. Brand-faithful means every pane draws from the same grounded palette; a variant that needs an ungrounded value is an interview question, not a new token. Derived values are computed from grounded ones (`color-mix()` etc.) and labelled `derived`. |
| 2 — VARIANT STYLES | One clearly-banded sub-block per variant | Scope to `.rv-<id>` (the pane class), never `body.…` — in grid view every pane renders at once, so a body-scoped rule bleeds into all of them. Intra-pane sub-options driven by a `variant` axis still scope to `.v-name` (the `WF.compare()` clone harness depends on it). |
| 3 — VARIANT PANES | One `<section id="rv-<id>" class="rv-pane rv-<id>" data-variant data-tier>` per variant inside `#rv-stage` | Current FIRST — manifest order is tab order. Real labels, longest-case strings, own `wf-zone`/`data-z` bands per pane. ids must be pane-unique across the whole file: hidden panes are still in the document, so a duplicated id breaks `aria-controls` and trips `__wf.markup().duplicateIds`. |
| 4 — MANIFEST + AXES + RENDER | `RV.mount({variants, axes, render})` | Axes are SHARED: they hit every pane at once. Flip "empty" and all variants answer simultaneously — the gallery's strongest interview move. |

The manifest entry shape: `{id, label, tier: current|restyle|restructure|rethink,
thesis, fidelity?, retired?}`. `fidelity` renders as a chip on the pane head
(used by the Current baseline — see `baseline.md`). `retired: true` keeps a
killed variant's record without a tab or cell — retire panes in v2 rather than
deleting their manifest entries, so the spec can cite what was rejected.

## The RV harness and `__rv`

`RV.mount` registers its state (`rv`, `view`, `split`) as ordinary WF axes, so
the control panel, URL hash, `WF.set()` and hash navigation all work unchanged.
A pasted URL like `#rv=restyle&view=split&split=current&empty=1` reproduces an
exact gallery configuration — use these as the "pane links" in the spec.

Automation drive points:

```js
__rv.show('restyle')             // single view, that pane active
__rv.mode('single'|'grid'|'split')
__rv.split('restyle','current')  // split view, A vs B
__rv.manifest()                  // declared variants, retired included
__rv.state()                     // {rv, view, split}
```

The switcher bar is docked **bottom-centre, not top**: a top-fixed bar would
overlay exactly the region most redesigns argue about (the header) and would
shift every measured band top.

## Measure in single view only

Grid and split shrink panes to fit and prepend cell heads, so geometry there is
for **looking, not for the spec**. In single view the heads are hidden, the
active pane starts at y=0, and the bar is fixed chrome outside the pane — bands
measure clean. Per-variant measurement is selector prefixing, no kit changes:

```js
__rv.show('restyle');            // then, in single view:
__wf.bands(['#rv-restyle .head', '#rv-restyle .body'])
__wf.contrast('#rv-restyle .row-muted')
__wf.focusables('#rv-restyle')
```

`__wf.markup()` is page-wide by design — attribute findings to a pane by the
returned snippet/id. Measure `contrast()` only on the pane currently shown:
computed styles on a `display:none` pane are not what a user sees.

All the parent's backgrounded-tab caveats apply verbatim (`__wf.env()` first;
scroll/rAF/transitions/`.focus()` silently no-op in a hidden tab — read the
parent's `references/browser-verification.md`).

## Sync obligation — this scaffold tracks the parent

Derived from `interactive-wireframe/assets/wireframe-scaffold.html` the way
wireframe-parity's `wf-probe.js` is: byte-faithful core, marked additions,
drift-checked. Specifically:

- **`WF` engine and `__wf` kit: verbatim.** Zero diff against the parent.
- **`__wfFb` kit: verbatim except two additions marked `RV:`** — `payload()`
  gains `variant: el.closest('.rv-pane')?.dataset.variant` (every browser
  comment self-attributes to a pane), and `isHarness()` covers the gallery
  chrome (`.rv-bar`, `.rv-cell-head`).
- **New and owned here:** the `RV` module, `__rv`, and the `rv-*` chrome CSS.

Drift check, run whenever the parent scaffold changes:

```bash
for f in <parent>/wireframe-scaffold.html <this>/reimagine-gallery.html; do
  sed -n '/const __wf = /,/window.__wf/p' "$f" \
    | grep -oE '^    (\w+)\(' | tr -d ' (' | sort | tr '\n' ' '; echo
done   # the two lines must be identical
```

If the parent's `__wf`/`WF`/`__wfFb` change, re-derive those sections here and
re-run the diff — a gallery measuring with a stale kit produces numbers that
disagree with wireframe-parity's, which reads as implementation drift when it
is tooling drift.
