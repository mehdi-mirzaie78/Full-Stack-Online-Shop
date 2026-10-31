import json
import logging
import traceback
from contextvars import ContextVar
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID, uuid4

from apps.core.telemetry import trace_ids

request_id: ContextVar[str | None] = ContextVar("request_id", default=None)
EVENTS = {"http_request", "database_unavailable", "redis_unavailable", "cache_mismatch"}


def valid_request_id(value: object) -> str | None:
    if not isinstance(value, str) or len(value) != 36:
        return None
    try:
        identifier = str(UUID(value))
    except ValueError:
        return None
    return identifier if identifier == value.lower() else None


def correlation_id(value: object) -> str:
    return valid_request_id(value) or str(uuid4())


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        from celery import current_task

        task_request = getattr(current_task, "request", None)
        headers = getattr(task_request, "headers", None) or {}
        event = getattr(record, "event", None)
        data = {
            "timestamp": datetime.fromtimestamp(record.created, UTC).isoformat(),
            "level": record.levelname,
            "service": "celery" if getattr(task_request, "id", None) else "django",
            "logger": record.name,
            "event": event if isinstance(event, str) and event in EVENTS else "framework_log",
            "request_id": valid_request_id(request_id.get())
            or valid_request_id(headers.get("request_id")),
            "task_id": getattr(task_request, "id", None),
        }
        data.update(trace_ids())
        if event == "http_request":
            for key in ("method", "route", "status_code", "duration_ms"):
                data[key] = getattr(record, key, None)
        if record.exc_info and record.exc_info[0]:
            frames = traceback.extract_tb(record.exc_info[2])[-15:]
            data["exception"] = {
                "type": record.exc_info[0].__name__,
                "frames": [
                    {"file": Path(f.filename).name, "line": f.lineno, "function": f.name}
                    for f in frames
                ],
            }
        return json.dumps(data, ensure_ascii=True)
