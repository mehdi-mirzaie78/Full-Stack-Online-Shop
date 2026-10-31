#!/usr/bin/env python3
"""Exercise real running applications; verify SDK exports in Loki and Tempo."""
import argparse
import base64
import json
import time
import uuid
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


def fetch(url, headers=None):
    try:
        response = urlopen(Request(url, headers=headers or {}), timeout=10)
    except HTTPError as error:
        response = error
    with response:
        return response.status, dict(response.headers), response.read()


def poll(url, predicate, timeout=60):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        status, _, body = fetch(url, {"Accept": "application/json"})
        if status == 200:
            data = json.loads(body)
            if predicate(data):
                return data
        time.sleep(1)
    raise AssertionError(f"Telemetry absent: {url}")


def spans(document):
    for batch in document.get("batches", document.get("resourceSpans", [])):
        service = next((a["value"].get("stringValue") for a in batch["resource"].get("attributes", []) if a["key"] == "service.name"), None)
        for scope in batch.get("scopeSpans", batch.get("instrumentationLibrarySpans", [])):
            for span in scope.get("spans", []):
                yield service, span


def normalized_id(value):
    if len(value) in (16, 32) and all(c in "0123456789abcdef" for c in value):
        return value
    return base64.b64decode(value).hex()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--django", default="http://127.0.0.1:8000")
    parser.add_argument("--next", default="http://127.0.0.1:3000")
    parser.add_argument("--loki", default="http://127.0.0.1:3101")
    parser.add_argument("--tempo", default="http://127.0.0.1:3200")
    args = parser.parse_args()
    marker = "private-sdk-probe-" + uuid.uuid4().hex
    start = time.time_ns()
    results = []
    for service, base, path in (("django", args.django, "/api/health/"), ("next", args.next, "/"), ("django", args.django, "/" + marker), ("next", args.next, "/" + marker)):
        trace_id, parent_id = uuid.uuid4().hex, uuid.uuid4().hex[:16]
        request_id = str(uuid.uuid4())
        status, response_headers, _ = fetch(base + path + "?private=" + marker, {
            "traceparent": f"00-{trace_id}-{parent_id}-01",
            "X-Request-ID": request_id,
            "Authorization": "Bearer " + marker,
            "Cookie": "private=" + marker,
        })
        expected = 404 if marker in path else 200
        assert status == expected or (service == "django" and path == "/api/health/" and status == 503), (service, expected, status)
        trace_url = args.tempo + "/api/traces/" + trace_id
        document = poll(trace_url, lambda data: bool(list(spans(data))))
        exported = [(s, span) for s, span in spans(document) if s == service]
        assert exported, (service, "service missing")
        assert any(normalized_id(span.get("parentSpanId", "")) == parent_id for _, span in exported), "SDK ignored incoming traceparent"
        assert marker not in json.dumps(document), "Private marker reached Tempo"
        for _, span in exported:
            allowed_names = ("/", "unmatched") if service == "next" else ("api/health/", "/api/health/", "unmatched")
            assert span["name"] in allowed_names
            assert {a["key"] for a in span.get("attributes", [])} <= {"http.request.method", "http.route", "http.response.status_code", "request_id"}
        result = {"service": service, "status": status, "trace_id": trace_id, "parent_span_id": parent_id, "tempo_query": trace_url, "span_count": len(exported)}
        if service == "django":
            query = '{service="server"} | json | trace_id="' + trace_id + '" | event="http_request"'
            log_url = args.loki + "/loki/api/v1/query_range?" + urlencode({"query": query, "start": start, "end": time.time_ns() + 60_000_000_000, "limit": 100})
            logs = poll(log_url, lambda data: bool(data.get("data", {}).get("result")))
            assert marker not in json.dumps(logs), "Private marker reached Loki"
            entries = [json.loads(value[1]) for stream in logs["data"]["result"] for value in stream["values"]]
            assert any(entry["request_id"] == response_headers.get("X-Request-ID") and any(normalized_id(span["spanId"]) == entry["span_id"] for _, span in exported) for entry in entries), "Log and stored SDK span not correlated"
            result.update({"request_id": response_headers.get("X-Request-ID"), "loki_query": query})
        results.append(result)
    print(json.dumps({"checks": results, "private_marker_absent": True}, indent=2))


if __name__ == "__main__":
    main()
