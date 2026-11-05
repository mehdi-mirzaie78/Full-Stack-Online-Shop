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


def test_real_storage_round_trip(s3_bucket):
    client, bucket = s3_bucket
    client.put_object(Bucket=bucket, Key="fixture.txt", Body=b"repeatable-test-payload")
    response = client.get_object(Bucket=bucket, Key="fixture.txt")
    assert response["Body"].read() == b"repeatable-test-payload"
    client.delete_object(Bucket=bucket, Key="fixture.txt")
    assert client.list_objects_v2(Bucket=bucket)["KeyCount"] == 0
