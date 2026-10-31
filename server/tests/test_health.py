from unittest.mock import patch

import pytest
from rest_framework.test import APIClient


@pytest.fixture
def client():
    return APIClient()


def test_health_check_healthy(client):
    with (
        patch("apps.core.health.check_database", return_value=(True, "ok")),
        patch("apps.core.health.check_redis", return_value=(True, "ok")),
    ):
        response = client.get("/api/health/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["services"]["database"]["status"] == "ok"
        assert data["services"]["redis"]["status"] == "ok"


def test_health_check_degraded_when_db_down(client):
    with (
        patch("apps.core.health.check_database", return_value=(False, "connection refused")),
        patch("apps.core.health.check_redis", return_value=(True, "ok")),
    ):
        response = client.get("/api/health/")
        assert response.status_code == 503
        data = response.json()
        assert data["status"] == "unhealthy"
        assert data["services"]["database"]["status"] == "error"


def test_health_db_endpoint(client):
    with patch("apps.core.health.check_database", return_value=(True, "ok")):
        response = client.get("/api/health/db/")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"


@pytest.mark.parametrize(
    "endpoint,target,event",
    [
        ("/api/health/db/", "apps.core.health.connection.cursor", "database_unavailable"),
        ("/api/health/redis/", "apps.core.health.cache.set", "redis_unavailable"),
    ],
)
def test_health_failure_private(client, caplog, endpoint, target, event):
    from apps.core.logging import JsonFormatter

    with patch(target, side_effect=RuntimeError("password=private-value")):
        response = client.get(endpoint)
    assert response.status_code == 503
    assert response.json()["detail"] == "unavailable"
    assert "private-value" not in response.content.decode()
    records = [r for r in caplog.records if getattr(r, "event", None) == event]
    assert len(records) == 1
    assert "private-value" not in JsonFormatter().format(records[0])


def test_redis_mismatch_logged(caplog):
    from apps.core.health import check_redis

    with (
        patch("apps.core.health.cache.set"),
        patch("apps.core.health.cache.get", return_value="wrong"),
    ):
        assert check_redis() == (False, "cache read mismatch")
    assert any(getattr(r, "event", None) == "cache_mismatch" for r in caplog.records)


def test_health_redis_endpoint(client):
    with patch("apps.core.health.check_redis", return_value=(True, "ok")):
        response = client.get("/api/health/redis/")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"
