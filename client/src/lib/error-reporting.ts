import { isSpanContextValid, trace } from "@opentelemetry/api";

type Event = "request_failed" | "browser_error" | "unhandled_rejection" | "render_failed" | "preview_failed";
type Context = { service?: "next" | "browser"; requestId?: string; route?: string; method?: string };
const uuid = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
const errorTypes = new Set(["Error", "TypeError", "RangeError", "ReferenceError", "SyntaxError", "URIError", "EvalError"]);
export const safeRoute = (route?: string) => route && /^\/[\w/.[\]()-]*$/.test(route) && route.length <= 200 ? route : null;
export const safeMethod = (method?: string) => method && /^(GET|HEAD|POST|PUT|PATCH|DELETE|OPTIONS)$/.test(method) ? method : null;

export function reportError(event: Event, error: unknown, context: Context = {}) {
  const span = context.service === "next" ? trace.getActiveSpan()?.spanContext() : undefined;
  console.error(JSON.stringify({
    timestamp: new Date().toISOString(), level: "ERROR", service: context.service ?? "browser", event,
    error_type: error instanceof Error ? (errorTypes.has(error.name) ? error.name : "Error") : "UnknownError",
    request_id: context.requestId && uuid.test(context.requestId) ? context.requestId.toLowerCase() : null,
    route: safeRoute(context.route), method: safeMethod(context.method),
    trace_id: span && isSpanContextValid(span) ? span.traceId : null,
    span_id: span && isSpanContextValid(span) ? span.spanId : null,
  }));
}
