# Design rules

Read this before writing markup. These rules are the shipped MicroDots /
BespokeAgentics brand, not preferences. Where the project has its own theme
package (`packages/*theme*/src/tokens.css`) or a style-guide wiki page, read
them first and let the project win on any token value; the rules below still
bind on everything else.

## Type

Two faces, no third. **DM Sans** for prose and headings, **DM Mono** for anything
a machine produced. Caveat appears only as the editorial accent.

| Role        | Size                       | Weight  | Tracking               |
| ----------- | -------------------------- | ------- | ---------------------- |
| Hero H1     | `clamp(30px, 5vw, 52px)`   | 800     | −0.03em                |
| Section H2  | `clamp(26px, 3.6vw, 40px)` | 700–800 | −0.02em                |
| Card title  | 15–17px                    | 500     | −0.01em                |
| Body        | `--fs-body-m` (14.1px)     | **300** | normal                 |
| Lede / deck | 16–17px                    | 300     | normal                 |
| Eyebrow     | 10.5–11px mono             | 400     | 0.12–0.14em, uppercase |
| Panel label | 10px mono                  | 500     | 0.1em, uppercase       |
| Metadata    | 9.5–10px mono              | 400     | 0.1–0.12em, uppercase  |

Rules that get broken most:

- **Body is light (300). Never bold body prose.** 400 for UI labels, 500 for
  buttons and card titles, 700–800 only for display headings.
- **Sentence case everywhere.** Uppercase is reserved for mono labels.
- **Measure in `ch`, never px.** 20–22ch display headings, 46–56ch ledes,
  62–74ch body columns, 82–88ch for a full-width callout.
- `text-wrap: pretty` on paragraphs, `balance` on headings.
- **One eyebrow per section, never stacked.** `--accent` for a section head,
  `--text-muted` for a panel header.
- **Long mono strings truncate; they never wrap mid-token.** `overflow: hidden`
  - `text-overflow: ellipsis` + `white-space: nowrap`.
- `--text-muted` is 9–11px metadata only. It is never a sentence.
- Mono floor is 9px.

## Panels

1px border, `--surface-default` body, 10–14px radius, `overflow: hidden`.
Header strip on `--surface-raised`, 30–44px tall, closed by a `--border-subtle`
rule, mono label left and mono status right. Body padding 12–24px.
**A child's radius stays at least 2px below its parent's.**

On a `.band--alt` band, bump panel surfaces one step (`--surface-raised` body,
`--surface-elevated` head) so they still read against the band.

## Status

A 4–9px dot, a mono word, or a 5–10% row wash with a 15–30% border.
**Never a filled block. Blue is not a status.**

The selected-row treatment is three coordinated changes at once: border to
`--border-accent`, background to `--interactive-subtle`, mono id to `--accent`.

**Dashed border means "not real yet"** — gated, speculative, unbuilt. Keep the
convention; it is how the page under-claims rather than over-claims.

## Depth

**Rest has no shadow.** Emphasis is a border shift to `--border-accent` plus
`--shadow-glow`. Only two real shadows exist on a page: the nav's after-scroll
shadow, and `--shadow-cta` under a primary button. Hover never moves an element —
a primary button answers hover by deepening its shadow, nothing else.

## Motion

`--ease-standard` everywhere. 0.2s interactive · 0.25–0.3s panel and card ·
0.4s scroll reveals.

Reveals are `opacity 0→1` plus `translateY(10px)→none` over 0.4s, triggered at
70px above the fold, **one-shot — no stagger, no re-trigger**. **Above the fold
never animates in**: the hero carries no `[data-reveal]`.

**At most one loop on a resting page**, and zero is fine. No bounce, no spring,
no shrink-on-press, no glowing box-shadow keyframes, no pulsing.

## Layout

The one responsive primitive:

```css
grid-template-columns: repeat(auto-fit, minmax(min(Npx, 100%), 1fr));
```

The `min()` is not optional — a bare `minmax(440px, 1fr)` pushes 65px of
horizontal scroll onto a 375px screen. **The 880px nav disclosure is the only
width media query permitted on the page.**

Bands alternate `--surface-page` / `--surface-default`, never two of the same in
a row, each closed by its own 1px `--border-subtle` rule. 104px vertical padding,
1200px max width, `--sp-8` gutters.

Overflow protection: `min-width: 0` on every grid and flex child,
`overflow-wrap: break-word` on the body, wide tables inside an
`overflow-x: auto` container. **Never `display: flex` on an `<li>` for a marker
character — position the marker absolutely.**

## Iconography

24×24 viewBox, 1.5px stroke, round caps and joins, `currentColor`. Lucide idiom.
Rendered at 14–17px. No icon fonts, no emoji.

## Code samples

Hand-span the tokens; do not load a highlighter. **Never a syntax-highlighter
rainbow** — five colours, by role:

| Role                          | Colour             |
| ----------------------------- | ------------------ |
| element / schema / event name | `--accent`         |
| attribute name                | `--accent-subtle`  |
| value                         | `--text-primary`   |
| punctuation, keys             | `--text-secondary` |
| version, comment              | `--text-muted`     |

## Correctness notes

These have each shipped a real bug.

1. **Always set `color` AND `font-family` on a `<button>`.** Browsers default
   `color` to `buttontext` and `inherit` does not apply. Several clickable rows
   shipped black-on-navy before this was caught.
2. **Source order is the theme switch.** `:root` and `[data-theme='dark']` are
   both specificity (0,1,0). Put dark above light and the toggle silently stops
   working one way.
3. **The blocking `<script>` in `<head>` is required.** Without it the page
   paints the served theme, then flips.
4. **Never define a page-level `.node` class.** Mermaid uses `.node` internally
   on SVG `<g>` elements with `transform: translate(…)`; a page-level rule
   leaks in and breaks the layout. Scope any Mermaid styling under `.mermaid`.
5. **Mermaid line breaks are `<br/>` inside quoted labels**, never `\n` — the
   escape renders as literal text.
6. **Prefer `flowchart TD`.** `LR` spreads horizontally and makes labels
   unreadable past four nodes.
   6b. **Do not remove the two `.mermaid` label rules in `components.css`, and do
   not drop `flowchart:` or the `document.fonts.ready` await from the shell.**
   All four exist because mermaid sizes a node from a measurement taken before
   DM Sans loads, in a detached div this page then restyles — and
   `tokens.css`'s `p { text-wrap: pretty }` leaks into mermaid's own `<p>`,
   resetting `text-wrap-mode` to `wrap` and defeating the `nowrap` mermaid
   relies on. The failure is **silent**: the diagram renders, so it looks
   finished, but every label is cut at its first space and the widest line
   loses its last glyph. "Locked catalog snapshot" paints as "Locked",
   "catalog-gap" as "catalog-". Always read a rendered diagram back before
   shipping — the DOM holds the full string, so only pixels reveal it.
7. Control heights: nav and toolbar 30–36px, primary buttons 38–46px, touch
   targets 44px. Below 880px the nav sheet's rows go to 44px.
8. **The mobile nav sheet is opaque (`--surface-raised`), never blurred.** A
   `backdrop-filter` on it renders **no blur at all**, because `.nav__inner` is
   already a backdrop root. Worse, the contrast sweep _passed_ the blurred
   version at 8.58:1 by compositing declared token colours over a surface that
   was actually hero artwork — a false pass in the one instrument trusted to be
   objective, caught only by looking at a screenshot. Opaque measures 8.07:1
   dark / 8.19:1 light.
9. **The anchor offset is 72px, not "whatever clears the nav".** 14px top +
   58px capsule = 72, and the capsule's geometry was chosen to preserve the
   offset every anchored band already carried.

## Pre-flight checklist

- [ ] Dark block below light block; page tested in **both** themes.
- [ ] Toggle persists to `md-theme` and survives reload.
- [ ] Mermaid re-renders on toggle and keeps zoom and pan.
- [ ] Every machine value is mono; no prose is mono.
- [ ] No accent on more than two things in one panel.
- [ ] No shadow at rest anywhere except the nav after scroll.
- [ ] Hero has no `[data-reveal]`.
- [ ] At most one loop on the resting page.
- [ ] Every grid uses `minmax(min(Npx, 100%), 1fr)`; only one media query.
- [ ] No horizontal scroll on the body at 320px.
- [ ] At most four editorial hues, one word each.
- [ ] No emoji.
- [ ] Every number on the page traces to a command run or a `file:line` read.
