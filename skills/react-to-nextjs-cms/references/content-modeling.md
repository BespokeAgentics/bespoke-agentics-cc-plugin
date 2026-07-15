# Content modeling — externalizing baked-in copy into editable Tina content

This is the phase that makes the site *editable*. The prototype hardcodes all copy in JSX; you move it
into Git-backed content files and model it so a non-developer can edit — ideally in place. Pair with
`tina-schema.md` (the exact `tina/config` field syntax + `useTina`/`tinaField` wiring).

## The mental model

- **Code** = the components (design system, blocks, layout). Ships in the repo, edited by developers.
- **Content** = the words and images. Lives in `content/**` as Markdown/JSON, edited by the client
  through Tina. Committed to Git on save (self-hosted Tina's git provider). **This is the "no formal CMS"
  promise: the source of truth is files in the repo, not a database.**

Your job: for every `content_candidate` the analyzer flagged, decide *is this content or is this
structure?* Content becomes a Tina field; structure stays in code.

| Baked in JSX | Verdict | Where it goes |
|---|---|---|
| `<h1>Comfort, engineered right.</h1>` | content | `hero.headline` field |
| `"Fast repairs, honest installs…"` | content | `hero.sub` field |
| `["Repairs","Installs","Maintenance"]` service names | content | `services` list of objects |
| phone `843-555-0100`, hours, address | content | `contact.*` fields (or a `settings` global) |
| hero/section images (`<image-slot>`) | content | `image` fields |
| CTA button label + href | content | `cta.text`, `cta.url` |
| `aria-label="Open menu"`, class names, icon names | structure | stays in code |
| section order / which blocks exist | **content** (page-builder) | the `blocks` list (reorderable) |

## Model a marketing page as a blocks list (the page-builder pattern)

Don't model a landing page as ~40 flat fields. Model it as an **ordered list of section blocks**, each a
named template. The editor can then reorder, add, and remove sections — the closest thing to the
prototype's feel, and far more useful than a rigid form.

`content/pages/home.json` (what an editor's changes serialize to):
```jsonc
{
  "title": "Home",
  "blocks": [
    { "_template": "hero", "eyebrow": "SERVING THE SOUTH CAROLINA LOWCOUNTRY",
      "headline": "Comfort, engineered right.",
      "sub": "Fast repairs, honest installs, and maintenance that actually saves you money.",
      "image": "/uploads/hero-tech.jpg", "accent": "cool", "layout": "overlay",
      "cta": { "text": "No heat? No cool? We're on it.", "url": "/book" } },
    { "_template": "services", "heading": "What we do",
      "items": [ { "title": "Repairs", "body": "Same-day when it matters." }, { "title": "Installs", "body": "…" } ] },
    { "_template": "cta", "text": "Book a visit", "url": "/book" }
  ]
}
```

Each block template ⇄ a React block component in `components/blocks/*` that renders it. The page view maps
`blocks` → `switch (block._template)` → the matching component. See `tina-schema.md` for the exact
`object`/`list`/`templates` schema and the render switch.

**Reuse the tweak knobs.** The prototype's `TWEAK_DEFAULTS` (`accent`, `heroTone`, `heroLayout`,
`heroPhoto`) were design choices exposed to the author. Keep the ones the client should control as fields
on the relevant block (e.g. `hero.accent` as a `string` field with `options: ["flame","cool"]`, rendered
as a select). Drop knobs that were just prototyping scaffolding.

## Globals vs page content

- **Per-page** content (hero copy, that page's sections) → the page's own content file.
- **Site-wide** content used across pages (nav labels, footer, phone/address, social links) → a **`settings`
  global collection** (a single `content/settings/index.json`), so editing it once updates every page.
  Header/Footer read from it.

## Where content files live

```
content/
├── pages/            # one file per routed page: home.json, services.json, commercial.json, book.json
├── settings/         # index.json — nav, footer, contact (the site global)
└── users/            # index.json — the Tina admin user(s) seed (self-hosted auth)
```

Format: **JSON** for structured, block-based pages (clean diffs, no frontmatter ceremony). Use **MD/MDX**
only where a field is genuinely long-form prose with rich text (a blog post body, an "about" narrative) —
then that field is `type: "rich-text", isBody: true` and renders through `TinaMarkdown`. Most marketing
pages are better as JSON blocks.

## Externalization procedure (per page)

1. Read the page JSX. List every content literal (the analyzer's candidates are the starting set).
2. Decide the block breakdown (hero / services / testimonials / cta / …) — usually the page's own visual
   sections.
3. Write the `content/pages/<id>.json` with the real copy lifted verbatim from the JSX.
4. Add/confirm the matching templates in `tina/collections/page.ts`.
5. Refactor the page component to **read from `data.blocks`** instead of hardcoded strings, and render each
   block via its component. Add `data-tina-field={tinaField(block, "headline")}` to each editable element.
6. Delete the now-dead hardcoded copy from the component.

Fan this out: one `content-porter` subagent per page (they all share the collection contract), per
`parallel-porting.md`. The main thread writes the schema first so porters target a fixed shape.

## Acceptance test

Open the running site in Tina edit mode, click a headline: the sidebar focuses that exact field, and
typing updates the page live. Change a service item's text, hit save: a commit lands in the repo and the
`content/pages/<id>.json` diff shows only that change. If a piece of visible copy *can't* be edited that
way, it's still hardcoded — go back and externalize it.
