import type { NextConfig } from "next";
import { PHASE_DEVELOPMENT_SERVER } from "next/constants";
import { loadEnvConfig } from "@next/env";
import path from "node:path";

const nextConfig = (phase: string): NextConfig => {
  const development = phase === PHASE_DEVELOPMENT_SERVER;
  // Next already cached client env; reload root files from the original process env.
  loadEnvConfig(path.resolve(__dirname, ".."), development, console, true);

  return {
    distDir: development ? ".next-dev" : ".next",
    reactStrictMode: true,
    images: {
      remotePatterns: [
        {
          protocol: "http",
          hostname: "localhost",
          port: "9000",
          pathname: "/**",
        },
      ],
    },
  };
};

export default nextConfig;
