import type { Collection } from "tinacms";

// Page-builder model: each page is an ordered list of section "blocks", one template
// per section type. The editor can reorder / add / remove sections. Add templates as you
// externalize more of the prototype's sections (references/content-modeling.md).
export const pageCollection: Collection = {
  name: "page",
  label: "Pages",
  path: "content/pages",
  format: "json",
  ui: {
    // Maps a document to its front-end route for the admin preview pane.
    router: ({ document }) =>
      document._sys.filename === "home" ? "/" : `/${document._sys.filename}`,
  },
  fields: [
    { type: "string", name: "title", label: "Title", isTitle: true, required: true },
    {
      type: "object",
      name: "blocks",
      label: "Sections",
      list: true,
      ui: { itemProps: (item) => ({ label: item?._template }) },
      templates: [
        {
          name: "hero",
          label: "Hero",
          fields: [
            { type: "string", name: "eyebrow", label: "Eyebrow" },
            { type: "string", name: "headline", label: "Headline" },
            { type: "string", name: "sub", label: "Subhead", ui: { component: "textarea" } },
            { type: "image", name: "image", label: "Background image" },
            { type: "string", name: "imageAlt", label: "Image alt text" },
            { type: "string", name: "accent", label: "Accent", options: ["flame", "cool"] },
            { type: "string", name: "layout", label: "Layout", options: ["split", "overlay"] },
            {
              type: "object",
              name: "cta",
              label: "Call to action",
              fields: [
                { type: "string", name: "text", label: "Text" },
                { type: "string", name: "url", label: "URL" },
              ],
            },
          ],
        },
        {
          name: "services",
          label: "Services grid",
          fields: [
            { type: "string", name: "heading", label: "Heading" },
            {
              type: "object",
              name: "items",
              label: "Items",
              list: true,
              ui: { itemProps: (i) => ({ label: i?.title }) },
              fields: [
                { type: "string", name: "title", label: "Title" },
                { type: "string", name: "body", label: "Body", ui: { component: "textarea" } },
                { type: "string", name: "icon", label: "Icon (lucide name)" },
              ],
            },
          ],
        },
        {
          name: "cta",
          label: "CTA band",
          fields: [
            { type: "string", name: "text", label: "Text" },
            { type: "string", name: "url", label: "URL" },
          ],
        },
      ],
    },
  ],
};
