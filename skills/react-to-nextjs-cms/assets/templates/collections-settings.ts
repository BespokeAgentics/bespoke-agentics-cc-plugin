import type { Collection } from "tinacms";

// Site-wide content used across pages (nav, footer, contact). A single document
// (content/settings/index.json) so editing it once updates every page. Header/Footer
// read from this.
export const settingsCollection: Collection = {
  name: "settings",
  label: "Site settings",
  path: "content/settings",
  format: "json",
  ui: {
    global: true, // shows in a dedicated "global" area of the admin, not the document list
    allowedActions: { create: false, delete: false },
  },
  fields: [
    { type: "string", name: "siteName", label: "Site name" },
    { type: "image", name: "logo", label: "Logo" },
    {
      type: "object",
      name: "nav",
      label: "Nav links",
      list: true,
      ui: { itemProps: (i) => ({ label: i?.label }) },
      fields: [
        { type: "string", name: "label", label: "Label" },
        { type: "string", name: "url", label: "URL" },
      ],
    },
    {
      type: "object",
      name: "contact",
      label: "Contact",
      fields: [
        { type: "string", name: "phone", label: "Phone" },
        { type: "string", name: "email", label: "Email" },
        { type: "string", name: "address", label: "Address" },
        { type: "string", name: "hours", label: "Hours" },
      ],
    },
    { type: "string", name: "footerNote", label: "Footer note" },
  ],
};
