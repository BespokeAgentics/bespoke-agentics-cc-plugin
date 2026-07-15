import {
  UsernamePasswordAuthJSProvider,
  TinaUserCollection,
} from "tinacms-authjs/dist/tinacms";
import { defineConfig, LocalAuthProvider } from "tinacms";
import { pageCollection } from "./collections/page";
import { settingsCollection } from "./collections/settings";

// Self-hosted: local dev uses LocalAuthProvider + a local DB; production uses Auth.js
// against the self-hosted backend. `contentApiUrlOverride` points the generated client
// at OUR backend route instead of Tina Cloud.
const isLocal = process.env.TINA_PUBLIC_IS_LOCAL === "true";

export default defineConfig({
  authProvider: isLocal
    ? new LocalAuthProvider()
    : new UsernamePasswordAuthJSProvider(),
  contentApiUrlOverride: "/api/tina/gql",
  build: {
    publicFolder: "public",
    outputFolder: "admin", // admin SPA -> public/admin -> served at /admin (see next.config rewrite)
  },
  media: {
    // Git/static media under public/uploads. For --media r2|s3 replace this with
    // media.loadCustomStore -> next-tinacms-s3 (see references/deploy-<target>.md).
    tina: { mediaRoot: "uploads", publicFolder: "public" },
  },
  schema: {
    // TinaUserCollection backs Auth.js self-hosted login — keep it first.
    collections: [TinaUserCollection, pageCollection, settingsCollection],
  },
});
