# Tina schema, config & inline visual editing (Next.js App Router)

The exact `tina/config.tsx` shape, the blocks schema, and the `useTina`/`tinaField` wiring that makes
content click-to-edit on the live page. Versions and file layout are verified against
`github.com/tinacms/tina-self-hosted-demo` (the canonical self-hosted reference).

## `tina/config.tsx`

The config file is `.tsx`. For self-hosted, the two load-bearing settings are **`contentApiUrlOverride`**
(points the generated client at your backend instead of Tina Cloud) and the local/prod **`authProvider`**
split.

```tsx
import { UsernamePasswordAuthJSProvider, TinaUserCollection } from "tinacms-authjs/dist/tinacms";
import { defineConfig, LocalAuthProvider } from "tinacms";
import { pageCollection } from "./collections/page";
import { settingsCollection } from "./collections/settings";

const isLocal = process.env.TINA_PUBLIC_IS_LOCAL === "true";

export default defineConfig({
  authProvider: isLocal ? new LocalAuthProvider() : new UsernamePasswordAuthJSProvider(),
  contentApiUrlOverride: "/api/tina/gql",          // ← self-hosted backend (NOT Tina Cloud)
  build: { publicFolder: "public", outputFolder: "admin" },   // admin SPA → public/admin → /admin
  media: { tina: { mediaRoot: "uploads", publicFolder: "public" } },   // git/static media under public/uploads
  schema: { collections: [TinaUserCollection, pageCollection, settingsCollection] },
});
```

- `TinaUserCollection` is **required** for Auth.js self-hosted login (users stored as content).
- For `--media r2|s3`, replace `media.tina` with `media.loadCustomStore` → `next-tinacms-s3` (see
  `deploy-cloudflare.md` / `deploy-vercel.md`).
- For `--tina cloud`, drop `contentApiUrlOverride`/`authProvider` and set `clientId`/`branch`/`token`.

## The blocks collection — `tina/collections/page.ts`

The page-builder model: a `blocks` field that is `type: "object"`, `list: true`, with one `template` per
section type. Tina stores a `_template` discriminator on each block.

```ts
import type { Collection } from "tinacms";

export const pageCollection: Collection = {
  name: "page",
  label: "Pages",
  path: "content/pages",
  format: "json",
  ui: { router: ({ document }) => (document._sys.filename === "home" ? "/" : `/${document._sys.filename}`) },
  fields: [
    { type: "string", name: "title", label: "Title", isTitle: true, required: true },
    {
      type: "object", name: "blocks", label: "Sections", list: true,
      ui: { itemProps: (item) => ({ label: item?._template }) },
      templates: [
        {
          name: "hero", label: "Hero",
          fields: [
            { type: "string", name: "eyebrow", label: "Eyebrow" },
            { type: "string", name: "headline", label: "Headline" },
            { type: "string", name: "sub", label: "Subhead", ui: { component: "textarea" } },
            { type: "image", name: "image", label: "Background image" },
            { type: "string", name: "accent", label: "Accent", options: ["flame", "cool"] },
            { type: "string", name: "layout", label: "Layout", options: ["split", "overlay"] },
            { type: "object", name: "cta", label: "CTA", fields: [
              { type: "string", name: "text" }, { type: "string", name: "url" } ] },
          ],
        },
        {
          name: "services", label: "Services",
          fields: [
            { type: "string", name: "heading", label: "Heading" },
            { type: "object", name: "items", label: "Items", list: true,
              ui: { itemProps: (i) => ({ label: i?.title }) },
              fields: [ { type: "string", name: "title" }, { type: "string", name: "body", ui: { component: "textarea" } } ] },
          ],
        },
        { name: "cta", label: "CTA band",
          fields: [ { type: "string", name: "text" }, { type: "string", name: "url" } ] },
      ],
    },
  ],
};
```

Field types you'll use: `string` (+ `options` for a select, `ui.component:"textarea"` for multi-line),
`image`, `object` (nested + `list` for arrays), `rich-text` (`isBody: true` for long prose → `TinaMarkdown`),
`number`, `boolean`, `datetime`, `reference` (cross-collection link).

## Inline visual editing — the App-Router split

Editing feels "inline" because of three pieces: `useTina` makes the data live, `tinaField` marks an
element, and Tina outlines every marked element in edit mode so clicking it focuses the sidebar field.

**Server Component** `app/(site)/page.tsx` — fetch on the server:
```tsx
import client from "@/tina/__generated__/client";
import HomeView from "./home-view";

export const revalidate = 0;    // editable route: don't serve a stale cache (see gotchas.md)

export default async function Page() {
  const res = await client.queries.page({ relativePath: "home.json" });
  return <HomeView {...res} />;   // pass the WHOLE result: { data, query, variables }
}
```

**Client Component** `app/(site)/home-view.tsx` — go live + mark fields:
```tsx
"use client";
import { useTina, tinaField } from "tinacms/dist/react";
import { Hero, Services, CtaBand } from "@/components/blocks";

export default function HomeView(props: {
  data: any; query: string; variables: any;
}) {
  const { data } = useTina(props);          // in edit mode, re-hydrates on every keystroke
  return (
    <>
      {data.page.blocks?.map((block: any, i: number) => {
        switch (block.__typename) {          // Tina suffixes template name, e.g. PageBlocksHero
          case "PageBlocksHero":
            return (
              <Hero key={i} block={block}
                    titleField={tinaField(block, "headline")}   // pass the marker down as a prop…
                    subField={tinaField(block, "sub")} />
            );
          case "PageBlocksServices": return <Services key={i} block={block} />;
          case "PageBlocksCta":      return <CtaBand key={i} block={block} />;
          default: return null;
        }
      })}
    </>
  );
}
```

**Inside the block component**, spread the marker onto a *real HTML element* (never a React component —
components can't receive arbitrary DOM attributes):
```tsx
export function Hero({ block, titleField, subField }: HeroProps) {
  return (
    <section>
      <h1 data-tina-field={titleField}>{block.headline}</h1>
      <p  data-tina-field={subField}>{block.sub}</p>
    </section>
  );
}
```

- `tinaField(obj, "prop")` reads the hidden `_content_source` metadata `useTina` injects and returns the
  value for `data-tina-field`. Put it **on the element that shows the value**.
- In production (not edit mode) `useTina` passes `data` straight through and `tinaField` is inert — zero
  runtime cost.
- `__typename` is the reliable block discriminator in query results (`PageBlocks<Template>`); `_template`
  is what's stored on disk.

## The `/admin` route & preview

- `tinacms build` compiles the admin SPA to **`public/admin/`** (from `build.outputFolder`). It's a build
  artifact — **gitignore it**. Add the rewrite in `next.config.mjs` so `/admin` resolves:
  `{ source: "/admin", destination: "/admin/index.html" }`.
- Each collection's `ui.router` maps a document to its front-end URL so the admin's preview pane loads the
  live page with the editing outlines.

## Generated client & queries

`tinacms dev`/`build` generates `tina/__generated__/` (`client.ts`, `databaseClient.ts`, `types.ts`,
`queries.ts`). Fetch with the typed `client.queries.<collection>({ relativePath })`. For self-hosted RSC
reads you *may* import `databaseClient` for a direct DB read (no HTTP hop); the client component still
needs `{ query, variables, data }` for `useTina` either way. `tina/__generated__/` is gitignored;
`tina/tina-lock.json` is committed.
