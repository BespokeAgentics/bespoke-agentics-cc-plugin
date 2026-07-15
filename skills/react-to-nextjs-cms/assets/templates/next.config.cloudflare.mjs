import { initOpenNextCloudflareForDev } from "@opennextjs/cloudflare";

/** @type {import('next').NextConfig} */
const nextConfig = {
  // The four Tina packages ship untranspiled — REQUIRED or next build fails.
  transpilePackages: [
    "tinacms",
    "tinacms-authjs",
    "@tinacms/datalayer",
    "tinacms-gitprovider-github",
  ],
  async rewrites() {
    // Serve the built admin SPA (public/admin) at /admin.
    return [{ source: "/admin", destination: "/admin/index.html" }];
  },
  // For --media r2|s3, add the media host here:
  // images: { remotePatterns: [{ protocol: "https", hostname: "<your-r2-or-s3-host>" }] },
};

// Lets `next dev` see Cloudflare bindings via getCloudflareContext().
initOpenNextCloudflareForDev();

export default nextConfig;
