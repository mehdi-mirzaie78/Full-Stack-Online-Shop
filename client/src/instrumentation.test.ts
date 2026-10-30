import { afterEach, expect, it, vi } from "vitest";
import { onRequestError, register } from "./instrumentation";

vi.mock("./instrumentation.node", () => ({ registerLocalTelemetry: vi.fn() }));
afterEach(() => { vi.restoreAllMocks(); vi.unstubAllEnvs(); });
it("logs template and validated request ID, not private request URL", async () => {
  const output = vi.spyOn(console, "error").mockImplementation(() => {});
  await onRequestError(new Error("private"), {
    path: "/products/private?token=private", method: "GET", headers: { "x-request-id": "invalid" },
  }, { routerKind: "App Router", routePath: "/products/[id]", routeType: "render", revalidateReason: undefined, renderSource: "react-server-components" });
  expect(JSON.parse(output.mock.calls[0][0] as string)).toMatchObject({ route: "/products/[id]", request_id: null });
  expect(output.mock.calls[0][0]).not.toContain("private");
});
it("registers only opted-in Node runtime", async () => {
  const { registerLocalTelemetry } = await import("./instrumentation.node");
  vi.stubEnv("NEXT_RUNTIME", "nodejs"); vi.stubEnv("OTEL_ENABLED", "false");
  await register(); expect(registerLocalTelemetry).not.toHaveBeenCalled();
  vi.stubEnv("NEXT_RUNTIME", "edge"); vi.stubEnv("OTEL_ENABLED", "true");
  await register(); expect(registerLocalTelemetry).not.toHaveBeenCalled();
  vi.stubEnv("NEXT_RUNTIME", "nodejs");
  await register(); expect(registerLocalTelemetry).toHaveBeenCalledOnce();
});
