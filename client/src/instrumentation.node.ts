import { registerOTel, OTLPHttpProtoTraceExporter } from "@vercel/otel";
import { resourceFromAttributes } from "@opentelemetry/resources";
import type { SpanContext } from "@opentelemetry/api";
import { safeMethod, safeRoute } from "./lib/error-reporting";

type TraceExporter = Pick<OTLPHttpProtoTraceExporter, "export" | "shutdown" | "forceFlush">;

export function localTraceUrl(endpoint: string | undefined): string {
  if (!endpoint) throw new Error("Explicit local OTLP endpoint required");
  const url = new URL(endpoint);
  if (url.protocol !== "http:" || !["alloy", "localhost", "127.0.0.1", "[::1]"].includes(url.hostname)
    || url.username || url.password || url.search || url.hash || url.pathname !== "/") {
    throw new Error("Only local OTLP base endpoints permitted");
  }
  return `${url.origin}/v1/traces`;
}

const cleanContext = (context: SpanContext): SpanContext => ({
  traceId: context.traceId, spanId: context.spanId, traceFlags: context.traceFlags,
});

export function safeExporter(exporter: TraceExporter): TraceExporter {
  return {
    export(spans, callback) {
      exporter.export(spans.map((span) => {
        const route = safeRoute(typeof span.attributes["http.route"] === "string" ? span.attributes["http.route"] : undefined);
        const method = safeMethod(String(span.attributes["http.request.method"] ?? span.attributes["http.method"] ?? ""));
        const status = span.attributes["http.response.status_code"] ?? span.attributes["http.status_code"];
        return {
          name: route ?? "request", kind: span.kind,
          spanContext: () => cleanContext(span.spanContext()),
          parentSpanContext: span.parentSpanContext ? cleanContext(span.parentSpanContext) : undefined,
          startTime: span.startTime, endTime: span.endTime, duration: span.duration, ended: span.ended,
          status: { code: span.status.code },
          attributes: {
            ...(route ? { "http.route": route } : {}),
            ...(method ? { "http.request.method": method } : {}),
            ...(typeof status === "number" && Number.isInteger(status) && status >= 100 && status <= 599 ? { "http.response.status_code": status } : {}),
          },
          resource: resourceFromAttributes({ "service.name": "next" }),
          instrumentationScope: { name: "next" }, events: [], links: [],
          droppedAttributesCount: 0, droppedEventsCount: 0, droppedLinksCount: 0,
        };
      }), callback);
    },
    shutdown: () => exporter.shutdown(),
    forceFlush: () => exporter.forceFlush?.() ?? Promise.resolve(),
  };
}

export function backendPropagationUrls(origin: string | undefined): RegExp[] {
  if (!origin) return [];
  const url = new URL(origin);
  if (!["http:", "https:"].includes(url.protocol) || url.username || url.password
    || url.pathname !== "/" || url.search || url.hash) {
    throw new Error("OTEL_BACKEND_ORIGIN must be an HTTP origin without credentials or path");
  }
  return [new RegExp(`^${url.origin.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}/`)];
}

export function registerLocalTelemetry() {
  const trusted = backendPropagationUrls(process.env.OTEL_BACKEND_ORIGIN);
  const originalFetch = globalThis.fetch;
  // Sit below OTel so only requests carrying trace context lose automatic redirects.
  // Native fetch forwards traceparent across origins without rechecking the allowlist.
  globalThis.fetch = async (input, init) => {
    const request = input instanceof Request ? input : undefined;
    const url = new URL(request?.url ?? String(input));
    const headers = new Headers(init?.headers ?? request?.headers);
    const redirect = init?.redirect ?? request?.redirect ?? "follow";
    if (trusted.some((pattern) => pattern.test(url.href)) && headers.has("traceparent") && redirect === "follow") {
      return originalFetch(input, { ...init, redirect: "error" });
    }
    return originalFetch(input, init);
  };
  registerOTel({
    serviceName: "next", instrumentations: ["fetch"], propagators: ["tracecontext"],
    instrumentationConfig: { fetch: {
      propagateContextUrls: trusted,
      // Vercel also trusts localhost/deployment URLs by default; deny their complement.
      dontPropagateContextUrls: [trusted.length ? new RegExp(`^(?!${trusted[0].source.slice(1)})`) : /.*/],
    } },
    autoDetectResources: false, resourceDetectors: [], traceSampler: "always_on",
    metricReaders: [], logRecordProcessors: [],
    traceExporter: safeExporter(new OTLPHttpProtoTraceExporter({
      url: localTraceUrl(process.env.OTEL_EXPORTER_OTLP_ENDPOINT), headers: {}, timeoutMillis: 1000,
    })),
  });
}
