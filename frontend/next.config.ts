import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Removed strict COOP/COEP headers because they block Sandpack cross-origin iframes
  typescript: {
    ignoreBuildErrors: true,
  },
  eslint: {
    // ESLint runs fine locally via `npm run lint`.
    // Vercel uses pnpm which resolves eslint-config-next differently,
    // causing build failures. Disable ESLint during CI builds.
    ignoreDuringBuilds: true,
  },
};

export default nextConfig;
