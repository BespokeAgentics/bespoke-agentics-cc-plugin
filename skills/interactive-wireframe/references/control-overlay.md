# Control overlay — spec and axis catalogue

Read before Phase 2. The overlay is what makes this a wireframe you *interrogate*
rather than one you look at.

## What it is for

Every control replaces a question you would otherwise have to ask in prose.

> "What does an engineer see when the record is owned by someone else and they
> only have read access?"

as a paragraph, that is three assumptions and a guess. As three controls, it is
a state the user can *look at* — and they will immediately tell you the answer is
wrong, which is the point. People are far better at critiquing something concrete
than at answering a hypothetical.

So the overlay is not a debug panel. It is the interview instrument.

## Deriving the axes

The overlay is generated from the axes **this surface actually varies on** — not
a fixed panel copied between projects. Interrogate the surface:

1. **Who is looking?** Roles, personas, permission flags, auth states, plan
   tiers, internal-vs-customer. → one `select` + the flags as `toggle`s.
2. **What state can the thing be in?** Every enum the surface displays: status,
   stage, lifecycle, review outcome, sync state. → one `select` per enum.
3. **What can go wrong?** Error, rejected, expired, conflicted, offline,
   partially-loaded. → `toggle`s. These are the states designs forget and
   production hits daily.
4. **What are the data extremes?** Empty · exactly one · many · overflowing ·
   longest-real-string · missing optional field. → a `select` of fixtures.
   Layout breaks at the extremes, never at the happy path.
5. **What numbers drive behaviour?** Scroll thresholds, debounce, truncation
   limits, page size, breakpoint. → `number`. Making a threshold draggable turns
   "does 80px feel right?" into ten seconds of scrolling.
6. **What is genuinely undecided?** Competing layouts, placements, treatments.
   → `variant`. Ship the argument as a switch instead of arguing.
7. **What helps you see structure?** Zone guides, layout mode
   (push vs overlay), reduced motion, theme. → `bodyclass`.
8. **What is configurable per install?** A mapping the customer controls
   (stage → owning role, field visibility per plan). → `matrix`.

Two tests before an axis earns a slot:

- **Does it change something visible?** A control that does nothing teaches the
  user that controls do nothing, and they stop touching them.
- **Will anyone actually touch it?** Aim for **6–12 axes**. Past that the panel
  becomes a settings screen and the important ones get lost. Group with
  `divider`, explain with `note`.

## Axis types

Provided by `assets/wireframe-scaffold.html` via `WF.mount({axes, render})`.

| Type | Shape | Use for |
|---|---|---|
| `select` | `{id, label, type, value, options:[{value,label}], from}` | Roles, enums, fixtures |
| `toggle` | `{id, label, type, value}` | Permission flags, error states |
| `number` | `{id, label, type, value, min, step}` | Thresholds, counts, widths |
| `variant` | `{id, label, type, value, options}` | Competing layouts — applies an **exclusive body class** |
| `bodyclass` | `{id, label, type, bodyClass, value}` | Guides, push/overlay, theme |
| `matrix` | `{id, label, type, rows:[{id,label,value}], options}` | Per-row configurable mapping |
| `action` | `{label, type, run(S, update)}` | Scroll to top, reset, open comparison |
| `divider` / `note` | `{type}` / `{type, text}` | Grouping and explanation |

`from:` renders as a small provenance line under the control — it is how a
reviewer sees at a glance that the options are the product's real values.

```js
WF.mount({
  axes: [
    { id:'role', label:'Viewing as', type:'select', value:'staff',
      options:[{value:'staff',label:'Staff'},{value:'customer',label:'Customer'}],
      from:'src/lib/auth/roles.ts:14' },
    { id:'status', label:'Order status', type:'select',
      options:[/* verbatim from the label map */], from:'src/lib/orders.ts:31' },
    { id:'canEdit', label:'Viewer can edit', type:'toggle', value:true },
    { id:'rows', label:'Rows in list', type:'number', value:12, min:0, step:1 },
    { type:'divider' },
    { id:'layout', label:'Action placement', type:'variant', value:'v-inline',
      options:[{value:'v-inline',label:'A · inline'},{value:'v-menu',label:'B · overflow menu'}] },
    { id:'guides', label:'Show zone guides', type:'bodyclass', bodyClass:'wf-guides' },
    { label:'Compare placements', type:'action',
      run:() => WF.compare('#row', ['v-inline','v-menu']) },
  ],
  render(S) { /* single function: read S, write the DOM */ },
});
```

## Wiring contract

- **One `render(S)`.** Every control change calls it; it reads state and writes
  the DOM. Resist per-control handlers that mutate the DOM directly — that is
  how a wireframe ends up with states reachable by one route and not another.
- **Render from state at init too.** The scaffold calls `render` on mount. A
  panel that only updates on *change* shows a default that disagrees with the
  DOM until you touch something — which reads as a layout bug that isn't one.
- **State lives in `S`, nowhere else.** The URL hash mirrors it automatically, so
  any configuration is a link you can paste, screenshot, and re-verify.
- **Keep the overlay out of the surface's own stacking context** — it ships at
  `z-index:9000`. If the surface needs more, it is worth asking why.

## Variant CSS — the rule that is not a preference

Scope variant styles to `.v-name`, **never** `body.v-name`:

```css
.v-inline .row-actions { display:flex }          /* ✅ works cloned */
body.v-menu .row-actions { display:none }        /* ❌ dead in comparison */
```

`WF.compare()` clones the surface into `<div class="v-name">` wrappers, so a
body-scoped rule never matches the clone. The symptom is every panel rendering
identically — which the user reads as "these options look the same," not "the
harness is broken." `WF.compare()` also suspends the live variant class on
`<body>` for the duration, because otherwise it matches every clone at equal
specificity and wins on source order.

## The comparison sheet

When a decision is aesthetic, stop arguing and render the options side by side:

```js
WF.compare('#header', [
  {value:'v-a', label:'A · scale'},
  {value:'v-b', label:'B · tinted band'},
  {value:'v-c', label:'C · eyebrow'},
]);
// … screenshot once …
WF.closeCompare();
```

One screenshot of three real variants ends the discussion faster than three
paragraphs, and it routinely exposes that two of them are visually identical.
