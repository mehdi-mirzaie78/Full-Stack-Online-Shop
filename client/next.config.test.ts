import { execFileSync } from "node:child_process";
import path from "node:path";
import { describe, it } from "vitest";

const checkConfig = String.raw`
const assert = require("node:assert/strict");
const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");
const Module = require("node:module");
const configPath = process.argv[1];
const phase = process.argv[2];
const development = phase === "phase-development-server";
const mode = development ? "development" : "production";
const requireClient = Module.createRequire(configPath);
const { loadEnvConfig } = requireClient("@next/env");
const ts = requireClient("typescript");
const root = fs.mkdtempSync(path.join(os.tmpdir(), "next-config-env-"));
const client = path.join(root, "client");

try {
  fs.mkdirSync(client);
  fs.writeFileSync(path.join(client, ".env"), "CONFIG_SHARED=client\nCONFIG_CLIENT_ONLY=client\n");
  fs.writeFileSync(path.join(root, ".env"), [
    "CONFIG_SHARED=root",
    "CONFIG_PROCESS=file",
    "CONFIG_ROOT_ONLY=root",
    "CONFIG_EXPANDED=$" + "{CONFIG_ROOT_ONLY}/expanded",
  ].join("\n"));
  for (const mode of ["development", "production"]) {
    fs.writeFileSync(path.join(root, ".env." + mode), "CONFIG_MODE=" + mode + "\n");
    fs.writeFileSync(path.join(root, ".env." + mode + ".local"), "CONFIG_LOCAL=" + mode + "-local\n");
  }

  // Next loads client env before evaluating next.config.ts, sharing @next/env's cache.
  loadEnvConfig(client, development);
  assert.equal(process.env.CONFIG_SHARED, "client");
  const fixtureConfig = path.join(client, "next.config.cjs");
  const compiled = ts.transpileModule(fs.readFileSync(configPath, "utf8"), {
    compilerOptions: { module: ts.ModuleKind.CommonJS, esModuleInterop: true },
  }).outputText;
  const configModule = new Module(fixtureConfig);
  configModule.filename = fixtureConfig;
  configModule.paths = Module._nodeModulePaths(path.dirname(configPath));
  configModule._compile(compiled, fixtureConfig);
  const config = configModule.exports.default(phase);

  assert.equal(process.env.CONFIG_SHARED, "root", "root env must replace cached client env");
  assert.equal(process.env.CONFIG_ROOT_ONLY, "root");
  assert.equal(process.env.CONFIG_CLIENT_ONLY, undefined);
  assert.equal(process.env.CONFIG_PROCESS, "process", "process env must beat env files");
  assert.equal(process.env.CONFIG_MODE, mode);
  assert.equal(process.env.CONFIG_LOCAL, mode + "-local");
  assert.equal(process.env.CONFIG_EXPANDED, "root/expanded");
  assert.equal(config.distDir, development ? ".next-dev" : ".next");
} finally {
  fs.rmSync(root, { recursive: true, force: true });
}
`;

describe("Next config root environment", () => {
  it.each([
    ["phase-development-server", "development"],
    ["phase-production-build", "production"],
    ["phase-production-server", "production"],
  ] as const)("replaces cached client env during %s", (phase, nodeEnv) => {
    execFileSync(process.execPath, ["-e", checkConfig, path.resolve(__dirname, "next.config.ts"), phase], {
      env: {
        NODE_ENV: nodeEnv,
        CONFIG_PROCESS: "process",
        ...(process.env.TMPDIR ? { TMPDIR: process.env.TMPDIR } : {}),
      },
      stdio: "pipe",
    });
  });
});
