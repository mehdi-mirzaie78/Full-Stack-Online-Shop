import atexit
from contextlib import contextmanager
from threading import Lock

from django.conf import settings
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.trace.sampling import ALWAYS_ON
from opentelemetry.trace import SpanKind, StatusCode
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator

_provider: TracerProvider | None = None
_lock = Lock()


def get_tracer():
    global _provider
    endpoint = settings.OTEL_EXPORTER_OTLP_ENDPOINT
    if not settings.OTEL_ENABLED or not endpoint:
        return None
    with _lock:
        if _provider is None:
            # Explicit resource prevents environment/host metadata auto-discovery.
            provider = TracerProvider(
                resource=Resource({"service.name": "django"}),
                sampler=ALWAYS_ON,
                shutdown_on_exit=False,
            )
            exporter = OTLPSpanExporter(endpoint=endpoint.rstrip("/") + "/v1/traces", timeout=2)
            provider.add_span_processor(
                BatchSpanProcessor(
                    exporter,
                    max_queue_size=512,
                    max_export_batch_size=64,
                    schedule_delay_millis=1000,
                    export_timeout_millis=2000,
                )
            )
            _provider = provider
            atexit.register(provider.shutdown)
        return _provider.get_tracer(__name__)


@contextmanager
def request_span(request):
    tracer = get_tracer()
    if tracer is None:
        yield None
        return
    # Only traceparent crosses trust boundary; no baggage or tracestate.
    parent = TraceContextTextMapPropagator().extract(
        {"traceparent": request.headers.get("traceparent", "")}
    )
    with tracer.start_as_current_span(
        "request",
        context=parent,
        kind=SpanKind.SERVER,
        record_exception=False,
        set_status_on_exception=False,
    ) as span:
        yield span


def finish_span(span, method: str, route: str, status: int, identifier: str) -> None:
    if span is None:
        return
    span.update_name(route)
    span.set_attributes(
        {
            "http.request.method": method,
            "http.route": route,
            "http.response.status_code": status,
            "request_id": identifier,
        }
    )
    if status >= 500:
        span.set_status(StatusCode.ERROR)


def trace_ids() -> dict[str, str | None]:
    context = trace.get_current_span().get_span_context()
    return {
        "trace_id": f"{context.trace_id:032x}" if context.is_valid else None,
        "span_id": f"{context.span_id:016x}" if context.is_valid else None,
    }
