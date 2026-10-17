from unittest.mock import patch

import pytest
from rest_framework.test import APIClient


@pytest.fixture
def client():
    return APIClient()


def test_health_check_healthy(client):
    with (
        patch("core.health.check_database", return_value=(True, "ok")),
        patch("core.health.check_redis", return_value=(True, "ok")),
    ):
        response = client.get("/api/health/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["services"]["database"]["status"] == "ok"
        assert data["services"]["redis"]["status"] == "ok"


def test_health_check_degraded_when_db_down(client):
    with (
        patch("core.health.check_database", return_value=(False, "connection refused")),
        patch("core.health.check_redis", return_value=(True, "ok")),
    ):
        response = client.get("/api/health/")
        assert response.status_code == 503
        data = response.json()
        assert data["status"] == "unhealthy"
        assert data["services"]["database"]["status"] == "error"


def test_health_db_endpoint(client):
    with patch("core.health.check_database", return_value=(True, "ok")):
        response = client.get("/api/health/db/")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"


def test_health_redis_endpoint(client):
    with patch("core.health.check_redis", return_value=(True, "ok")):
        response = client.get("/api/health/redis/")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"
