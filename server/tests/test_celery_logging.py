import json
import logging
import subprocess
import sys
from contextlib import contextmanager
from textwrap import dedent

from celery._state import _task_stack

from apps.core.logging import JsonFormatter, request_id
from config.celery import app, attach_request_id

IDENTIFIER = "b4f63dc7-4b04-4b23-a182-555cb8277fd1"


@contextmanager
def task_context(identifier=IDENTIFIER):
    def probe():
        pass

    task = app.task(name="tests.logging_probe")(probe)
    task.push_request(id="test-task", headers={"request_id": identifier})
    _task_stack.push(task)
    try:
        yield
    finally:
        _task_stack.pop()
        task.pop_request()


def test_worker_logging_setup_preserves_safe_json_and_task_correlation():
    # Celery's process-global setup flag and logger mutations must not affect other tests.
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            dedent(
                f"""
                import django
                import logging
                from celery._state import _task_stack
                from config.celery import app

                django.setup()
                app.log.setup_logging_subsystem(loglevel="INFO", colorize=False)
                @app.task(name="tests.worker_logging_probe")
                def task():
                    pass
                task.push_request(id="test-task", headers={{"request_id": "{IDENTIFIER}"}})
                _task_stack.push(task)
                try:
                    try:
                        raise ValueError("private-exception-value")
                    except ValueError:
                        logging.getLogger("celery.task").exception(
                            "kwargs=%s", {{"token": "private-task-value"}}
                        )
                finally:
                    _task_stack.pop()
                    task.pop_request()
                logging.getLogger("celery.task").info("private-after-task-value")
                """
            ),
        ],
        capture_output=True,
        text=True,
        check=True,
        timeout=30,
    )
    output = result.stdout + result.stderr
    assert "private-" not in output, output
    task_record, outside_record = [json.loads(line) for line in output.splitlines()]
    assert task_record["service"] == "celery"
    assert task_record["logger"] == "celery.task"
    assert task_record["task_id"] == "test-task"
    assert task_record["request_id"] == IDENTIFIER
    assert task_record["exception"]["type"] == "ValueError"
    assert task_record["exception"]["frames"]
    assert outside_record["task_id"] is None
    assert outside_record["request_id"] is None


def test_publish_carries_request_and_preserves_headers():
    headers = {"existing": "value"}
    token = request_id.set(IDENTIFIER)
    try:
        attach_request_id(headers=headers)
        attach_request_id(headers=None)
    finally:
        request_id.reset(token)
    assert headers == {"existing": "value", "request_id": IDENTIFIER}


def test_publish_outside_request_does_not_invent_id():
    headers = {}
    attach_request_id(headers=headers)
    assert headers == {}


def test_task_formatter_uses_headers_without_payload_and_resets():
    record = logging.LogRecord(
        "celery.task", logging.ERROR, __file__, 1, "kwargs=%s", ({"token": "private"},), None
    )
    with task_context():
        data = json.loads(JsonFormatter().format(record))
    assert data["service"] == "celery"
    assert data["task_id"] == "test-task"
    assert data["request_id"] == IDENTIFIER
    assert "private" not in json.dumps(data)
    data = json.loads(JsonFormatter().format(record))
    assert data["task_id"] is None
    assert data["request_id"] is None


def test_invalid_worker_header_is_dropped():
    with task_context("token=private"):
        record = logging.LogRecord("celery.task", logging.INFO, __file__, 1, "", (), None)
        assert json.loads(JsonFormatter().format(record))["request_id"] is None


def test_nested_task_publish_preserves_parent_correlation():
    headers = {}
    with task_context():
        attach_request_id(headers=headers)
    assert headers["request_id"] == IDENTIFIER
