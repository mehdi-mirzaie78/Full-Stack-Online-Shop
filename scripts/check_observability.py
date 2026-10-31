"""Private telemetry checks; --ci starts isolated synthetic stack, never root .env.

--ci removes only its own UUID-named containers/volumes, even on failure.
--keep retains smoke containers/volumes for inspection; prints project handle.
Default: structural checks plus readiness of existing local stack.
"""
import argparse
import base64
import contextlib
from http.client import HTTPException
import json
import os
from pathlib import Path
import socket
import subprocess
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "infra/observability"
KNOWN_ROUTES = ("/",) + tuple(
    prefix + route for route in ("api/health/", "api/health/db/", "api/health/redis/",
                                "api/schema/", "api/docs/", "api/redoc/") for prefix in ("", "/")
)


def structural():
    config = json.loads((ROOT / "infra/compose.observability.yml").read_text())
    services = config["services"]
    assert set(services) == {"grafana", "loki", "tempo", "prometheus", "alloy", "docker-socket-proxy"}
    assert len(config["volumes"]) == 5
    for name, service in services.items():
        assert "@sha256:" in service["image"], name
        assert all(port.startswith("127.0.0.1:") for port in service.get("ports", [])), name
        if name != "docker-socket-proxy":
            assert "docker.sock" not in str(service)
    assert "ports" not in services["docker-socket-proxy"]
    assert services["grafana"]["environment"]["GF_SECURITY_ADMIN_PASSWORD__FILE"]
    assert config["networks"]["collector-api"]["internal"]
    assert all("default" not in services[n]["networks"] for n in ["grafana", "loki", "tempo", "prometheus"])
    assert "default" not in services["tempo"]["networks"]
    alloy = (BASE / "config.alloy").read_text()
    assert 'target_label = "trace_id"' not in alloy
    assert 'target_label = "request_id"' not in alloy
    assert "toJson $d" in alloy and 'Len(links) > 0' in alloy
    assert 'observability.scope=' in alloy
    destinations = ["http://loki:3100/loki/api/v1/push", "http://prometheus:9090/api/v1/write", "tempo:4317"]
    assert all(value in alloy for value in destinations)
    for path in (BASE / "grafana/dashboards").glob("*.json"):
        json.loads(path.read_text())
    print("PASS structure: loopback, pinned images, separate volumes, secret file, local exporters")


def http(url, data=None, auth=None):
    headers = {}
    if data is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(data).encode()
    if auth:
        headers["Authorization"] = "Basic " + base64.b64encode(auth.encode()).decode()
    with urllib.request.urlopen(urllib.request.Request(url, data, headers), timeout=5) as response:
        body = response.read().decode()
        try:
            return json.loads(body)
        except ValueError:
            return body


def poll(name, check, timeout=60):
    deadline = time.monotonic() + timeout
    last = "no data"
    while time.monotonic() < deadline:
        try:
            result = check()
            if result:
                print("PASS " + name)
                return result
        except (OSError, HTTPException, ValueError, KeyError, AssertionError) as error:
            last = str(error)
        time.sleep(1)
    raise AssertionError(name + ": timed out: " + last)


def free_port():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def fixture_payload(identifier, trace_id, marker, route="/api/health/"):
    def attr(key, value):
        return {"key": key, "value": {"intValue" if isinstance(value, int) else "stringValue": value}}
    start = time.time_ns()
    span = {"traceId": trace_id, "spanId": uuid.uuid4().hex[:16], "name": marker,
            "kind": 2, "startTimeUnixNano": str(start), "endTimeUnixNano": str(start + 12000000),
            "traceState": "vendor=" + marker,
            "attributes": [attr("http.route", route), attr("http.request.method", "GET"),
                           attr("http.response.status_code", 200), attr("request_id", identifier),
                           attr("url.full", "https://invalid/?token=" + marker)],
            "status": {"code": 2, "message": marker},
            "events": [{"name": marker, "timeUnixNano": str(start), "attributes": [attr("exception.message", marker)]}],
            "links": [{"traceId": uuid.uuid4().hex, "spanId": uuid.uuid4().hex[:16],
                       "traceState": "vendor=" + marker, "attributes": [attr("secret", marker)]}]}
    linked = dict(span, spanId=uuid.uuid4().hex[:16])
    span.pop("links")
    child = dict(span, spanId=uuid.uuid4().hex[:16], parentSpanId=span["spanId"], kind=3)
    safe = {"event": "http_request", "level": "INFO", "request_id": identifier,
            "trace_id": trace_id, "span_id": span["spanId"], "method": "GET",
            "route": route, "status_code": 200, "duration_ms": 12,
            "arbitrary": {"token": marker}, "exception": {"message": marker}}
    return {"logs": [json.dumps(safe), marker, '{"bad":', json.dumps({"event": marker, "level": "ERROR"})],
            "trace": {"resourceSpans": [{"resource": {"attributes": [attr("service.name", "django"), attr("secret", marker)]},
                                         "scopeSpans": [{"scope": {"name": marker, "version": marker,
                                                                    "attributes": [attr("secret", marker)]}, "spans": [span, child, linked]}]}]}}


def route_fixtures(urls, logs):
    for route in (*KNOWN_ROUTES, "/api/private/" + uuid.uuid4().hex):
        identifier, trace_id = str(uuid.uuid4()), uuid.uuid4().hex
        http(urls["fixture"], fixture_payload(identifier, trace_id, "PRIVATE_" + uuid.uuid4().hex, route))
        records = poll("route log " + route, lambda: logs(identifier))
        values = [json.loads(line) for record in records for _, line in record["values"]]
        assert all(value.get("route") == (route if route in KNOWN_ROUTES else None) for value in values), values
        stored = poll("route trace " + route, lambda: http(urls["tempo"] + "/api/traces/" + trace_id))
        spans = [span for batch in stored.get("batches", stored.get("resourceSpans", []))
                 for scope in batch.get("scopeSpans", batch.get("instrumentationLibrarySpans", []))
                 for span in scope["spans"]]
        expected = route if route in KNOWN_ROUTES else "unmatched"
        assert len(spans) == 2, spans
        for span in spans:
            attributes = {a["key"]: a["value"] for a in span["attributes"]}
            assert span["name"] == expected, span
            assert attributes["http.route"] == {"stringValue": expected}, span
    print("PASS finite route allowlist: known templates retained in logs/traces; private route stripped")


def readiness(urls):
    for name, path in [("grafana", "/api/health"), ("loki", "/ready"), ("tempo", "/ready"),
                       ("prometheus", "/-/ready"), ("alloy", "/-/ready")]:
        poll(name + " ready", lambda n=name, p=path: http(urls[n] + p))
    assert http(urls["grafana"] + "/api/health")["database"] == "ok"


def run_ci(keep):
    project = "shop-obs-smoke-" + uuid.uuid4().hex[:10]
    # Explicit env file bypasses automatic root .env loading. Never export caller credentials.
    env = {key: value for key, value in os.environ.items()
           if key in {"PATH", "HOME", "DOCKER_HOST", "DOCKER_CONTEXT", "DOCKER_CONFIG", "XDG_RUNTIME_DIR", "TMPDIR"}}
    ports = {name: free_port() for name in ["grafana", "loki", "tempo", "prometheus", "alloy", "otlp", "fixture"]}
    env.update({"OBS_" + name.upper() + "_PORT": str(port) for name, port in ports.items()})
    env["OBS_LOG_SCOPE"] = project
    urls = {name: "http://127.0.0.1:" + str(port) for name, port in ports.items()}
    scratch = Path(os.environ.get("TMPDIR", str(Path.home() / ".hermes/cache/scratch")))
    scratch.mkdir(parents=True, exist_ok=True)
    context = (contextlib.nullcontext(tempfile.mkdtemp(prefix=project, dir=scratch)) if keep
               else tempfile.TemporaryDirectory(prefix=project, dir=scratch))
    with context as folder:
        folder = Path(folder)
        password = uuid.uuid4().hex
        (folder / "password").write_text(password)
        (folder / "password").chmod(0o644)  # Grafana UID reads dedicated random smoke-only file.
        env["OBS_GRAFANA_PASSWORD_FILE"] = str(folder / "password")
        empty = folder / "empty.env"
        empty.write_text("")
        compose = ["docker", "compose", "--env-file", str(empty), "--project-name", project,
                   "-f", str(ROOT / "infra/compose.observability.yml"),
                   "-f", str(ROOT / "infra/compose.observability.test.yml")]

        def docker(*args):
            result = subprocess.run(compose + list(args), env=env, cwd=ROOT, text=True,
                                    stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=600)
            if result.returncode:
                raise AssertionError("Compose " + " ".join(args) + ": " + result.stdout)
            return result.stdout

        def prom(query):
            return http(urls["prometheus"] + "/api/v1/query?" + urllib.parse.urlencode({"query": query}))["data"]["result"]

        def logs(identifier=None):
            query = '{service="server"}'
            if identifier:
                query += ' | json | request_id="' + identifier + '"'
            return http(urls["loki"] + "/loki/api/v1/query_range?" + urllib.parse.urlencode(
                {"query": query, "start": str(time.time_ns() - 600_000_000_000), "limit": 1000}))["data"]["result"]

        try:
            docker("config", "--quiet")
            print(docker("up", "-d"))
            readiness(urls)
            print(docker("run", "--rm", "--no-deps", "loki", "-config.file=/etc/loki/local.yml", "-verify-config=true"))
            print(docker("run", "--rm", "--no-deps", "--entrypoint", "promtool", "prometheus", "check", "config", "/etc/prometheus/prometheus.yml"))
            print(docker("run", "--rm", "--no-deps", "alloy", "validate", "/etc/alloy/config.alloy"))
            print(docker("run", "--rm", "--no-deps", "--entrypoint", "promtool", "prometheus", "test", "rules", "/etc/prometheus/test_alerts.yml"))
            poll("synthetic fixture ready", lambda: http(urls["fixture"], {}) == {})
            route_fixtures(urls, logs)
            identifier, trace_id, marker = str(uuid.uuid4()), uuid.uuid4().hex, "PRIVATE_" + uuid.uuid4().hex
            payload = fixture_payload(identifier, trace_id, marker)
            http(urls["fixture"], payload)
            records = poll("Docker collected approved JSON", lambda: logs(identifier))
            assert marker not in json.dumps(records), "nested log secret persisted"
            assert all(set(row["stream"]) == {"service", "environment"} for row in logs())
            stored = poll("Tempo trace parent-child", lambda: http(urls["tempo"] + "/api/traces/" + trace_id))
            assert marker not in json.dumps(stored), "trace secret persisted"
            spans = [s for batch in stored.get("batches", stored.get("resourceSpans", []))
                     for scope in batch.get("scopeSpans", batch.get("instrumentationLibrarySpans", [])) for s in scope["spans"]]
            assert len(spans) == 2, stored
            assert any(s.get("parentSpanId") for s in spans)
            assert marker not in json.dumps(logs()), "unapproved log line persisted"
            poll("four scrape targets up", lambda: len([r for r in prom("up") if r["value"][1] == "1"]) == 4)
            counters = poll("spanmetrics counters", lambda: prom('{__name__=~".*calls.*",service_name="django"}'))
            hist = poll("spanmetrics histogram", lambda: prom('{__name__=~".*duration.*bucket",service_name="django"}'))
            print("METRICS " + json.dumps({"counter": counters[0]["metric"], "histogram": hist[0]["metric"]}))
            assert marker not in json.dumps(prom('{service_name="django"}'))
            denied = [(method, path) for method in ["POST", "PUT", "PATCH", "DELETE"] for path in ["/containers/create", "/containers/invalid"]]
            denied += [("GET", "/containers/invalid/archive"), ("GET", "/containers/invalid/export"), ("GET", "/containers/invalid/json"), ("GET", "/images/json")]
            statuses = http(urls["fixture"], {"proxy": denied})
            assert set(statuses.values()) == {403}, statuses
            print("PASS proxy denied writes, archive, export and image listing; read-only inspect required by Alloy")
            auth = "observer:" + password
            for uid in ["shop-overview", "shop-logs"]:
                dash = http(urls["grafana"] + "/api/dashboards/uid/" + uid, auth=auth)
                assert dash["dashboard"]["uid"] == uid
            sources = http(urls["grafana"] + "/api/datasources", auth=auth)
            assert {s["uid"] for s in sources} == {"loki", "tempo", "prometheus"}
            by_uid = {source["uid"]: source for source in sources}
            assert by_uid["loki"]["jsonData"]["derivedFields"][0]["url"] == "${__value.raw}"
            assert by_uid["tempo"]["jsonData"]["tracesToLogsV2"]["query"] == '{service=~"server|client"} | json | trace_id = "${__trace.traceId}"'
            print("PASS Grafana provisioned correlation templates")
            overview = http(urls["grafana"] + "/api/dashboards/uid/shop-overview", auth=auth)
            for panel in overview["dashboard"]["panels"]:
                if panel["datasource"]["uid"] == "prometheus":
                    poll("dashboard " + panel["title"], lambda p=panel: prom(p["targets"][0]["expr"]))
            print("PASS Grafana dashboards, panel queries and datasources provisioned")
            before = sum(float(r["value"][1]) for r in counters)
            http(urls["fixture"], payload)
            poll("request counter increased", lambda: sum(float(r["value"][1]) for r in prom('{__name__=~".*calls.*",service_name="django"}')) > before)
            docker("restart", "loki", "tempo", "prometheus", "grafana")
            readiness(urls)
            poll("log persistence", lambda: logs(identifier))
            poll("trace persistence", lambda: http(urls["tempo"] + "/api/traces/" + trace_id))
            poll("metrics persistence", lambda: prom('{__name__=~".*calls.*",service_name="django"}'))
            for uid in ["shop-overview", "shop-logs"]:
                assert http(urls["grafana"] + "/api/dashboards/uid/" + uid, auth=auth)
            print("PASS privacy and restart persistence")
            ids = docker("ps", "-q").split()
            print(subprocess.check_output(["docker", "stats", "--no-stream", "--format", "{{.Name}} {{.MemUsage}}", *ids], text=True))
            print("PASS smoke project=" + project + " trace=" + trace_id + " request=" + identifier)
            if keep:
                print("Retained containers; dedicated smoke secret directory=" + str(folder))
        finally:
            if not keep:
                print(docker("down", "--volumes", "--remove-orphans"))
            else:
                print("Retained project=" + project + " ports=" + json.dumps(ports))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ci", action="store_true")
    parser.add_argument("--keep", action="store_true")
    parser.add_argument("--static", action="store_true")
    args = parser.parse_args()
    structural()
    if args.ci:
        run_ci(args.keep)
    elif not args.static:
        readiness({n: "http://127.0.0.1:" + str(p) for n, p in
                   [("grafana", 3001), ("loki", 3101), ("tempo", 3200), ("prometheus", 9090), ("alloy", 12345)]})


if __name__ == "__main__":
    main()
