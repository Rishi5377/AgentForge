import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Removed strict COOP/COEP headers because they block Sandpack cross-origin iframes
  typescript: {
    ignoreBuildErrors: true,
  },
};

export default nextConfig;
