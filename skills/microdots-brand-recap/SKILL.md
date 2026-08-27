---
name: microdots-brand-recap
description: Generates a self-contained HTML page in the BespokeAgentics / MicroDots brand — DM Sans + DM Mono, the shipped light/dark token palette, a floating nav capsule with a working theme toggle, and Mermaid diagrams re-themed from live tokens. Use whenever the user asks for a project recap, diff review, plan review, dashboard, report, audit, or any visual-explainer page "in the MicroDots brand", "BespokeAgentics style", or "MicroDots style" — and whenever they ask to restyle an existing visual-explainer page into that brand. This skill REPLACES the visual-explainer skill's aesthetic-selection step; its content workflow still applies.
---

# MicroDots brand recap

Produce a visual-explainer page in the BespokeAgentics / MicroDots brand instead
of picking a freeform aesthetic. The content workflow is unchanged — **the
design decision is already made and is not yours to re-open.**

## How this composes with visual-explainer

| visual-explainer step                                       | What happens here                                                                   |
| ----------------------------------------------------------- | ----------------------------------------------------------------------------------- |
| 1. Think — pick an aesthetic                                | **Skipped.** The brand is the aesthetic. Do not invent a palette or a font pairing. |
| 2. Structure — pick a rendering approach                    | Unchanged. Mermaid for topology, CSS grid for text-heavy cards, `<table>` for data. |
| 3. Style                                                    | **Replaced by this skill's assets.**                                                |
| 4. Deliver — write the file, open in browser                | Unchanged.                                                                          |

If the user invoked a visual-explainer command (`project-recap`, `diff-review`,
`plan-review`, …), follow that command's data-gathering and verification phases
exactly, then build the page from these assets. **The verification checkpoint
still binds: every number on the page must trace to a command you ran or a
`file:line` you read.**

## Build order

Asset paths below are relative to
`${CLAUDE_PLUGIN_ROOT}/skills/microdots-brand-recap/`.

1. **Copy `assets/shell.html` verbatim** as the starting file. It is a working
   page: blocking theme script, nav capsule, theme toggle, scroll-spy, nav
   disclosure, reveals, and the Mermaid zoom/pan module that re-themes on
   toggle. **Do not re-derive any of it.**
2. **Paste `assets/tokens.css` into the `<style>` block, first.** Light lives on
   `:root`; dark is `[data-theme='dark']` and **must stay below it** — every
   selector is specificity (0,1,0), so source order is the entire switch.
3. **Paste `assets/components.css` after it.** Panels, KPIs, status columns,
   tables, step lists, debt cards, callouts, collapsibles, Mermaid chrome.
4. **Read `references/design-rules.md` before writing any markup.** It carries
   the type scale, panel anatomy, motion budget, the correctness notes that have
   each shipped a real bug, and the pre-flight checklist.
5. Fill in bands. Alternate `band` / `band--alt`, each closed by its own 1px
   `--border-subtle` rule.
6. Write the file to the output location the invoking command specifies (default
   `~/.agent/diagrams/<name>.html`) and `open` it.

If the project ships its own theme package (`packages/*theme*/src/tokens.css`)
or a brand style-guide page, read it and let the project's token values win.
Everything else in these rules still binds.

## The rules you cannot break

1. **One accent, rationed.** If three things on a panel are blue, two are wrong.
   Blue marks what is live, selected, or interactive. **Blue is not a status.**
2. **Hairlines, not fills.** 1px borders and low-opacity washes. No zebra
   striping, no filled status blocks, no floodfill.
3. **Mono carries data.** Every machine-produced string — versions, hashes,
   ports, counts, paths, tags, statuses — is DM Mono. Prose is DM Sans 300.
   The two faces never blur into each other.
4. **Rest has no shadow.** Emphasis is a border shift to `--border-accent` plus
   `--shadow-glow`. Only two real shadows exist: the nav's after-scroll shadow
   and `--shadow-cta` under a primary button.
5. **Motion is confirmation.** `--ease-standard`, 0.2–0.4s. Reveals are one-shot
   with no stagger and never re-trigger. **Above the fold never animates in.**
   At most one loop on a resting page. No bounce, no spring, no shrink-on-press.
6. **No emoji, no photography, no gradient text.**

## The one responsive primitive

```css
grid-template-columns: repeat(auto-fit, minmax(min(340px, 100%), 1fr));
```

No media queries — the `min()` clamps the track floor to the container, so a
340px card never pushes horizontal scroll onto a 320px screen. **The nav
disclosure at 880px is the only permitted width query**, and it is already
written for you in the shell.

## The editorial accent

One Caveat word per section, underlined, at `1.24em` of its heading. At most
four hues on a page. Pick the emphatic word — the one the sentence turns on —
not a noun at random.

| Class       | Dark      | Light     |
| ----------- | --------- | --------- |
| `.ed--hero` | `#00F5A0` | `#008456` |
| `.ed--how`  | `#3D8BFF` | `#0368FF` |
| `.ed--wire` | `#00E0FF` | `#007F91` |
| `.ed--ent`  | `#B26BFF` | `#9A3CFF` |
| `.ed--rel`  | `#FF3B5C` | `#E80027` |
| `.ed--cta`  | `#FFB800` | `#966C00` |

All twelve clear 4.5:1 against their theme's page surface. **These hexes are
literals by design — never add them to the palette, never use them in product
UI.** The nav wordmark's five-dot band is the one place all six appear at once.

## Files

| Path                         | Use                                                                     |
| ---------------------------- | ----------------------------------------------------------------------- |
| `assets/shell.html`          | The whole working skeleton. Start here, always.                         |
| `assets/tokens.css`          | The token block, both themes. Paste first.                              |
| `assets/components.css`      | Panels, KPIs, status, tables, steps, debt, Mermaid.                     |
| `references/design-rules.md` | Type scale, panel anatomy, motion budget, correctness notes, checklist. |
