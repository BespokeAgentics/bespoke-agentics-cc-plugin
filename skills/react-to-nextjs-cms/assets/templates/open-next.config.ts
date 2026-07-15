import { defineCloudflareConfig } from "@opennextjs/cloudflare";
// Optional: R2-backed incremental cache for ISR. Bind NEXT_INC_CACHE_R2_BUCKET in
// wrangler.jsonc, then uncomment:
// import r2IncrementalCache from "@opennextjs/cloudflare/overrides/incremental-cache/r2-incremental-cache";

export default defineCloudflareConfig({
  // incrementalCache: r2IncrementalCache,
});
