import logging
from time import perf_counter

from django.http import HttpRequest, HttpResponse

from apps.core.logging import correlation_id, request_id
from apps.core.telemetry import finish_span, request_span

logger = logging.getLogger("apps.core.http")


class RequestLoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        identifier = correlation_id(request.headers.get("X-Request-ID"))
        token = request_id.set(identifier)
        try:
            with request_span(request) as span:
                return self.respond(request, identifier, span)
        finally:
            request_id.reset(token)

    def respond(self, request: HttpRequest, identifier: str, span) -> HttpResponse:
        started = perf_counter()
        status = 500
        try:
            response = self.get_response(request)
            status = response.status_code
            response["X-Request-ID"] = identifier
            return response
        finally:
            match = getattr(request, "resolver_match", None)
            route = getattr(match, "route", None) or "unmatched"
            method = (
                request.method
                if request.method
                in {"GET", "HEAD", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "TRACE", "CONNECT"}
                else "OTHER"
            )
            finish_span(span, method, route, status, identifier)
            logger.log(
                logging.ERROR if status >= 500 else logging.INFO,
                "http_request",
                extra={
                    "event": "http_request",
                    "method": method,
                    "route": route,
                    "status_code": status,
                    "duration_ms": round((perf_counter() - started) * 1000, 2),
                },
            )
