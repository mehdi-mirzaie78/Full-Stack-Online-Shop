import json
import logging
from uuid import UUID

import pytest
from django.http import HttpResponse
from django.test import Client, RequestFactory, override_settings
from django.urls import path

from apps.core.logging import JsonFormatter, request_id
from apps.core.middleware import RequestLoggingMiddleware


@pytest.fixture
def json_lines():
    lines = []

    class Handler(logging.Handler):
        def emit(self, record):
            lines.append(json.loads(JsonFormatter().format(record)))

    handler = Handler()
    root = logging.getLogger()
    root.addHandler(handler)
    try:
        yield lines
    finally:
        root.removeHandler(handler)


def crash(request):
    raise RuntimeError("private-exception-token")


urlpatterns = [path("crash/", crash), path("item/<str:key>/", lambda r, key: HttpResponse())]


@pytest.mark.parametrize(
    "supplied", [None, "unsafe\nheader", "123", "b4f63dc7-4b04-4b23-a182-555cb8277fd1"]
)
def test_correlation_and_cleanup(supplied, caplog, json_lines):
    request = RequestFactory().get("/private-id/?token=secret")
    if supplied:
        request.META["HTTP_X_REQUEST_ID"] = supplied
    with caplog.at_level(logging.INFO):
        response = RequestLoggingMiddleware(lambda _: HttpResponse())(request)
    identifier = response["X-Request-ID"]
    assert str(UUID(identifier)) == identifier
    if supplied and len(supplied) == 36:
        assert identifier == supplied
    records = [r for r in caplog.records if getattr(r, "event", None) == "http_request"]
    assert len(records) == 1
    data = next(line for line in json_lines if line["event"] == "http_request")
    assert data["request_id"] == identifier
    assert data["status_code"] == 200
    assert data["duration_ms"] >= 0
    assert "private-id" not in json.dumps(data)
    assert "secret" not in json.dumps(data)
    assert request_id.get() is None


def test_exception_resets_context(caplog):
    with pytest.raises(RuntimeError):
        RequestLoggingMiddleware(crash)(RequestFactory().get("/"))
    assert request_id.get() is None
    record = next(r for r in caplog.records if getattr(r, "event", None) == "http_request")
    assert record.status_code == 500


@override_settings(ROOT_URLCONF=__name__)
def test_framework_failure_safe_and_correlated(caplog, json_lines):
    with caplog.at_level(logging.INFO):
        response = Client(raise_request_exception=False).get("/crash/")
    assert response.status_code == 500
    assert UUID(response["X-Request-ID"])
    records = [r for r in caplog.records if r.name == "django.request" and r.exc_info]
    assert records
    data = next(line for line in json_lines if line["logger"] == "django.request")
    assert data["exception"]["type"] == "RuntimeError"
    assert data["request_id"] == response["X-Request-ID"]
    assert "private-exception-token" not in json.dumps(data)
    assert request_id.get() is None


@override_settings(ROOT_URLCONF=__name__)
def test_route_template_not_path(caplog):
    with caplog.at_level(logging.INFO):
        response = Client().get("/item/private-id/?token=secret")
    record = next(r for r in caplog.records if getattr(r, "event", None) == "http_request")
    assert record.route == "item/<str:key>/"
    assert response.status_code == 200


def test_unmatched_response_has_id():
    response = Client().get("/not-found/")
    assert response.status_code == 404
    assert UUID(response["X-Request-ID"])


def test_configured_logger_has_one_handler_owner():
    from django.conf import settings

    assert settings.LOGGING["root"]["handlers"] == ["console"]
    assert logging.getLogger("django.request").propagate
    assert not logging.getLogger("django.request").handlers
