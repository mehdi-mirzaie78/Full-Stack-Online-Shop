import json
import logging
from unittest.mock import patch

import pytest
from django.http import HttpResponse
from django.test import RequestFactory, override_settings
from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from opentelemetry.trace import SpanKind, StatusCode

from apps.core import telemetry
from apps.core.logging import JsonFormatter, request_id
from apps.core.middleware import RequestLoggingMiddleware


@override_settings(OTEL_ENABLED=False)
def test_disabled_has_no_exporter():
    with patch.object(telemetry, "OTLPSpanExporter") as exporter:
        assert telemetry.get_tracer() is None
    exporter.assert_not_called()


@pytest.fixture
def spans():
    exporter = InMemorySpanExporter()
    provider = TracerProvider(resource=Resource({"service.name": "django"}))
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    with patch.object(telemetry, "get_tracer", return_value=provider.get_tracer("test")):
        yield exporter
    provider.shutdown()


def test_safe_span_inherits_parent_and_logs_ids(spans):
    logged = []

    def view(request):
        record = logging.LogRecord("app", logging.INFO, __file__, 1, "private", (), None)
        logged.append(json.loads(JsonFormatter().format(record)))
        return HttpResponse()

    request = RequestFactory().get(
        "/private-id/?token=private",
        HTTP_TRACEPARENT="00-12345678901234567890123456789012-1234567890123456-01",
        HTTP_TRACESTATE="secret=private",
        HTTP_BAGGAGE="token=private",
    )
    RequestLoggingMiddleware(view)(request)
    (span,) = spans.get_finished_spans()
    assert span.context.trace_id == int("12345678901234567890123456789012", 16)
    assert span.parent.span_id == int("1234567890123456", 16)
    assert not span.context.trace_state
    assert span.kind == SpanKind.SERVER
    assert span.attributes["http.route"] == "unmatched"
    assert span.attributes["http.response.status_code"] == 200
    assert logged[0]["trace_id"] == f"{span.context.trace_id:032x}"
    assert logged[0]["span_id"] == f"{span.context.span_id:016x}"
    assert "private" not in span.to_json()
    assert not span.events
    assert not span.links
    assert request_id.get() is None
    assert not trace.get_current_span().get_span_context().is_valid


def test_failure_span_has_status_without_exception_text(spans):
    def broken(request):
        raise RuntimeError("private-token")

    with pytest.raises(RuntimeError):
        RequestLoggingMiddleware(broken)(RequestFactory().get("/private-token/"))
    (span,) = spans.get_finished_spans()
    assert span.status.status_code == StatusCode.ERROR
    assert not span.status.description
    assert "private-token" not in span.to_json()
    assert not span.events
    assert request_id.get() is None


def test_framework_route_template_and_completion_log_share_span(spans, caplog):
    from django.test import Client

    lines = []

    class Handler(logging.Handler):
        def emit(self, record):
            if getattr(record, "event", None) == "http_request":
                lines.append(json.loads(JsonFormatter().format(record)))

    handler = Handler()
    logger = logging.getLogger("apps.core.http")
    logger.addHandler(handler)
    try:
        with (
            override_settings(ROOT_URLCONF="tests.test_request_logging"),
            caplog.at_level(logging.INFO),
        ):
            response = Client().get("/item/private-marker/?token=private-marker")
    finally:
        logger.removeHandler(handler)
    (span,) = spans.get_finished_spans()
    assert response.status_code == 200
    assert span.name == "item/<str:key>/"
    assert span.attributes["http.route"] == "item/<str:key>/"
    assert lines[0]["trace_id"] == f"{span.context.trace_id:032x}"
    assert lines[0]["request_id"] == response["X-Request-ID"]
    assert "private-marker" not in span.to_json()


def test_sequential_requests_do_not_share_trace(spans):
    middleware = RequestLoggingMiddleware(lambda _: HttpResponse())
    middleware(RequestFactory().get("/"))
    middleware(RequestFactory().get("/"))
    first, second = spans.get_finished_spans()
    assert first.context.trace_id != second.context.trace_id


def test_explicit_exporter_delivers_safe_protobuf_and_survives_outage(monkeypatch):
    import threading
    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

    from opentelemetry.proto.collector.trace.v1.trace_service_pb2 import ExportTraceServiceRequest

    payloads = []

    class Receiver(BaseHTTPRequestHandler):
        def do_POST(self):
            assert self.path == "/v1/traces"
            payloads.append(self.rfile.read(int(self.headers["Content-Length"])))
            self.send_response(200)
            self.end_headers()

        def log_message(self, *args):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Receiver)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    monkeypatch.setattr(telemetry, "_provider", None)
    endpoint = f"http://127.0.0.1:{server.server_port}"
    try:
        with override_settings(OTEL_ENABLED=True, OTEL_EXPORTER_OTLP_ENDPOINT=endpoint):
            middleware = RequestLoggingMiddleware(lambda _: HttpResponse())
            response = middleware(RequestFactory().get("/private-marker/?token=private-marker"))
            assert response.status_code == 200
            provider = telemetry._provider
            assert provider.force_flush(timeout_millis=5000)
            assert len(payloads) == 1
            message = ExportTraceServiceRequest.FromString(payloads[0])
            assert "private-marker" not in str(message)
            assert len(message.resource_spans) == 1
            assert telemetry.get_tracer() is not None
            assert telemetry._provider is provider
            server.shutdown()
            server.server_close()
            response = middleware(RequestFactory().get("/"))
            assert response.status_code == 200
    finally:
        if telemetry._provider:
            telemetry._provider.shutdown()
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


@override_settings(OTEL_ENABLED=True, OTEL_EXPORTER_OTLP_ENDPOINT="")
def test_enabled_without_explicit_endpoint_does_not_export():
    with patch.object(telemetry, "OTLPSpanExporter") as exporter:
        assert telemetry.get_tracer() is None
    exporter.assert_not_called()
