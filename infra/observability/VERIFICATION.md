# Local verification evidence

Executed 2026-10-30; Docker Desktop Engine 29.9.2, Compose v5.6.1. No root `.env` read; shared development stack not started.

- `python scripts/check_observability.py --static`: exit 0.
- `python scripts/check_observability.py --ci`: exit 0; project `shop-obs-smoke-952fed30b5` cleaned own containers/volumes.
- `python scripts/check_observability.py --ci --keep`: exit 0 after final privacy/template changes; project `shop-obs-smoke-0674df1e91` retained for parent inspection.
- Loki `-verify-config=true`, Alloy `validate`, Prometheus `promtool check config`, `promtool test rules`: exit 0. Rules tested no traffic, healthy traffic, sustained errors and target down. Latency threshold config validates; dedicated latency firing fixture not yet added.
- Real Docker collection found approved JSON; nested secret discarded; native/malformed/unapproved lines absent. Only service/environment stream labels. Parse query fields are query-time, not indexed labels.
- OTLP trace `e65c1cceecdd42bfb058883376cde8dd`, request `455d8902-aa78-464a-abe7-a3d241a21d84`: two related parent/child spans stored; third linked span dropped. URL/resource/scope/status/event/link marker absent from persisted trace and metrics.
- Four scrape targets up; `traces_span_metrics_calls_total` increased; `traces_span_metrics_duration_milliseconds_bucket` present. Server kind/status labels verified. All overview PromQL panels returned data.
- Grafana API authenticated, both dashboard UIDs and three datasources present before/after restart. Backend restart preserved logs/traces/metrics. Browser waterfall/link clicking not exercised.
- Proxy actual POST/PUT/PATCH/DELETE + archive/export/image routes returned 403. Inspect required by Alloy; denying it prevented log tailing. Proxy scope remains host-wide reads.
- Collector stop did not break synthetic HTTP fixture. Real Django/Next SDK integration subsequently passed via `scripts/check_app_telemetry.py`: inherited parent IDs, matching Django Loki records, private query/header/cookie marker absent. Parent read back Django trace `ea51f4ee45e3414091e947c20ea6b97d` and Next trace `6390202d8b17422ca8c8c2c25924781f` from Tempo (HTTP 200) before cleanup. Trusted-origin outgoing fetch propagation passed actual HTTP regression; foreign origin received no traceparent. No business Next-to-Django route or collector-outage application timing claim.
- Effective runtime configs: Loki retention 1w/reporting false; Tempo compactor block_retention 72h/reporting false; Prometheus retention 15d/1GiB. Multi-day expiry not exercised.
- `git diff --check`: exit 0.
- Parent independently reran full `python3 scripts/check_observability.py --ci`: exit 0, disposable project `shop-obs-smoke-c7c42d7b1a` removed afterward.
- Route regression: failed before allowlist fix; final full smoke project `shop-obs-smoke-3887c2ea5c` passed root `/` plus all six API templates (leading/no-leading slash), unknown private route exclusion, storage, privacy, dashboards and persistence; cleaned afterward.

Historical inspection containers (now removed after parent read-back): prefix `shop-obs-smoke-0674df1e91-`, suffix `-1`, services grafana/loki/tempo/prometheus/alloy/docker-socket-proxy/server. Ports grafana 59509, loki 53867, tempo 34205, prometheus 43351, alloy 54853, OTLP 60331, synthetic fixture 37487. All 127.0.0.1. Dedicated random smoke secret mount `/home/specter/.hermes/cache/scratch/shop-obs-smoke-0674df1e9174hsyv4r/password`; value never printed. Earlier passing project `shop-obs-smoke-b80f409211` was removed by parent after verification; no shared development containers/volumes touched.

Measured memory: Grafana 370.1 MiB, Alloy 64.86 MiB, Loki 58.39 MiB, Prometheus 52.08 MiB, Tempo 50.17 MiB, proxy 15.18 MiB, fixture 14.54 MiB. Snapshot only, not capacity guarantee. Container `du`: Grafana 1.7M, Prometheus 440K. Full per-volume disk accounting not exercised.

Image registry manifests verified with `docker buildx imagetools inspect`; exact pins in `versions.env.example`. Docker Hub daemon pulls repeatedly hit auth TLS timeouts. Workaround downloaded registry blobs through host Python, verified SHA-256 against manifests, imported OCI archives; Prometheus official quay.io mirror had identical manifest digest. No synthetic/fake registry output used. Workaround scripts live only scratch, not CI dependency.
