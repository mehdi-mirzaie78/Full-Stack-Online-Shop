import type { NextConfig } from "next";
import { PHASE_DEVELOPMENT_SERVER } from "next/constants";
import { loadEnvConfig } from "@next/env";
import path from "node:path";

const nextConfig = (phase: string): NextConfig => {
  const testing = process.env.SHOP_TEST_MODE === "1";
  const development = phase === PHASE_DEVELOPMENT_SERVER;
  // Next already cached client env; reload root files from the original process env.
  // The infra directory has no env files; tests discard cached client/development values.
  loadEnvConfig(path.resolve(__dirname, testing ? "../infra" : ".."), development, console, true);

  return {
    distDir: testing ? ".next-test" : development ? ".next-dev" : ".next",
    typescript: { tsconfigPath: testing ? "tsconfig.test.json" : "tsconfig.json" },
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
