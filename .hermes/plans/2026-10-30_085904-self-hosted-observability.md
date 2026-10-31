# Private Docker Observability — Logging and CI Plan Revision

> **For Hermes:** Planning only. Execute task-by-task with available implementation/review skills after approval. No application or infrastructure changes have been applied.

**Goal:** Keep logs, metrics and distributed traces on this machine while providing searchable Grafana dashboards and automated regression checks.

**Architecture:** Run Grafana OSS, Loki, Prometheus, Tempo and Grafana Alloy as an optional local Compose overlay. Alloy collects approved container logs and OpenTelemetry spans, Loki stores logs, Tempo stores traces, and Prometheus stores infrastructure metrics plus request/error/duration metrics derived from spans. Grafana joins these sources into one local UI; no Grafana Cloud, external telemetry exporter, remote-write destination or online logging account is configured.

**Tech stack:** Existing application stack plus Grafana OSS, Loki single-binary/filesystem, Tempo monolithic/local storage, Prometheus single-server, Alloy collector, OpenTelemetry Python SDK and `@vercel/otel` for Next.js.

---

## Relationship to original plan

This revision and `.hermes/plans/2026-10-30_083809-logging-and-ci.md` form one implementation specification. Original plan owns application-safe JSON events, health-error sanitization, test isolation and four CI gates. This revision **replaces** original exclusions of Loki/OpenTelemetry/local retention, adds real traces and monitoring, and overrides documentation claiming there is no local centralized store.

Execute original application logging/CI tasks, then this revision's numbered tasks in order. Introduce tracing regression tests before instrumentation changes. Retain original security rules: no bodies, query strings, auth headers, cookies, SQL, payment/OTP values, task payloads or arbitrary error messages. Original browser console reporting remains local-browser-only; this revision does not quietly open an unauthenticated browser ingestion endpoint.

Original plan includes implementation-time discovery gates and code examples; do not treat those examples as executed code. Run real installs/typechecks/config validators. No tasks.md transition or container start occurs during planning.

## Current context

- Read `AGENTS.md`, `infra/AGENTS.md`, `server/AGENTS.md`, `client/AGENTS.md`, `docs/development/testing.md` before implementation.
- Application services already live in `infra/compose.dev.yml`; infrastructure in `infra/docker-compose.yml`. Compose default network can connect optional overlay without changing database/storage services.
- Docker Desktop uses a VM: do not assume host `/var/lib/docker/containers` exists. Discover Docker logs through Engine API inside collector container, not Linux host log paths.
- Existing `client` port is 3000. Use Grafana **127.0.0.1:3001**, local diagnostics Loki **127.0.0.1:3101**, Tempo **127.0.0.1:3200**, Prometheus **127.0.0.1:9090**, Alloy UI **127.0.0.1:12345**, optional host OTLP **127.0.0.1:4318**. None bound to public interfaces.
- Existing service health endpoints check real PostgreSQL/Redis; mocked tests are not monitoring evidence. Existing hardcoded connected badge is not live monitoring.
- Services do not yet implement business API calls from Next to Django or real Celery workflows. Test trace propagation using dedicated test-only fixture, not a pretend production checkout endpoint.
- Prometheus is **metrics**, not a log database. Loki is logs; Tempo is traces; Grafana is dashboard/query UI. Request IDs are not distributed traces: W3C `traceparent` plus parent/child spans must be verified.

## Selection and scope

| Component | Purpose | Why here |
| --- | --- | --- |
| Grafana OSS | Explore logs, filters, dashboards, trace waterfall | One self-hosted UI for all three signal types |
| Loki | Store/search structured logs via LogQL | Small local filesystem deployment; filters JSON without full-text indexing every field |
| Prometheus | Scrape/store/query metrics, evaluate alerts | Request rates, error rates, latency, collector health |
| Tempo | Store/query traces via TraceQL | Correlates spans and trace IDs with Loki logs |
| Alloy | Collect Docker logs and receive OTLP | Supported Grafana collector; avoids deprecated Promtail |

Do not use Grafana's all-in-one development demo as production architecture. Do not add Elasticsearch, Kubernetes, Mimir, Kafka, cAdvisor, node_exporter, DB exporters or Alertmanager until an actual requirement justifies them. This foundation monitors application RED metrics and telemetry service health; host CPU/disk and deep PostgreSQL/RabbitMQ internals need future exporters. No claim of those metrics now.

Promtail is EOL as of March 2, 2026 according to upstream documentation; use Alloy.

### Data policy

- Logs: 7-day retention. Traces: 3 days. Metrics: 15 days plus 1 GB TSDB size cap. These are initial local defaults, not compliance policy.
- Separate named volumes for each backend. Never reuse shop media bucket or database volumes.
- Disable Grafana analytics/update/plugin checks and Loki/Tempo usage reporting; no plugin marketplace downloads at runtime.
- No external destination in Alloy configuration. Prometheus `remote_write` receiver is for **local Alloy**, not an online service.
- Container images/dependencies still require downloads during setup. “Private telemetry” is not equivalent to an air-gapped supply chain.
- Log only approved application JSON lines initially. Native infrastructure logs remain accessible via Compose, but do not centrally ingest unsanitized service/provider output by default.
- Request IDs/trace IDs are JSON fields or structured metadata, **never Loki stream labels or Prometheus metric labels**. Labels: Compose service and environment only.
- Default local tracing samples all spans for debugging. Span-derived metrics therefore represent observed requests accurately for instrumented processes. If sampling changes, stop treating trace-derived counts as full traffic; add unsampled application counters before changing this.

### Security prerequisite: Docker log discovery

**The Docker socket is a privileged host-control interface. Mounting it read-only does not make Docker API operations read-only. Do not expose it over TCP or mount it into Grafana, Loki, Tempo, Prometheus, or application containers.**

Use an internal Docker socket proxy permitting read-only container discovery/log API calls, with POST disabled and no host port. The proxy alone mounts socket. Alloy connects only to proxy. This reduces API surface but still allows sensitive container metadata access; Docker proxy compromise remains serious. Review the chosen proxy implementation and exact API allowlist before enabling collection. If user rejects socket access, stop and offer application OTLP log export rather than silently weakening isolation.

---

## Task 1 — Verify image/API compatibility and record exact pins

**Files:** create `infra/observability/versions.env.example`; later exact references in `.env.example`.

Each step: 2–5 minutes; commit checkpoints only if implementation commits authorized.

1. Read official release pages for `grafana/grafana`, `grafana/loki`, `grafana/tempo`, `grafana/alloy`, `prom/prometheus`, and selected Docker socket proxy. Select supported stable versions with matching config docs; never use `latest`.
2. During execution, verify tags exist with `docker buildx imagetools inspect <image>:<version>` and record manifest digests. Do not fabricate version numbers/digests. Pin resulting image references as root `.env.example` variables: `GRAFANA_IMAGE`, `LOKI_IMAGE`, `TEMPO_IMAGE`, `PROMETHEUS_IMAGE`, `ALLOY_IMAGE`, `DOCKER_SOCKET_PROXY_IMAGE`.
3. Discovery gate: Tempo monolithic/local block config below is Tempo 2.x-shaped. If selecting Tempo 3.x, read its **versioned** monolithic docs and rewrite relevant config before implementation; do not mix current latest docs with old binaries. Verify Loki `v13`/TSDB config, Alloy OTTL `keep_keys`, spanmetrics and Prometheus remote-write receiver support using selected versions' own validators.
4. Python: add `opentelemetry-api`, `opentelemetry-sdk`, `opentelemetry-exporter-otlp-proto-http` to `server/pyproject.toml`; resolve compatible versions and regenerate `server/requirements-dev.lock` in clean Python 3.12 environment. No auto-instrument-all package.
5. Client: `npm --prefix client install --save-exact @vercel/otel @opentelemetry/api`; add any required peer dependencies reported by installed package. Commit lockfile. Inspect installed API/type exports before adding SDK setup; upstream README API is a reference, not permission to ignore version differences.
6. Verification: clean `pip install -r server/requirements-dev.lock`, `npm --prefix client ci`, Python imports and client typecheck succeed. Suggested checkpoint: `build: pin local observability images and SDK dependencies`.

## Task 2 — Backend storage configuration

**Files:** create `infra/observability/loki.yml`, `infra/observability/tempo.yml`, `infra/observability/prometheus.yml`, `infra/observability/alerts.yml`.

1. RED: write Task 7 structural assertions for existence/retention/destinations first; run before config creation, expected missing-file failure.
2. Create `infra/observability/loki.yml`:

```yaml
auth_enabled: false
server:
  http_listen_port: 3100
common:
  path_prefix: /loki
  replication_factor: 1
  ring:
    instance_addr: 127.0.0.1
    kvstore:
      store: inmemory
schema_config:
  configs:
    - from: 2024-01-01
      store: tsdb
      object_store: filesystem
      schema: v13
      index:
        prefix: index_
        period: 24h
storage_config:
  filesystem:
    directory: /loki/chunks
compactor:
  working_directory: /loki/compactor
  retention_enabled: true
  delete_request_store: filesystem
limits_config:
  retention_period: 168h
analytics:
  reporting_enabled: false
```

3. Create `infra/observability/tempo.yml` for verified compatible monolithic image:

```yaml
server:
  http_listen_port: 3200
distributor:
  receivers:
    otlp:
      grpc:
        endpoint: 0.0.0.0:4317
      http:
        endpoint: 0.0.0.0:4318
ingester:
  max_block_duration: 5m
compactor:
  compaction:
    block_retention: 72h
storage:
  trace:
    backend: local
    wal:
      path: /var/tempo/wal
    local:
      path: /var/tempo/blocks
usage_report:
  reporting_enabled: false
```

4. Create `infra/observability/prometheus.yml`:

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s
rule_files: [/etc/prometheus/alerts.yml]
scrape_configs:
  - job_name: prometheus
    static_configs:
      - targets: [prometheus:9090]
  - job_name: alloy
    static_configs:
      - targets: [alloy:12345]
  - job_name: loki
    static_configs:
      - targets: [loki:3100]
  - job_name: tempo
    static_configs:
      - targets: [tempo:3200]
```

5. Create `infra/observability/alerts.yml`:

```yaml
groups:
  - name: local-observability
    rules:
      - alert: TelemetryTargetDown
        expr: up == 0
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "Local telemetry target is unavailable"
```

Only local Prometheus rule state is provided. No email/webhook receiver or external alert transport. Add application error/latency alert rules after Task 6 verifies exact exported metric names; do not fabricate names.

6. GREEN: run selected Loki config verification flag and `promtool check config /etc/prometheus/prometheus.yml` using pinned containers with read-only mounts. Tempo: start ephemeral container with config, confirm `/ready`, then stop it. Config syntax validation alone is not storage/ingestion evidence. Suggested checkpoint: `infra: configure private telemetry storage and retention`.

## Task 3 — Alloy pipeline with privacy filter

**File:** create `infra/observability/config.alloy`.

1. RED: structural test must reject an external exporter URL and request_id label. Test actual leak fixture in Task 8 before accepting pipeline.
2. Add this complete starting config, validating against selected Alloy version:

```alloy
logging {
  level = "info"
}

discovery.docker "shop" {
  host = "tcp://docker-socket-proxy:2375"
  filter {
    name = "label"
    values = ["observability.logs=true"]
  }
}

discovery.relabel "shop" {
  targets = discovery.docker.shop.targets
  rule {
    source_labels = ["__meta_docker_container_label_com_docker_compose_service"]
    target_label = "service"
  }
  rule {
    target_label = "environment"
    replacement = "development"
  }
}

loki.source.docker "shop" {
  host = "tcp://docker-socket-proxy:2375"
  targets = discovery.relabel.shop.output
  forward_to = [loki.process.safe.receiver]
}

loki.process "safe" {
  // Only approved structured application lines enter durable log storage.
  stage.match {
    selector = "{service=~\".+\"} !~ \"^\\{\""
    action = "drop"
  }
  stage.json {
    expressions = { event = "event", service = "service", timestamp = "timestamp" }
    drop_malformed = true
  }
  stage.match {
    selector = "{service=~\".+\"} !~ \"\\\"event\\\"\""
    action = "drop"
  }
  forward_to = [loki.write.local.receiver]
}

loki.write "local" {
  endpoint {
    url = "http://loki:3100/loki/api/v1/push"
  }
}

otelcol.receiver.otlp "local" {
  grpc { endpoint = "0.0.0.0:4317" }
  http { endpoint = "0.0.0.0:4318" }
  output {
    traces = [otelcol.processor.transform.safe.input]
  }
}

otelcol.processor.transform "safe" {
  error_mode = "propagate"
  trace_statements {
    context = "resource"
    statements = [
      `keep_keys(attributes, ["service.name", "deployment.environment.name"])`,
    ]
  }
  trace_statements {
    context = "span"
    statements = [
      `keep_keys(attributes, ["http.request.method", "http.method", "http.route", "http.response.status_code", "http.status_code", "request_id"])`,
      `set(name, "request")`,
      `set(name, attributes["http.route"]) where attributes["http.route"] != nil`,
      `set(status.message, "")`,
    ]
  }
  trace_statements {
    context = "spanevent"
    statements = [`keep_keys(attributes, ["exception.type"])`, `set(name, "event")`]
  }
  output {
    traces = [otelcol.processor.batch.local.input, otelcol.connector.spanmetrics.local.input]
  }
}

otelcol.processor.batch "local" {
  output { traces = [otelcol.exporter.otlp.tempo.input] }
}

otelcol.exporter.otlp "tempo" {
  client {
    endpoint = "tempo:4317"
    tls { insecure = true }
  }
}

otelcol.connector.spanmetrics "local" {
  histogram {
    explicit { buckets = ["5ms", "10ms", "25ms", "50ms", "100ms", "250ms", "500ms", "1s", "2s", "5s"] }
  }
  output { metrics = [otelcol.exporter.prometheus.local.input] }
}

otelcol.exporter.prometheus "local" {
  forward_to = [prometheus.remote_write.local.receiver]
}

prometheus.remote_write "local" {
  endpoint { url = "http://prometheus:9090/api/v1/write" }
}
```

**Important boundary:** JSON syntax and an event field do not prove arbitrary stdout is safe. Enable collection only for app containers whose emitter schema was tested. Before GREEN, tighten log event allowlist to original plan's exact event set and reconstruct stored JSON from allowed extracted fields if any app prints uncontrolled JSON. Do not rely on regex redaction for arbitrary secrets. Native Next diagnostics that are not approved JSON must be dropped. Labels/metadata forwarded by Docker discovery must not include container env or task args.

Trace sanitization is defense in depth; spans must also be minimized before leaving application process. Remove span links or allowlist link attributes at SDK/processor level; otherwise an auto-instrumenter may attach extra data outside span attributes/events. If selected Alloy version cannot sanitize links, disable links in SDK and regression-test exported payload. Treat filter errors as dropped telemetry, not bypass.

3. GREEN: `alloy validate` against mounted config exits 0; actual safe and secret-bearing fixtures in Task 8 prove storage behavior. Collector downtime must not break application requests; export is asynchronous and bounded. Suggested checkpoint: `infra: collect private logs traces and request metrics`.

## Task 4 — Compose overlay and Grafana provisioning

**Files:** create `infra/compose.observability.yml`, `infra/observability/grafana/datasources.yml`, `infra/observability/grafana/dashboards.yml`; modify `.env.example`, `package.json`, `infra/compose.dev.yml`.

1. RED: Task 7 tests fail until services/loopback/provisioning exist.
2. Create overlay:

```yaml
services:
  docker-socket-proxy:
    image: ${DOCKER_SOCKET_PROXY_IMAGE:?Pin Docker socket proxy image}
    environment:
      CONTAINERS: "1"
      POST: "0"
      LOG_LEVEL: warning
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
    networks: [collector-api]
    restart: unless-stopped
  grafana:
    image: ${GRAFANA_IMAGE:?Pin Grafana image}
    ports: ["127.0.0.1:3001:3000"]
    environment:
      GF_SECURITY_ADMIN_USER: ${GRAFANA_ADMIN_USER:?Set local Grafana user}
      GF_SECURITY_ADMIN_PASSWORD: ${GRAFANA_ADMIN_PASSWORD:?Set local Grafana password}
      GF_USERS_ALLOW_SIGN_UP: "false"
      GF_AUTH_ANONYMOUS_ENABLED: "false"
      GF_ANALYTICS_REPORTING_ENABLED: "false"
      GF_ANALYTICS_CHECK_FOR_UPDATES: "false"
      GF_ANALYTICS_CHECK_FOR_PLUGIN_UPDATES: "false"
    volumes:
      - grafana_data:/var/lib/grafana
      - ./observability/grafana/datasources.yml:/etc/grafana/provisioning/datasources/local.yml:ro
      - ./observability/grafana/dashboards.yml:/etc/grafana/provisioning/dashboards/local.yml:ro
      - ./observability/grafana/dashboards:/var/lib/grafana/dashboards:ro
    restart: unless-stopped
  loki:
    image: ${LOKI_IMAGE:?Pin Loki image}
    command: [-config.file=/etc/loki/local.yml]
    ports: ["127.0.0.1:3101:3100"]
    volumes:
      - ./observability/loki.yml:/etc/loki/local.yml:ro
      - loki_data:/loki
    restart: unless-stopped
  tempo:
    image: ${TEMPO_IMAGE:?Pin compatible Tempo image}
    command: [-config.file=/etc/tempo/local.yml]
    ports: ["127.0.0.1:3200:3200"]
    volumes:
      - ./observability/tempo.yml:/etc/tempo/local.yml:ro
      - tempo_data:/var/tempo
    restart: unless-stopped
  prometheus:
    image: ${PROMETHEUS_IMAGE:?Pin Prometheus image}
    command:
      - --config.file=/etc/prometheus/prometheus.yml
      - --storage.tsdb.path=/prometheus
      - --storage.tsdb.retention.time=15d
      - --storage.tsdb.retention.size=1GB
      - --web.enable-remote-write-receiver
    ports: ["127.0.0.1:9090:9090"]
    volumes:
      - ./observability/prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - ./observability/alerts.yml:/etc/prometheus/alerts.yml:ro
      - prometheus_data:/prometheus
    restart: unless-stopped
  alloy:
    image: ${ALLOY_IMAGE:?Pin Alloy image}
    command: [run, /etc/alloy/config.alloy, --storage.path=/var/lib/alloy, --server.http.listen-addr=0.0.0.0:12345, --disable-reporting]
    ports: ["127.0.0.1:12345:12345", "127.0.0.1:4318:4318"]
    volumes:
      - ./observability/config.alloy:/etc/alloy/config.alloy:ro
      - alloy_data:/var/lib/alloy
    networks: [default, collector-api]
    depends_on: [docker-socket-proxy, loki, tempo, prometheus]
    restart: unless-stopped
networks:
  collector-api:
    internal: true
volumes:
  grafana_data:
  loki_data:
  tempo_data:
  prometheus_data:
  alloy_data:
```

Discovery gate: proxy images differ in API flags and healthcheck tools. Above environment matches common Docker socket proxy conventions; verify actual selected proxy accepts container listing, inspect and logs with GET, denies POST/container creation and has no host port. Do not ship an unverified privilege boundary.

Add tested healthchecks using commands actually present in pinned images; do not assume `curl`/shell exists in distroless images. If no in-image tool exists, use external readiness probe from Task 8 and document why that container lacks healthcheck. Replace simple `depends_on` with healthy condition only for services with genuine healthchecks.

3. Add **only** `labels: {observability.logs: "true"}` to `server` and `client` in `infra/compose.dev.yml`. Do not label infrastructure containers yet. Worker label added when real worker service exists.
4. Add environment to backend/client overlay services: `OTEL_ENABLED: "true"`, `OTEL_EXPORTER_OTLP_ENDPOINT: http://alloy:4318`, `OTEL_EXPORTER_OTLP_PROTOCOL: http/protobuf`, `OTEL_SERVICE_NAME: django` or `next`, `OTEL_TRACES_SAMPLER: always_on`, `OTEL_METRICS_EXPORTER: none`, `OTEL_LOGS_EXPORTER: none`. Defaults without overlay remain disabled. Do not add `NEXT_PUBLIC_` exporter endpoints.
5. Provision `infra/observability/grafana/datasources.yml`:

```yaml
apiVersion: 1
datasources:
  - name: Loki
    uid: loki
    type: loki
    access: proxy
    url: http://loki:3100
    jsonData:
      derivedFields:
        - name: TraceID
          matcherRegex: '"trace_id"\s*:\s*"([a-f0-9]{32})"'
          datasourceUid: tempo
          url: '$${__value.raw}'
  - name: Prometheus
    uid: prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
  - name: Tempo
    uid: tempo
    type: tempo
    access: proxy
    url: http://tempo:3200
    jsonData:
      tracesToLogsV2:
        datasourceUid: loki
        spanStartTimeShift: -1m
        spanEndTimeShift: 1m
        filterByTraceID: false
        customQuery: true
        query: '{service=~"server|client"} | json | trace_id = "$${__trace.traceId}"'
```

Grafana provisioning env-expands `$`; doubled `$` is intentional. Verify rendered log/trace links in UI; don't just assert config text.

6. Provision `infra/observability/grafana/dashboards.yml`:

```yaml
apiVersion: 1
providers:
  - name: local
    type: file
    disableDeletion: true
    options:
      path: /var/lib/grafana/dashboards
```

7. Root script `obs:up`: `docker compose --env-file .env -f infra/docker-compose.yml -f infra/compose.dev.yml -f infra/compose.observability.yml up -d --build`; `obs:logs`: same file list followed by `logs --tail 100 -f grafana loki tempo prometheus alloy`. `obs:status`: same file list followed by `ps`. Do not add destructive reset command.
8. GREEN: `docker compose ... config --quiet`, start stack, readiness endpoints succeed, Grafana local login works, proxy denies write API, existing app health stays healthy. Grafana password goes in ignored root `.env` through user-owned secure setup, never chat or committed template. Suggested checkpoint: `infra: add optional local Grafana observability stack`.

## Task 5 — Real spans and log/trace correlation

**Files:** create `server/apps/core/telemetry.py`, `server/tests/test_telemetry.py`; modify `server/apps/core/middleware.py`, `server/apps/core/logging.py`, `server/config/settings.py`; create `client/src/instrumentation.node.ts`; extend `client/src/instrumentation.ts`, `client/src/lib/error-reporting.ts` and their tests.

1. RED: write tests before instrumentation. Assert disabled telemetry creates no network exporter; valid inbound W3C parent trace ID is inherited; generated span has server kind, status and route template; no raw path/query/body/header/exception message; formatted application log contains same 32-hex trace_id and 16-hex span_id; sequential requests cannot reuse context. Use OpenTelemetry in-memory exporter in tests, never actual network. These imports must be checked against installed SDK from Task 1.
2. Minimal Python design: lazily create one `TracerProvider(Resource.create({"service.name": "django"}))` when `OTEL_ENABLED` is true; attach bounded `BatchSpanProcessor(OTLPSpanExporter(endpoint=<configured-local-base>/v1/traces))`. Use W3C `TraceContextTextMapPropagator.extract` on incoming `traceparent`, ignore baggage and arbitrary tracestate. Start `SpanKind.SERVER` around existing request logging middleware with `record_exception=False`, `set_status_on_exception=False`; set safe route/method/status explicitly in finally. On 500, set `StatusCode.ERROR` without description. Do not automatically instrument psycopg/Redis/celery/provider I/O in this first slice.
3. Add trace fields to original Python formatter from `trace.get_current_span().get_span_context()` only when valid. Ensure completion log runs **inside** active span, then close span and request ContextVar. Cleanup must survive downstream failure. Provider flush/shutdown registered once with process lifecycle; no per-request SDK init or blocking flush.
4. Client SDK uses native Next instrumentation; complete register block to append to existing hook file:

```typescript
export async function register() {
  if (process.env.NEXT_RUNTIME === "nodejs" && process.env.OTEL_ENABLED === "true") {
    await import("./instrumentation.node");
  }
}
```

Create `client/src/instrumentation.node.ts`:

```typescript
import { registerOTel } from "@vercel/otel";

registerOTel({
  serviceName: "next",
  instrumentations: [],
});
```

This disables automatic fetch instrumentation; Next framework spans remain. Next's native fetch/context behavior must be verified before claiming downstream propagation. Existing `onRequestError` remains intact. `OTEL_EXPORTER_OTLP_ENDPOINT` explicitly points at local Alloy; no automatic hosted integration allowed. Do not enable verbose Next span capture.
5. In server-side TypeScript reporting, use `@opentelemetry/api` `trace.getActiveSpan()?.spanContext()` to add trace_id/span_id only when valid. Avoid bringing Node SDK into browser bundle; API package alone is safe, or split server-only helper if bundle inspection shows problem. Browser events without a trace remain null, not fake IDs.
6. **Discovery/code-completion gate:** Python SDK initialization and span lifecycle are version-sensitive and must be authored against installed definitions. Before implementation handoff, supply complete `telemetry.py` and middleware diff with in-memory regression tests; do not guess SDK constructors or global provider resets. This gate is explicitly pending, not a tested code snippet.
7. GREEN: unit tests, typecheck/lint/build and Task 8 trace roundtrip pass. Add test-only Next route fixture which invokes Django health with explicit `traceparent` injected by OTel API propagator; assert one Tempo trace contains parent Next span and child Django span. Fixture must live under temporary E2E app root or be compiled only for test environment, never expose a debugging route in production. If no business API path exists, trace propagation test is harness evidence only.
8. Suggested checkpoint: `feat(observability): correlate safe app logs with local traces`.

## Task 6 — Provision practical dashboards and alert queries

**Files:** create `infra/observability/grafana/dashboards/overview.json`, `infra/observability/grafana/dashboards/logs.json`; extend `infra/observability/alerts.yml`.

1. RED: verify Grafana API cannot find expected dashboard UIDs before provisioning. Save dashboard JSON only after confirming actual metric label/name output from live Alloy spanmetrics. These names vary with component version; no invented PromQL.
2. Create two small dashboards through Grafana UI, export JSON, remove instance IDs and datasource secrets, commit provisioned JSON. Exact UIDs: `shop-overview`, `shop-logs`. Datasource references must use `prometheus`/`loki` UIDs, not numeric local IDs.
3. `shop-overview` panels: telemetry `up` by job; request rate, error rate and p95 duration by service from observed spanmetrics; recent Django ERROR events; links to Explore logs and Tempo traces. Use server spans only for traffic panels so nested Next spans do not inflate request totals. If current schema lacks span-kind/status label, fix collection first, not dashboard math.
4. `shop-logs`: service dropdown (`server`, `client`), level filter, time range, text search, request_id and trace_id filters. Starting LogQL:

```logql
{service="server"} | json | level="ERROR"
```

```logql
{service=~"server|client"} | json | request_id="<copy-response-X-Request-ID>"
```

```logql
{service=~"server|client"} | json | trace_id="<copy-trace-id>"
```

Text inside angle brackets is user search input, not runtime config. Do not index these values as labels.
5. Add sustained application 5xx ratio and p95 latency rules using real discovered metric names; minimum traffic guard prevents alerting on one isolated dev request. Verify with `promtool test rules` fixtures for normal traffic, failures, no traffic, and service down. Rules visible in local Prometheus UI; external notification delivery remains excluded.
6. GREEN: Grafana API returns both dashboard UIDs after restart; all panels resolve actual data, no unknown metric/datasource; click log trace link, inspect waterfall and return to matching logs. Suggested checkpoint: `feat(observability): provision local log and request dashboards`.

## Task 7 — Configuration regression tests and CI gate

**Files:** create `server/tests/test_observability_config.py`, `infra/observability/test_alerts.yml`; extend `.github/workflows/ci.yml`.

Write these assertions before owning configuration tasks. Complete baseline test:

```python
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]


def test_observability_is_local_and_has_persistent_storage():
    config = yaml.safe_load((ROOT / "infra/compose.observability.yml").read_text())
    services = config["services"]
    assert set(services) == {"grafana", "loki", "tempo", "prometheus", "alloy", "docker-socket-proxy"}
    for name, service in services.items():
        for port in service.get("ports", []):
            assert str(port).startswith("127.0.0.1:"), (name, port)
        if name != "docker-socket-proxy":
            assert "docker.sock" not in str(service.get("volumes", []))
    assert "ports" not in services["docker-socket-proxy"]
    assert services["docker-socket-proxy"]["environment"]["POST"] == "0"
    assert len(config["volumes"]) == 5


def test_retention_and_local_export_destinations():
    base = ROOT / "infra/observability"
    loki = yaml.safe_load((base / "loki.yml").read_text())
    assert loki["limits_config"]["retention_period"] == "168h"
    assert loki["analytics"]["reporting_enabled"] is False
    tempo = yaml.safe_load((base / "tempo.yml").read_text())
    assert tempo["compactor"]["compaction"]["block_retention"] == "72h"
    alloy = (base / "config.alloy").read_text()
    assert 'http://loki:3100/loki/api/v1/push' in alloy
    assert 'http://prometheus:9090/api/v1/write' in alloy
    assert 'tempo:4317' in alloy
    assert 'grafana.net' not in alloy
    assert 'target_label = "trace_id"' not in alloy
    assert 'target_label = "request_id"' not in alloy
```

1. RED: `(cd server && pytest tests/test_observability_config.py -q)` before configs; expect missing files. GREEN after Tasks 2–4.
2. Add `observability` CI job, independent from existing four jobs, with 15-minute timeout. Run config tests and pinned binary validators plus full Task 8 roundtrip on disposable volumes. Use synthetic safe events only. Update original `server/tests/test_ci_workflow.py` expected job set to include `observability`; write failing test before workflow change.
3. For CI, generate dedicated synthetic Compose variables from committed test template, not root developer `.env`. Use `--project-name shop-obs-ci`; no reuse of development volumes. Bind ephemeral localhost ports or run probes inside CI Docker network to avoid host-port collisions.
4. GitHub-hosted CI necessarily runs synthetic test telemetry on GitHub's machine. **Do not ship workstation/application logs there or upload Loki/Tempo/Prometheus volumes.** If user means no telemetry, even synthetic, may execute off-device, retain static validators in Actions and require runtime smoke locally; ask before relaxing their privacy intent.
5. No failure log dump automatically uploaded from collector stack; retain sanitized test assertion report only. Suggested checkpoint: `ci: validate private telemetry pipeline`.

## Task 8 — Real end-to-end smoke and privacy checks

**Files:** create `scripts/check_observability.py` using stdlib HTTP/JSON/UUID/time only; create `infra/compose.observability.test.yml` for approved synthetic log fixture.

Each bullet is a small separately verified step; script must use bounded polling (60s deadline, nonzero exit on failure), not fixed long sleeps or silent skip.

1. RED: write script to query readiness, Loki, Tempo and Prometheus before stack starts; run `python scripts/check_observability.py`; expect connection failure with explicit component name.
2. Implement check requests to `http://127.0.0.1:3001/api/health`, `http://127.0.0.1:3101/ready`, `http://127.0.0.1:3200/ready`, `http://127.0.0.1:9090/-/ready`, `http://127.0.0.1:12345/-/ready`. Expect HTTP 200; Grafana health JSON database `ok`.
3. Generate a synthetic UUID, call real Django `/api/health/` with `X-Request-ID`, and poll Loki `/loki/api/v1/query_range` for `{service="server"} | json | request_id="UUID"`; assert exact record status 200 and nonempty trace_id. Do not use a manually pushed Loki record as sole proof of Docker collection.
4. Query Tempo `/api/traces/<trace_id>`; assert stored trace exists and matching service/span. Query Prometheus `/api/v1/query` with `up`; assert each configured scrape target is 1. Send several known health requests then assert spanmetrics request counters increase and durations appear.
5. Test-only fixture emits safe JSON, malformed JSON and sensitive non-JSON marker. Verify approved synthetic event appears, malformed/native lines do not. For spans, inject synthetic token into URL/query, exception message/event attrs, resource attrs and link attrs; inspect returned trace JSON and assert token absent everywhere. Do not intentionally emit real secrets.
6. Stop Alloy; real health requests still return successfully within normal latency budget. Restart Alloy; subsequent requests export. Do not assert zero loss or exactly-once logs during crashes; queues/checkpoints have bounds.
7. Restart Loki/Tempo/Prometheus/Grafana without deleting volumes; previously recorded data and dashboard UIDs survive. Confirm retention settings in active runtime config. Do not pretend a short smoke proves seven-day expiry; test expiry with separate short-retention ephemeral fixture if supported.
8. Record `docker stats --no-stream` and disk/volume use for actual local stack. Do not promise a RAM number without measurement. If stack strains workstation, keep overlay opt-in, reduce retention/export volume, then measure again; no application correctness tradeoff.
9. GREEN: script exits 0 with named PASS lines for readiness, log lookup, trace lookup, metrics lookup, privacy and persistence; browser dashboard check succeeds. Run full existing lint/test/build/E2E gates afterward.
10. Suggested checkpoint: `test(observability): verify local telemetry and privacy end to end`.

## Task 9 — Runbook and roadmap updates

**Files:** update `docs/development/observability.md`, `docs/development/testing.md`, `README.md`, `tasks.md`, `infra/AGENTS.md` only where operational commands changed.

1. Document `npm run obs:up`, `obs:status`, `obs:logs`; Grafana URL `http://127.0.0.1:3001`; local login setup; two dashboards; exact LogQL/TraceQL/PromQL validated in Task 8. Explain local host apps use `http://127.0.0.1:4318`, containers `http://alloy:4318`.
2. Document privacy defaults, backend native-diagnostic exclusions, socket proxy privilege boundary, retention, volume backups, safe stop/restart, no automatic volume deletion. Never call `docker compose down -v` against shared application stack.
3. Explain full tracing limitations: server spans and verified test parent/child propagation exist; browser RUM, true Celery delivery spans and DB spans still pending. Celery request header correlation from original plan remains but is not a Tempo worker span unless instrumented.
4. Add `TASK-OBS-LOCAL`, mark active during implementation and verified only after roundtrip/privacy/restart checks. Keep broad pending domain E2E tasks pending.
5. Suggested checkpoint: `docs: explain private Grafana logs metrics and traces`.

---

## Acceptance and final checks

Implementation commands (not executed in planning):

```sh
npm run obs:up
npm run obs:status
python scripts/check_observability.py
(cd server && pytest tests/test_observability_config.py tests/test_telemetry.py -q)
npm run lint
npm --prefix client run typecheck
npm --prefix client run test
(cd server && pytest --cov=apps --cov-fail-under=85)
npm --prefix client run build
npm --prefix client run test:e2e
git diff --check
```

Expected: all exit 0, app checks retain original behavior, dashboard usable at localhost:3001, actual app-generated event searchable in Loki, linked trace retrievable in Tempo, Prometheus query has real request/duration samples, no sensitive marker stored, and data survives service restart. Never report success from container `running` alone.

- [ ] All telemetry storage local named volumes, no cloud destinations.
- [ ] All published ports loopback; Grafana authenticated; no default committed password.
- [ ] Docker API access narrowly proxied; writes denied; no public proxy port.
- [ ] User can search by service, level, time, request_id and trace_id.
- [ ] Trace waterfall linked to matching structured logs.
- [ ] Metrics show observed request rate/errors/latency and telemetry service health.
- [ ] Native/private payload lines not centrally stored; spans sanitized before export and at collector.
- [ ] Retention configured, backups/limitations documented, persistence tested.
- [ ] Actual CI validation verified, or remote execution explicitly unrun.

## Risks / explicit decisions

- Six extra containers (including socket proxy) cost RAM/disk; keep optional, measure before promising lightness. Local single-node filesystem storage is not HA and not production backup strategy.
- Loki/Tempo/Prometheus have no authentication in this local design; loopback host binding is not authorization against other local processes or containers. Shared-host or remote deployment requires authenticated reverse proxy/TLS, restricted networks and reviewed firewall policy before exposure.
- Grafana analytics disabled does not prove every dependency is air-gapped. Validate configuration and observe runtime outbound traffic in isolated smoke if strict no-egress required; never advertise total no-network guarantee without enforcement.
- Request IDs may be user-supplied after UUID validation; tracing context is untrusted correlation, not identity or authorization.
- App shutdown can lose buffered spans; export failure must not interrupt business requests. Retrying collectors are not guaranteed durable audit trails.
- Browser logs are not automatically uploaded to local Grafana. Adding browser collection later requires same-origin validated ingestion, rate limiting and size bounds; never publish internal OTLP/Loki ingest directly to browser.
- Prometheus is not a billing ledger; spanmetrics depends on tracing coverage and sampling. Avoid sensitive/high-cardinality labels.
- Container image pinning, complete SDK lifecycle tests and actual generated dashboards are execution prerequisites, not things verified during planning.

## Sources consulted

- Prometheus concepts: https://prometheus.io/docs/introduction/overview/
- Loki overview: https://grafana.com/docs/loki/latest/get-started/overview/
- Tempo overview: https://grafana.com/docs/tempo/latest/
- Alloy Docker collection: https://grafana.com/docs/alloy/latest/reference/components/loki/loki.source.docker/
- Promtail EOL: https://grafana.com/docs/loki/latest/send-data/promtail/
- Span-derived RED metrics: https://grafana.com/docs/alloy/latest/reference/components/otelcol/otelcol.connector.spanmetrics/
- Next 15 OpenTelemetry: https://nextjs.org/docs/15/app/guides/open-telemetry
- `@vercel/otel` configuration: https://github.com/vercel/otel/tree/main/packages/otel

## Planning status

Only plan markdown changed. No dependencies installed, Docker stack started, SDK code changed, or GitHub actions performed. Runtime/API compatibility gates remain explicitly unverified until implementation.
