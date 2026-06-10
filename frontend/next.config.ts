import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Removed strict COOP/COEP headers because they block Sandpack cross-origin iframes
};

export default nextConfig;
