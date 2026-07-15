# Interpreting `analysis.json` & the runtime-Babel prototype anatomy

`scripts/analyze_prototype.py` inventories the prototype so you skip the rote reading. This explains
the manifest, what a claude.ai "omelette" prototype is made of, and the judgment calls the script
can't make for you.

## What a runtime-Babel prototype looks like

These sites have **no build step**. A representative `index.html`:

```html
<script src="https://unpkg.com/react@18.3.1/umd/react.development.js"></script>
<script src="https://unpkg.com/react-dom@18.3.1/umd/react-dom.development.js"></script>
<script src="https://unpkg.com/@babel/standalone@7/babel.min.js"></script>
<script src="_ds/protec-design-system-<id>/_ds_bundle.js"></script>   <!-- design system → window.* -->
<script src="image-slot.js"></script>                                 <!-- <image-slot> custom element -->
<script src="site/enhance.js"></script>                               <!-- motion/atmosphere layer -->
<div id="root"></div>
<script type="text/babel" src="tweaks-panel.jsx"></script>            <!-- authoring edit-mode -->
<script type="text/babel" src="site/shared.jsx"></script>            <!-- shared page chrome -->
<script type="text/babel" src="site/home.jsx"></script>              <!-- the page → window.ProTecHome -->
<script type="text/babel">
  const TWEAK_DEFAULTS = /*EDITMODE-BEGIN*/{ "accent":"cool", "heroLayout":"overlay" }/*EDITMODE-END*/;
  function App(){ const [t,setTweak]=useTweaks(TWEAK_DEFAULTS);
    return <><window.ProTecHome {...t}/><TweaksPanel>…</TweaksPanel></>; }
  ReactDOM.createRoot(document.getElementById('root')).render(<App/>);
</script>
```

Everything is transpiled in the browser by `@babel/standalone` at load. **Don't try to "run" it — read
it.** The content you must make editable is the string/JSX literals inside `site/*.jsx`.

## Shape of the manifest

```jsonc
{
  "runtime": "react-babel-standalone",     // confirms the in-browser-Babel pattern
  "source_dir": "…/site",
  "html_entries": ["index.html","services.html","commercial.html","book.html"],
  "pages": [
    { "id": "home", "jsx": "site/home.jsx", "window_export": "ProTecHome",
      "mounted_by": "index.html", "props_from_tweaks": ["accent","heroPhoto","heroTone","heroLayout"] },
    …
  ],
  "design_system": {
    "id": "protec-design-system-<uuid>", "dir": "_ds/protec-design-system-<uuid>",
    "bundle": "_ds/.../_ds_bundle.js", "manifest": "_ds/.../_ds_manifest.json",
    "window_namespace": "ProTecDesignSystem_37762d",
    "tokens": ["_ds/.../tokens/colors.css","…/typography.css","…/spacing.css","…/effects.css","…/fonts.css"],
    "styles_entry": "_ds/.../styles.css",
    "components": [ {"name":"Button","props":["variant","size","icon"]}, {"name":"Card"}, … ]
  },
  "shared_components": ["Header","Footer","SectionEyebrow", …],   // from site/shared.jsx
  "image_slots": { "custom_element": "image-slot.js", "uses": 7 },
  "tweaks": {
    "panel": "tweaks-panel.jsx",
    "defaults": { "accent":"cool", "heroPhoto":"tech_smile", "heroTone":"light", "heroLayout":"overlay" },
    "controls": [ {"key":"accent","kind":"radio","options":["flame","cool"]}, … ]
  },
  "fonts": ["https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:…","…Source+Code+Pro…"],
  "content_candidates": [
    { "page":"home", "path":"hero.headline", "text":"Comfort, engineered right." },
    { "page":"home", "path":"hero.sub", "text":"Fast repairs, honest installs…" },
    { "page":"home", "path":"services[0].title", "text":"Repairs" },
    { "page":"home", "kind":"image", "slot":"hero", "hint":"tech_smile" },
    …
  ]
}
```

### The lists to act on

- **`pages`** — one Next.js route each (per `--pages`). `window_export` is the component the HTML mounts
  (`window.ProTecHome`); `props_from_tweaks` are the knobs the page currently takes — candidates for Tina
  fields (`content-modeling.md`).
- **`design_system.components`** — the library to port in Phase 5 (Wave 1–2). Names come from the
  `_ds_manifest.json` and the `window.<namespace>.*` exports in `_ds_bundle.js`.
- **`shared_components`** — `Header`/`Footer`/eyebrow from `site/shared.jsx`; port as the app shell.
- **`content_candidates`** — **the most important list.** Every hardcoded string/image the analyzer found
  in the JSX. This becomes your editable-fields inventory and your Tina schema. The analyzer is generous
  (it flags all literals); *you* decide which are real content (headline, copy, phone, list items, image
  slots) vs. structural/throwaway (aria labels, class names, icon names). Confirm the set in Phase 2.
- **`tweaks`** — the `EDITMODE-BEGIN/END` defaults + panel controls. The starter's edit-mode is
  authoring-only (postMessage → the harness rewrites the block on disk); it does **not** work in
  production. Map the knobs worth keeping (accent color, hero layout) to Tina fields; drop the rest.

## Roles, and what to do with each

| Thing | Meaning | Action |
|------|---------|--------|
| `_ds/<id>/tokens/*.css` | design tokens (colors/type/spacing/effects/fonts) | Phase 4: copy + generate Tailwind `@theme` |
| `_ds/<id>/_ds_bundle.js` | compiled design-system components (`window.<ns>.*`) | Phase 5: port each named component (read the manifest for the list) |
| `_ds/<id>/_ds_manifest.json` | the component index + props | Phase 5: the inventory to port |
| `site/*.jsx` | page components (content baked in) | Phase 5 port + Phase 6 externalize content |
| `site/shared.jsx` | header/footer/eyebrow chrome | Phase 5: the app-shell/layout |
| `site/enhance.js` | scroll-reveal / hero motion (plain JS) | Phase 4: re-express as a client effect or CSS |
| `image-slot.js` + `<image-slot>` | image placeholder/upload custom element | Phase 6: `next/image` bound to a Tina `image` field |
| `tweaks-panel.jsx` + `EDITMODE` block | authoring-time edit mode | Phase 6: map worth-keeping knobs → Tina fields; do NOT ship the panel |
| `*.html` (non-index) | per-route harness entries | read for the route→page map; don't ship as-is |

## Reading the source after the manifest

The manifest is inventory, not understanding. Before porting, open and skim:
- **The token sheets + `styles.css`** — the color roles (`--flame-500`, `--ink-700`, `--cool-400`), the
  type scale, the `[data-*]` theming if any, and non-token CSS (keyframes, base rules).
- **One or two page JSX files** — how the design-system components compose, what props pages pass, where
  the copy lives (inline strings vs. arrays of `{title, body}` objects — the latter map cleanly to Tina
  `object` lists), and what page-local components exist.
- **`tweaks-panel.jsx`** — the `useTweaks` contract and which knobs are real design choices.

## Gotchas

- **In-browser Babel means no bundler config to copy** — you're reading intent, not reusing a toolchain.
- **Globals via `window`**: page components reference the design system as `window.<ns>.Button` and each
  other as `window.ProTecHome`. Replace with real ESM imports when porting (`component-porting.md`).
- **Icons**: `data-lucide="wind"` resolved by a global pass, or a `<Icon name>` from the bundle → switch
  to `lucide-react`, keep the name string as the prop.
- **The 4.5MB `ProTech Home.html`** and similar giant single-file HTML are *rendered snapshots* — reference
  them as visual ground truth; never ship or parse them as source.
