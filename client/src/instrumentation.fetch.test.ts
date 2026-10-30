// @vitest-environment node
import { createServer } from "node:http";
import { once } from "node:events";
import { expect, it, vi } from "vitest";
import { trace } from "@opentelemetry/api";
import { registerLocalTelemetry } from "./instrumentation.node";

it("propagates real fetch parent trace only to configured backend origin", async () => {
  const seen: (string | undefined)[] = [];
  const server = createServer((request, response) => {
    if (request.url !== "/v1/traces") seen.push(request.headers.traceparent as string | undefined);
    if (request.url?.startsWith("/redirect/")) {
      response.writeHead(Number(request.url.split("/")[2]) || 302, {
        location: `http://localhost:${(server.address() as { port: number }).port}/redirect-target`,
      });
    }
    response.end("{}");
  });
  server.listen(0, "127.0.0.1");
  await once(server, "listening");
  const port = (server.address() as { port: number }).port;
  const origin = `http://127.0.0.1:${port}`;
  vi.stubEnv("OTEL_EXPORTER_OTLP_ENDPOINT", origin);
  vi.stubEnv("OTEL_BACKEND_ORIGIN", origin);
  try {
    registerLocalTelemetry();
    await trace.getTracer("fetch-test").startActiveSpan("parent", async (span) => {
      try {
        await (await fetch(`${origin}/trusted`)).text();
        await (await fetch(`http://localhost:${port}/foreign`)).text();
        expect(seen[0]?.split("-")[1]).toBe(span.spanContext().traceId);
        expect(seen[1]).toBeUndefined();
        for (const status of [301, 302, 303, 307, 308]) {
          seen.length = 0;
          await expect(fetch(`${origin}/redirect/${status}`)).rejects.toThrow(TypeError);
          expect(seen).toHaveLength(1);
          expect(seen[0]?.split("-")[1]).toBe(span.spanContext().traceId);
        }
        seen.length = 0;
        const manual = await fetch(new Request(`${origin}/redirect/302`, { redirect: "manual" }));
        expect(manual.status).toBe(302);
        await manual.text();
        expect(seen).toHaveLength(1);
        await expect(fetch(new Request(`${origin}/redirect/302`), { redirect: "follow" })).rejects.toThrow(TypeError);
        expect(seen).toHaveLength(2);

        seen.length = 0;
        await (await fetch(`http://localhost:${port}/redirect/302`)).text();
        expect(seen).toEqual([undefined, undefined]);
        seen.length = 0;
        await (await fetch(`${origin}/redirect/302`, { opentelemetry: { ignore: true } })).text();
        expect(seen).toEqual([undefined, undefined]);
      } finally { span.end(); }
    });
  } finally {
    vi.unstubAllEnvs();
    server.closeAllConnections();
    await new Promise<void>((resolve) => server.close(() => resolve()));
  }
});
