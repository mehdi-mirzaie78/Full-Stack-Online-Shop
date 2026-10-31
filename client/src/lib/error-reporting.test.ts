import { afterEach, expect, it, vi } from "vitest";
import { reportError } from "./error-reporting";

afterEach(() => vi.restoreAllMocks());

it("emits safe JSON without arbitrary thrown data or metadata", () => {
  const output = vi.spyOn(console, "error").mockImplementation(() => {});
  const error = new Error("password=private");
  error.name = "secret-name";
  reportError("request_failed", error, {
    service: "next", requestId: "b4f63dc7-4b04-4b23-a182-555cb8277fd1",
    route: "/products/[id]", method: "GET",
  });
  const data = JSON.parse(output.mock.calls[0][0] as string);
  expect(data).toMatchObject({ event: "request_failed", level: "ERROR", service: "next",
    request_id: "b4f63dc7-4b04-4b23-a182-555cb8277fd1", error_type: "Error",
    route: "/products/[id]", method: "GET", trace_id: null, span_id: null });
  expect(data.timestamp).toMatch(/Z$/);
  expect(output.mock.calls[0][0]).not.toMatch(/private|secret-name/);
});

it("rejects invalid correlation, method and raw query strings", () => {
  const output = vi.spyOn(console, "error").mockImplementation(() => {});
  reportError("unhandled_rejection", { token: "private" }, {
    requestId: "header\ninjection", route: "/private?token=private", method: "private",
  });
  expect(JSON.parse(output.mock.calls[0][0] as string)).toMatchObject({
    request_id: null, route: null, method: null, error_type: "UnknownError",
  });
  expect(output.mock.calls[0][0]).not.toContain("private");
});
