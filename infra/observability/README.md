# Private local telemetry

Run synthetic validation from repository root:

```sh
python scripts/check_observability.py --static
python scripts/check_observability.py --ci
```

Requires Python stdlib, Docker Engine and Compose. `--ci` creates UUID-named project, ephemeral loopback ports, dedicated synthetic scope, random disposable Grafana password file, and separate volumes. Explicit empty env file prevents reading root `.env`; caller credentials excluded. On completion/failure removes only its own project volumes. No raw service logs or telemetry volumes uploaded. `--keep` retains project, scratch password and handles for local inspection; remove retained project explicitly when finished.

Image defaults are immutable registry-verified manifest references; see `versions.env.example`. Tempo deliberately uses maintained 2.10.10 with `distributor.receivers.otlp.protocols.grpc`, not incompatible Tempo 3 config. Config validators and readiness use real pinned binaries. External readiness avoids assuming distroless images contain shell/curl.

## Development integration

Root `npm run obs:up`, `obs:status` and `obs:logs` merge `docker-compose.yml`, `compose.dev.yml`, `compose.observability.yml` and `compose.observability.apps.yml`. The last overlay enables application SDK export; standalone synthetic checks intentionally omit it. Do not merge test compose into development. Set `OBS_GRAFANA_PASSWORD_FILE` to dedicated user-generated file outside repository; do **not** put Grafana password in root `.env`, because backend imports that whole file. Secret mounted only in Grafana. User `observer` defaults; `GRAFANA_ADMIN_USER` overrides. Root scripts should pass password file path via process environment.

Configure application processes only when overlay enabled:

- `OTEL_ENABLED=true`
- `OTEL_EXPORTER_OTLP_ENDPOINT=http://alloy:4318` (host apps: `http://127.0.0.1:4318`)
- `OTEL_EXPORTER_OTLP_PROTOCOL=http/protobuf`
- `OTEL_SERVICE_NAME=django` / `next`
- `OTEL_TRACES_SAMPLER=always_on`
- `OTEL_METRICS_EXPORTER=none`, `OTEL_LOGS_EXPORTER=none`

Never expose exporter through `NEXT_PUBLIC_`. Development server/client labels opt in approved JSON only. Collector requires matching `observability.scope=development`; smoke uses unique scope so workstation apps never enter synthetic storage.

Grafana default `http://127.0.0.1:3001`, authenticated. Dashboard UIDs `shop-overview`, `shop-logs`; service, level, time, request ID, trace ID and text filters; Loki trace link opens Tempo. Backend ports loopback only. Backend telemetry network excludes apps; only Alloy joins app default network. Docker Desktop suppresses published ports for internal-only networks, so telemetry network is separate but not Docker `internal`; no claim of enforced air gap. Reporting/update/plugin preinstall disabled, exporters local; supply-chain downloads still use network.

## Privacy and limits

Log pipeline reconstructs allowlisted JSON, drops unknown/malformed/native lines and arbitrary nested objects. IDs stay JSON fields, never stream or metric labels. Route ceiling currently health/unmatched only; extend finite allowlist alongside verified route templates. Resource service names, HTTP method, status and span names normalized before spanmetrics. Scope/name/status/event text minimized. Linked spans **dropped**: Alloy accepts `set(links, [])` syntax but fails runtime conversion; filter `Len(links) > 0` fails closed. SDKs must not emit links.

**Docker socket is privileged even when mounted read-only.** HAProxy permits only GET/HEAD ping/version, container listing/inspect/logs and network listing. All writes and archive/export/exec/image/volume routes denied. Alloy requires inspect to determine TTY framing: denying inspect prevented actual ingestion. Residual host-wide metadata/env/log read remains serious; opt-in labels constrain collector, not compromised proxy. Socket proxy has no host port and isolated internal network. Reject socket access if this boundary unacceptable; use separately approved OTLP log pipeline instead.

Loki 7 days; Tempo 3 days; Prometheus 15 days and 1 GB cap. Each backend plus Alloy has own named volume. Short smoke proves restart persistence, not multi-day expiration. Stop/restart without deleting volumes. Never `down -v` shared development stack. No audit durability, HA, browser ingestion, host exporters, or external alert delivery. Error/latency rules use observed server spans; changing sampling invalidates full-traffic interpretation.

Synthetic smoke proves Docker logs, sanitized OTLP parent/child storage, local spanmetrics counters/histograms, target health, Grafana provisioning, proxy denial and backend restart persistence. It does not prove application SDK propagation or business journeys; parent owns full app integration. Native infrastructure logs stay in Docker, not central collection.
