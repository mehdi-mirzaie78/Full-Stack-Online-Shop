import json
import logging
import sys

from apps.core.logging import JsonFormatter


def test_framework_message_and_extras_are_not_serialized():
    record = logging.LogRecord(
        "provider", logging.ERROR, __file__, 10, "password=%s", ("private-value",), None
    )
    record.secret = "private-value"
    data = json.loads(JsonFormatter().format(record))
    assert data["event"] == "framework_log"
    assert data["service"] == "django"
    assert data["level"] == "ERROR"
    assert data["timestamp"].endswith("+00:00")
    assert data["request_id"] is None
    assert "private-value" not in json.dumps(data)


def test_invalid_identifiers_are_replaced():
    from uuid import UUID

    from apps.core.logging import correlation_id

    for value in [None, "", "z" * 36, "x" * 10000, "header\ninjection", object()]:
        assert str(UUID(correlation_id(value)))


def test_context_isolated_between_async_tasks():
    import asyncio

    from apps.core.logging import request_id

    async def run(identifier):
        token = request_id.set(identifier)
        try:
            await asyncio.sleep(0)
            return request_id.get()
        finally:
            request_id.reset(token)

    async def gather():
        return await asyncio.gather(run("first"), run("second"))

    assert asyncio.run(gather()) == ["first", "second"]
    assert request_id.get() is None


def test_exception_has_bounded_frames_not_value_source_or_locals():
    try:
        raise ValueError("secret-provider-token")
    except ValueError:
        record = logging.LogRecord("app", logging.ERROR, __file__, 1, "raw", (), sys.exc_info())
    data = json.loads(JsonFormatter().format(record))
    assert data["exception"]["type"] == "ValueError"
    assert 0 < len(data["exception"]["frames"]) <= 15
    assert set(data["exception"]["frames"][0]) == {"file", "line", "function"}
    assert "secret-provider-token" not in json.dumps(data)
