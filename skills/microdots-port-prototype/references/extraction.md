# Phases 1-2 -- Extraction and classification

## What a Claude Design artifact actually is

A Claude Design "standalone HTML" export is a self-unpacking bundle, not a build output.
Four `<script type="__bundler/*">` blocks carry everything:

| Block | Contents |
| --- | --- |
| `manifest` | `{ "<uuid>": { mime, compressed, data } }` -- every asset, base64, gzip when `compressed` |
| `template` | A JSON string: the real page shell, with `<script src="<uuid>">` tags and the full `<style>` blocks |
| `ext_resources` | External URLs the page pulls at runtime (usually `[]`) |
| `page_order` | Multi-page ordering when the export has more than one page (usually `[]`) |

The decisive property: **the app source is not minified**. Claude Design ships the
original hand-written, commented code inside the artifact. A 1.8 MB file that looks
opaque is a readable source tree behind one decode.

## The two export shapes

There are two shapes in the wild, and they put the app source in different places. The
extractor detects which and records it as `bundle_shape` in `index.json`; check it before
reasoning about the tree, because Phase 2 classification differs.

| Shape | How to recognize it | Where the app source lives | What Phase 2 gets |
| --- | --- | --- | --- |
| `babel-modules` | Many `<script type="text/babel" src="<uuid>">` tags | One manifest asset per module, in true load order | Many modules; roles are classifiable; `window.*` globals are the seam graph |
| `dc-runtime` | One inline `<script type="text/x-dc" data-dc-script>` | **Inline in the template** -- the manifest holds only the `dc-runtime` bundle, React, fonts and images | ONE module: `app/component.jsx`, a single `class Component extends DCLogic` |

For `dc-runtime` there is no module graph to classify. The seams come from inside the
component instead: its `state = { … }` object is the whole view model (`view`,
`centerTab`, … are the route/tab map), and the render tree's sections are the feature
domains. Classify **regions of the component**, not files, and cite `component.jsx:<line>`
ranges. Everything else in this skill is unchanged.

A shape the extractor does not recognize yields `bundle_shape: "unknown"`, zero app
modules and a warning on stderr. That is the degradation row: proceed only by treating
every module as `unclassified`, and say the confidence cost out loud.

## Running the extractor

    python3 scripts/extract_design_bundle.py <artifact.html|dir|zip> --check
    python3 scripts/extract_design_bundle.py <artifact.html|dir|zip> --out <dossier>/_src

Exit codes: `0` extracted · `2` not a Claude Design artifact (redirect, do not degrade) ·
`3` malformed (manifest present, template missing or unparseable).

Accepts a `.html` file, a `.zip`, or a directory (which must contain exactly one artifact
-- two or more and it lists them and stops rather than picking).

Output tree:

    _src/
      index.json              ordered module records: order, uuid, role, mime, path, bytes, sha256, declared_name, banner
      shell.html              the template, with every uuid src rewritten to its extracted path
      app/NN-<name>.jsx|.js   app source, NN = real load order
      app/entry.jsx           the inline bootstrap script (babel-modules shape)
      app/component.jsx       the whole app as one component (dc-runtime shape)
      vendor/<name>.js        React, Babel, Tailwind, dc-runtime, design-system bundles
      styles/style-NN.css     each <style> block, with its custom-property count
      assets/fonts/*.woff2    embedded fonts

## What the script guarantees, and what it refuses to guess

**Guaranteed, because the template declares it:**

- **Role.** The template's own script types declare it: `text/babel`, `text/jsx` and
  `text/x-dc` (or a `data-dc-script` attribute) are app source; a plain `<script src>` is
  a vendor library. Read off the template, never inferred from size or content.
- **Load order.** Script-tag order is dependency order -- these modules share state
  through `window`, so order is the only import graph that exists.
- **Design tokens.** `styles/` carries the real CSS with its custom-property counts. This
  is what the MicroDots theme layer consumes; it is never re-derived from screenshots.
- **Completeness.** Every manifest entry is written somewhere. Code the template never
  referenced is kept under `vendor/` with the role `vendor-unreferenced` rather than
  dropped, and `index.json` carries `unwritten_manifest_entries` -- which must be empty.
  A non-empty array means the artifact holds something this script did not understand.

**Refused, deliberately:**

- **A filename it was not given.** A module is named from an actual filename comment
  (`// tweaks-panel.jsx`) or it is `module-NN.js`. A banner comment is captured as the
  `banner` field and shown as a hint -- never promoted to a filename. A name that claims
  more than the source stated is worse than a neutral one.
- **Module purpose.** Roles beyond app/vendor are Phase 2's job, from content.

## Classification (Phase 2)

**`babel-modules` shape only** -- with `dc-runtime` there is one file, so classify regions
of `component.jsx` against the same role vocabulary and cite line ranges.

Assign every `app/` module exactly one role. Run these greps over `_src/app` and combine
with the `banner` hints in `index.json`:

| Role | Signals |
| --- | --- |
| `data-store` | Large literal arrays of records (`const [A-Z_]+ = \[`); assigns `window.DATA` / `window.<NAME>`; little or no JSX |
| `screen` | Returns a top-level view component; reads a store global; owns `useState` for its own view |
| `chrome` | Nav, sidebar, tab bar, shell, router-ish `setView` / `view===` switching |
| `ui-kit` | Reusable primitives (buttons, chips, icons, tables) with no domain nouns |
| `scaffold` | Claude Design's own tooling: `tweaks-panel.jsx`, `useTweaks`, `__activate_edit_mode`. **Always dies at the port** -- record as `drop`, never analyze as product |
| `vendor-global` | Reads an external global it does not define (e.g. `window.CumulativeDesignSystem_*`) -- an external dependency and a D-scope row |

Then record the seam graph in the same pass:

    grep -Hno "window\.[A-Za-z_][A-Za-z0-9_]*" _src/app/*.js*

Split writes (`window.X =`) from reads. The result is the prototype's real dependency
graph -- which module owns which data and which screens consume it. Phase 5 crosses it
with the feature domains to derive candidate MicroDot cut lines.

Write `<dossier>/prototype-inventory.json`:

```json
{
  "artifact": "<abs path>", "title": "<from index.json>", "slug": "<slug>",
  "modules": [{ "path": "_src/app/09-module-09.js", "order": 9, "role": "screen",
                "banner": "...", "label": "<human label>", "reads": ["DATA", "ENG"],
                "writes": [], "loc": 640, "confidence": "high" }],
  "stores": [{ "global": "DATA", "module": "_src/app/06-module-06.js",
               "collections": ["CONNECTIONS", "KNOWLEDGE"] }],
  "dropped": [{ "path": "_src/app/21-tweaks-panel.jsx", "why": "Claude Design scaffold" }],
  "unclassified": []
}
```

A module you cannot confidently classify goes in `unclassified` and is asked about in
Stage-1. Guessing a role here mis-routes a whole analysis agent.
