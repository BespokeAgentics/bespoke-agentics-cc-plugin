# Interpreting `analysis.json`

`scripts/analyze_zip.py` produces a manifest so you skip the rote inventory. This
explains how to read it and the judgment calls it can't make for you.

## Shape of the manifest

```jsonc
{
  "source_framework": "react-jsx",          // react-jsx | react-tsx | svelte | vue | html | ...
  "counts": { "primitives": 1, "page": 8, "tokens": 1, "asset": 4, ... },
  "files_by_role": { "page": ["src/pages/report.jsx", ...], "tokens": [...], ... },
  "tokens": {
    "files": ["styles/tokens.css"],
    "themes": ["dark", "light"],            // from [data-theme="…"] selectors
    "fonts": ["https://fonts.googleapis.com/css2?family=…"],
    "total_variables": 180,
    "scopes": { ":root": {…}, "[data-theme=\"dark\"]": {…}, "[data-theme=\"light\"]": {…} }
  },
  "components": [
    { "name": "Button", "file": "src/primitives.jsx", "exported": true,
      "window_member": true, "public": true, "screen": false, "kind": "primitive",
      "props": [ {"name":"variant","default":"'primary'","type":"string"}, … ] },
    …
  ],
  "component_count": 67,

  // The CURATED lists to ACT on — the analyzer already did the judgment:
  "recommended_library_components": ["Button","Badge","Card", … "Shell","TopBar"],
  "promotion_candidates": ["Input","Textarea","Field","KPI", …],
  "screens": ["AssessmentList","Wizard","ReportPage", …],
  "source_uses_react_aria": false,

  "pages": [...], "composites": [...], "assets": [...], "screenshots": [...]
}
```

### The curated lists (use these — don't re-derive)

The analyzer separates the public library from the screens for you, so Phase 2 is
*confirm the list*, not *read source and judge*:

- **`recommended_library_components`** — the public, non-screen components + layout
  composites. This is your library. `kind` on each component is `primitive` /
  `composite` / `screen` / `local`; `public` is true when the name is a
  `window`-export member (the strongest signal — the prototype's own export list) or is
  otherwise exported. `window_member` over `exported` is what fixes the old over-report
  where `export function FooPage()` looked "public."
- **`promotion_candidates`** — page-local components that *look* reusable (form/metric
  controls by name). Confirm which to promote into the library; leave the rest in pages.
- **`screens`** — rebuild these as page stories, not library components (Phase 6).
- **`source_uses_react_aria`** — almost always `false` for claude.ai exports. When
  false and `--library untitled-ui-react`, author in the *adapted* UUI idiom (token
  mapping + `sortCx`/`cx`, no forced React Aria) — see `targets/untitled-ui-react.md`.

Present `recommended_library_components` + the promotions you'd accept in the Phase 2
plan for the user to veto.

## Roles, and what to do with each

| Role | Meaning | Action |
|------|---------|--------|
| `tokens` | CSS sheet (≥8 custom props) or token JSON | Phase 4: copy verbatim + run `tokens_to_tailwind.py`. |
| `primitives` | File(s) defining the core components | Phase 5: port each to a library component. |
| `composite` | Shell / sidebar / topbar / panels | Phase 6: port as layout components. |
| `page` | A composed screen | Phase 6: rebuild as a full-viewport story. |
| `data` | Mock/fixture data | Phase 6: move into the Storybook app / `fixtures`. |
| `entry` | `app.jsx` / router | Read for the route→page map; don't ship the router as-is. |
| `asset` | svg/png logos, icons | Copy into the package. |
| `screenshot` | Reference PNGs | **Don't ship.** Use as visual ground truth while porting. |
| `html` | Standalone html entry | Usually the prototype harness; read for `<script>`/font wiring, don't ship. |

## Library vs page-local (the analyzer now recommends; you confirm)

The analyzer emits `recommended_library_components`, `promotion_candidates`, and
`screens` (above), so most of this judgment is done. The reasoning it applies — useful
to understand when you sanity-check its list:

- **Promote** page-local components that are clearly reusable: form controls
  (`Input`, `Textarea`, `Toggle`, `Seg`/segmented, `Field`), metric/stat tiles
  (`KPI`, `StatCell`, `MiniCard`), tabs, rows. If two pages use it, it's a library
  component.
- **Keep in the page** the genuinely one-off pieces: a bespoke Gantt, a risk heatmap,
  a page-specific hero. Porting these into the page's story is fine; they don't earn
  a public API.
- **Drop** non-components the regex may catch: the `App` root, route-splash wrappers.

Write the final library list into your Phase 2 plan so the user can veto.

## Reading the source after the manifest

The manifest is inventory, not understanding. Before porting, open and skim:

- **The token sheet** — confirm the theme model (default theme, how `[data-theme]`
  overrides work), the type scale, and any non-token CSS (keyframes like `shimmer`,
  `pulse`; base element styles) you'll need to carry into a global stylesheet.
- **The primitives file** — learn the idioms: are styles inline objects referencing
  `var(--…)`? How is hover/press done (local `useState`)? What's the icon system
  (`<i data-lucide="x">` + a `lucide.createIcons()` pass is common)?
- **One or two pages** — see how primitives compose, what props pages pass, and what
  page-local components exist. This is where you discover promotions.

If `source_framework` differs from `--framework` (e.g. source is `react-jsx`, target
is `svelte`), you're doing a cross-framework port — the inventory + props still apply,
but logic is rewritten per `references/targets/<framework>.md`.

## Gotchas

- **Icon system**: claude.ai exports frequently use Lucide via `data-lucide` attributes
  resolved by a global script. In a real library, switch to `lucide-react` (or the
  target's icon package) and pass icon *names* through as props — see
  `component-conversion.md`.
- **Globals via `window`**: source components talk to each other through `window.*`
  (e.g. `window.FINDINGS`). Replace with real imports/props when porting.
- **In-browser Babel**: the prototype has no build. Don't try to "run" it; read it.
