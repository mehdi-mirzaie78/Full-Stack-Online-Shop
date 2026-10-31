# Private logs, metrics and traces

## Signal ownership

- **Loki** stores approved structured application logs; LogQL filters service, severity, request ID and trace ID.
- **Tempo** stores OpenTelemetry traces; trace IDs connect spans with matching logs.
- **Prometheus** stores numeric metrics and evaluates local alert rules. It is not a log database.
- **Grafana OSS** provides dashboard/search UI for all three backends.
- **Alloy** collects opt-in Docker logs and receives local OTLP telemetry.

No cloud logging account or external export destination is required. Application telemetry stays in local Docker volumes. Installing images and packages still requires downloads; this is not an air-gapped installation.

## Start and inspect

Use existing root `.env` for shop development settings. Create a separate password file outside this repository, readable by Grafana's container user, and keep its parent directory private. Set `OBS_GRAFANA_PASSWORD_FILE` to its absolute path; **do not put the password itself in root `.env`**, which is imported by backend containers. Grafana username defaults to `observer`.

```sh
export OBS_GRAFANA_PASSWORD_FILE=/absolute/path/to/private/grafana-password
npm run obs:up
npm run obs:status
npm run obs:check
```

Open `http://127.0.0.1:3001`, sign in, then open **Shop overview** or **Shop logs**. `npm run obs:logs` follows collector/backend diagnostics. The overlay enables source-minimized application tracing; ordinary `npm run docker:up` does not enable telemetry. Do not start both with different Compose project names against the same shop data.

With application overlay already running, `python3 scripts/check_app_telemetry.py` checks real Django/Next SDK traces, matching Django Loki logs and privacy on synthetic probe requests. It does not start applications; optional URL flags support isolated test ports. It permits unhealthy Django health (503) to verify failure telemetry; use application health separately to diagnose dependency state.

Next fetch context propagation is restricted to exact `OTEL_BACKEND_ORIGIN` (overlay: `http://server:8000`). Other origins do not receive `traceparent`. Trusted requests carrying trace context reject automatic redirects, including same-origin redirects, because native fetch otherwise forwards tracing headers across origins; callers can explicitly use `redirect: "manual"` and validate the next destination. Untraced and foreign requests retain normal redirect behavior. Current storefront has no business API loader; SDK propagation tests are not a completed checkout waterfall.

For isolated synthetic verification, without reading developer `.env` or collecting developer logs:

```sh
npm run test:observability
```

This starts a unique test project and removes only that project's containers/volumes afterward. Run `python3 scripts/check_observability.py --static` for static-only checks. More details: [collector runbook](../../infra/observability/README.md).

Example Explore queries:

```logql
{service="server"} | json | level="ERROR"
```

```logql
{service=~"server|client"} | json | request_id="paste-response-X-Request-ID"
```

Trace IDs remain JSON fields, not indexed labels. A log's TraceID link opens Tempo. Backend diagnostic ports are localhost-only: Loki 3101, Tempo 3200, Prometheus 9090, Alloy 12345, OTLP 4318. For host-run apps explicitly set `OTEL_ENABLED=true` and `OTEL_EXPORTER_OTLP_ENDPOINT=http://127.0.0.1:4318`; Docker apps use internal Alloy URL supplied by overlay.

Collector route/event allowlists deliberately cover today's health/storefront foundation. Extend finite route templates alongside future APIs and regression tests; unknown templates become `unmatched`, never raw URLs. Metrics initially cover observed server spans and four telemetry scrape targets, not host CPU/disk or full DB/broker internals. Local rules do not deliver external notifications.

## Safety

Application reporters deliberately omit bodies, query strings, authorization, cookies, SQL, task arguments/results, and exception values. Python errors keep safe file/function/line frames. Correlation identifiers are not credentials or authorization evidence. Native framework output is not automatically safe and must not be blindly ingested.

Docker API access is privileged. A read-only socket mount does not make API operations read-only. Only the internal socket proxy may mount it; collector connects through that restricted proxy. Never expose proxy over a host port. Other local processes and containers may still reach loopback/internal services; remote/shared-host deployment requires additional authentication, TLS and network restrictions.

Grafana requires a local password, stored only in ignored local configuration. Never paste credentials into chat, commit real configuration, or publish backend ingest ports to browsers.

## Data lifecycle

Initial retention: logs seven days, traces three days, metrics fifteen days with a TSDB size cap. Retention is not a backup. Named telemetry volumes are separate from shop DB/media. Restarting containers preserves volumes; deleting volumes destroys history. No destructive reset command belongs in normal troubleshooting.

Browser console events are not automatically uploaded to Loki. Central browser reporting needs a validated, size-limited, rate-limited same-origin receiver; do not expose Loki/OTLP directly. Celery header correlation is not proof of real broker delivery or worker tracing. Host/DB/broker metrics need dedicated exporters; initial request metrics do not claim that coverage.

## CI

`.github/workflows/ci.yml` separates static checks, client tests/build, server tests/coverage, browser smoke and private telemetry validation. A failed gate must fail the job; unavailable dependencies must not silently skip tests.

Server CI uses isolated PostgreSQL/Redis with synthetic credentials. Browser smoke covers current storefront/error recovery, not future checkout/auth/RBAC journeys. Synthetic telemetry in CI does not include workstation data. Never upload telemetry volumes, root `.env`, environment dumps or real provider errors as artifacts.

Test reports and browser traces/screenshots expire after seven days. GitHub branch protection must be configured separately by repository owner; workflow YAML alone does not block merges. Hosted CI is not verified until authorized push/PR runs it.
