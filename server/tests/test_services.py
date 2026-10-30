import pytest
from django.db import connection

from apps.core.health import check_database, check_redis

pytestmark = pytest.mark.integration


@pytest.mark.django_db
def test_real_database_health():
    assert connection.vendor == "postgresql"
    assert check_database() == (True, "ok")


def test_real_redis_health():
    assert check_redis() == (True, "ok")
