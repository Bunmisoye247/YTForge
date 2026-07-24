import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  // Self-contained server bundle (only the deps actually used at runtime,
  // no full node_modules) — what frontend/Dockerfile's runtime stage copies.
  output: "standalone",
};

export default nextConfig;
