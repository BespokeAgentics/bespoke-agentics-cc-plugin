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
  // For --media s3|r2, add the media host here:
  // images: { remotePatterns: [{ protocol: "https", hostname: "<your-s3-or-r2-host>" }] },
};

export default nextConfig;
