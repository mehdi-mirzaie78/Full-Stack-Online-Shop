import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./e2e", fullyParallel: false, forbidOnly: Boolean(process.env.CI),
  retries: process.env.CI ? 1 : 0, workers: 1,
  reporter: [["list"], ["html", { open: "never" }]],
  use: {
    baseURL: "http://127.0.0.1:3100", browserName: "chromium",
    ...(process.env.E2E_BROWSER_CHANNEL ? { channel: process.env.E2E_BROWSER_CHANNEL } : {}),
    trace: "retain-on-failure", screenshot: "only-on-failure", video: "off",
  },
  webServer: {
    command: "npm run start -- --port 3100 --hostname 127.0.0.1",
    url: "http://127.0.0.1:3100", reuseExistingServer: false, timeout: 120_000,
    env: { OTEL_ENABLED: "false", NEXT_TELEMETRY_DISABLED: "1" },
  },
});
