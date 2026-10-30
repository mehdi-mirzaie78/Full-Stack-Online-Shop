import os

from celery import Celery, current_task
from celery.signals import before_task_publish, setup_logging
from django.conf import settings
from django.utils.log import configure_logging

from apps.core.logging import request_id, valid_request_id

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = Celery("config")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()


@setup_logging.connect
def configure_worker_logging(**kwargs):
    # Owning setup prevents Celery from replacing task handlers with its raw formatter.
    configure_logging(settings.LOGGING_CONFIG, settings.LOGGING)


@before_task_publish.connect
def attach_request_id(headers=None, **kwargs):
    task_request = getattr(current_task, "request", None)
    task_headers = getattr(task_request, "headers", None) or {}
    identifier = valid_request_id(request_id.get()) or valid_request_id(
        task_headers.get("request_id")
    )
    if headers is not None and identifier:
        headers["request_id"] = identifier
