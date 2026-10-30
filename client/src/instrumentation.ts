import type { Instrumentation } from "next";
import { reportError } from "./lib/error-reporting";

export const onRequestError: Instrumentation.onRequestError = (error, request, context) => {
  const header = request.headers["x-request-id"];
  reportError("request_failed", error, {
    service: "next", requestId: typeof header === "string" ? header : undefined,
    route: context.routePath, method: request.method,
  });
};

export async function register() {
  if (process.env.NEXT_RUNTIME === "nodejs" && process.env.OTEL_ENABLED === "true") {
    const { registerLocalTelemetry } = await import("./instrumentation.node");
    registerLocalTelemetry();
  }
}
