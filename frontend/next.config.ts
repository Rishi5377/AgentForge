import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Removed strict COOP/COEP headers because they block Sandpack cross-origin iframes
  typescript: {
    ignoreBuildErrors: true,
  },
  // Note: `eslint` key is NOT supported in Next.js 16+ next.config.ts
  // ESLint is configured via eslint.config.mjs instead
};

export default nextConfig;
