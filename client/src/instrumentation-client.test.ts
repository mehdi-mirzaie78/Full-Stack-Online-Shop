import { afterEach, expect, it, vi } from "vitest";

afterEach(() => { vi.restoreAllMocks(); vi.unstubAllGlobals(); });
it("registers non-suppressing browser hooks with safe reporting", async () => {
  const handlers = new Map<string, (event: { error?: unknown; reason?: unknown }) => void>();
  vi.stubGlobal("window", { addEventListener: (name: string, handler: (event: { error?: unknown; reason?: unknown }) => void) => handlers.set(name, handler) });
  const output = vi.spyOn(console, "error").mockImplementation(() => {});
  await import("./instrumentation-client");
  handlers.get("error")?.({ error: new Error("private") });
  handlers.get("unhandledrejection")?.({ reason: { token: "private" } });
  expect(output.mock.calls.map(([line]) => JSON.parse(line as string).event)).toEqual(["browser_error", "unhandled_rejection"]);
  expect(JSON.stringify(output.mock.calls)).not.toContain("private");
});
