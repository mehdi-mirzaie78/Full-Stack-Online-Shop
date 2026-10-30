import { afterEach, expect, it, vi } from "vitest";
import { OTLPHttpJsonTraceExporter, OTLPHttpProtoTraceExporter } from "@vercel/otel";
import { resourceFromAttributes } from "@opentelemetry/resources";
import { SpanKind, SpanStatusCode, createTraceState } from "@opentelemetry/api";
import { backendPropagationUrls, localTraceUrl, safeExporter } from "./instrumentation.node";

afterEach(() => vi.unstubAllGlobals());
it("limits backend propagation matcher to exact configured origin", () => {
  expect(backendPropagationUrls(undefined)).toEqual([]);
  const [trusted] = backendPropagationUrls("http://server:8000");
  expect(trusted.test("http://server:8000/api/health/")).toBe(true);
  for (const foreign of ["http://server:80000/", "http://server:8000.evil/", "http://server:8000@evil/", "https://server:8000/"]) {
    expect(trusted.test(foreign)).toBe(false);
  }
  for (const invalid of ["file:///", "http://user:secret@server:8000", "http://server:8000/private", "http://server:8000?token=private"]) {
    expect(() => backendPropagationUrls(invalid)).toThrow();
  }
});
it("normalizes unmatched spans and removes raw name, status, events, links and tracestate", () => {
  const output = vi.fn();
  const exporter = safeExporter({ export: output, shutdown: async () => {}, forceFlush: async () => {} });
  const context = { traceId: "a".repeat(32), spanId: "b".repeat(16), traceFlags: 1, traceState: createTraceState("secret=private") };
  exporter.export([{
    name: "GET /customer/private", kind: SpanKind.SERVER, spanContext: () => context,
    startTime: [1, 0], endTime: [2, 0], duration: [1, 0], ended: true,
    status: { code: SpanStatusCode.ERROR, message: "private" }, attributes: { "http.target": "/private" },
    resource: resourceFromAttributes({ token: "private" }), instrumentationScope: { name: "private" },
    events: [], links: [], droppedAttributesCount: 0, droppedEventsCount: 0, droppedLinksCount: 0,
  }], () => {});
  const span = output.mock.calls[0][0][0];
  expect(span.name).toBe("request");
  expect(span.spanContext()).not.toHaveProperty("traceState");
  expect(JSON.stringify(span)).not.toContain("private");
});
it("allows only explicit local OTLP destinations", () => {
  expect(localTraceUrl("http://alloy:4318")).toBe("http://alloy:4318/v1/traces");
  expect(localTraceUrl("http://127.0.0.1:4318")).toBe("http://127.0.0.1:4318/v1/traces");
  for (const url of [undefined, "https://cloud.example", "http://alloy:4318?token=secret", "http://user:secret@alloy:4318"]) {
    expect(() => localTraceUrl(url)).toThrow();
  }
});
it.each([OTLPHttpJsonTraceExporter, OTLPHttpProtoTraceExporter])("serializes only reconstructed safe spans, not URL/error/resource/link secrets (%s)", async (Exporter) => {
  let serialized = "";
  vi.stubGlobal("fetch", vi.fn(async (_url, init) => {
    serialized = typeof init.body === "string" ? init.body : new TextDecoder().decode(init.body);
    return new Response("{}", { status: 200 });
  }));
  const exporter = safeExporter(new Exporter({ url: "http://127.0.0.1:4318/v1/traces" }));
  const spanContext = { traceId: "a".repeat(32), spanId: "b".repeat(16), traceFlags: 1, traceState: createTraceState("private=secret-marker") };
  await new Promise<void>((resolve, reject) => exporter.export([{
    name: "GET /private/secret-marker?token=secret-marker", kind: SpanKind.SERVER,
    spanContext: () => spanContext, parentSpanContext: spanContext,
    startTime: [1, 0], endTime: [2, 0], duration: [1, 0], ended: true,
    status: { code: SpanStatusCode.ERROR, message: "secret-marker" },
    attributes: { "http.target": "/secret-marker", "http.route": "/products/[id]", "http.method": "GET", "http.status_code": 500, "req.url": "secret-marker" },
    resource: resourceFromAttributes({ "service.name": "secret-marker", "token": "secret-marker" }),
    instrumentationScope: { name: "secret-marker", version: "secret-marker" },
    events: [{ name: "exception", time: [1, 0], attributes: { "exception.message": "secret-marker" } }],
    links: [{ context: spanContext, attributes: { token: "secret-marker" } }],
    droppedAttributesCount: 0, droppedEventsCount: 0, droppedLinksCount: 0,
  }], (result) => result.code === 0 ? resolve() : reject(result.error)));
  expect(serialized).not.toContain("secret-marker");
  expect(serialized).toContain("/products/[id]");
  expect(serialized).toContain("next");
  if (Exporter === OTLPHttpJsonTraceExporter) {
    expect(JSON.parse(serialized).resourceSpans[0].scopeSpans[0].spans[0].links).toEqual([]);
  } else {
    expect(serialized.length).toBeGreaterThan(0);
  }
});
