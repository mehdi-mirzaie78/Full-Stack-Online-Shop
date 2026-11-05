import os
import socket
import subprocess
import sys

import pytest
from django.conf import settings
from django.core import mail


@pytest.mark.parametrize(
    "address",
    [
        ("203.0.113.1", 443),
        ("127.0.0.1", 5432),
        ("127.0.0.1", 6379),
        ("127.0.0.1", 9000),
        ("127.0.0.1", 55432),
    ],
)
def test_unit_tests_cannot_connect_to_external_or_service_sockets(address):
    with socket.socket() as connection, pytest.raises(RuntimeError, match="network access denied"):
        connection.connect(address)


def test_external_name_resolution_is_blocked():
    with pytest.raises(RuntimeError, match="network access denied"):
        socket.getaddrinfo("sms-provider.invalid", 443)


def test_email_stays_in_memory():
    assert mail.send_mail("Test", "Body", "sender@example.test", ["customer@example.test"]) == 1
    assert mail.outbox[-1].body == "Body"


def test_inherited_service_urls_cannot_override_test_settings():
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            """
import django
from django.conf import settings
from unittest.mock import patch
with patch('environ.Env.read_env', side_effect=AssertionError('Environment file was read')):
    django.setup()
assert settings.DATABASES['default']['PORT'] == '55432'
assert settings.CACHES['default']['LOCATION'] == 'redis://127.0.0.1:56379/15'
assert settings.CELERY_BROKER_URL == 'memory://'
assert settings.EMAIL_BACKEND == 'django.core.mail.backends.locmem.EmailBackend'
assert settings.OTEL_ENABLED is False
""",
        ],
        env=os.environ
        | {
            "DJANGO_SETTINGS_MODULE": "config.test_settings",
            "DATABASE_URL": "postgres://unused:unused@production.invalid:5432/production",
            "REDIS_URL": "redis://production.invalid:6379/0",
            "CELERY_BROKER_URL": "amqp://production.invalid",
            "OTEL_ENABLED": "true",
        },
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert result.returncode == 0, result.stderr


def test_development_settings_are_rejected():
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            """
from unittest.mock import patch
import pytest
with patch("environ.Env.read_env"):
    raise SystemExit(pytest.main(["--collect-only", "tests/test_health.py"]))
""",
        ],
        env=os.environ | {"DJANGO_SETTINGS_MODULE": "config.settings"},
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert result.returncode != 0
    assert "development settings are unsafe" in result.stderr


def test_synchronous_tasks_do_not_use_a_real_broker():
    assert settings.CELERY_TASK_ALWAYS_EAGER
    assert settings.CELERY_BROKER_URL == "memory://"
    assert settings.CELERY_RESULT_BACKEND == "cache+memory://"
