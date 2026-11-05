"""Fail closed on development settings and external Python socket connections."""

import socket
import uuid

import boto3
import pytest
from botocore.config import Config
from django.conf import settings


def pytest_configure():
    if (
        not getattr(settings, "TESTING", False)
        or settings.SETTINGS_MODULE != "config.test_settings"
    ):
        raise pytest.UsageError(
            "Tests require config.test_settings; development settings are unsafe."
        )


@pytest.fixture(autouse=True)
def allowed_network_ports(
    request: pytest.FixtureRequest,
    monkeypatch: pytest.MonkeyPatch,
) -> set[int]:
    ports = {55432, 56379, 59000} if request.node.get_closest_marker("integration") else set()
    connect = socket.socket.connect
    connect_ex = socket.socket.connect_ex
    getaddrinfo = socket.getaddrinfo

    def check(host, port):
        if host not in ("127.0.0.1", "localhost", "::1") or int(port) not in ports:
            raise RuntimeError(
                "Test network access denied; use an isolated service or fake provider."
            )

    def guarded_connect(sock, address):
        if sock.family in (socket.AF_INET, socket.AF_INET6):
            check(*address[:2])
        return connect(sock, address)

    def guarded_connect_ex(sock, address):
        if sock.family in (socket.AF_INET, socket.AF_INET6):
            check(*address[:2])
        return connect_ex(sock, address)

    def guarded_getaddrinfo(host, port, *args, **kwargs):
        check(host, port)
        return getaddrinfo(host, port, *args, **kwargs)

    monkeypatch.setattr(socket.socket, "connect", guarded_connect)
    monkeypatch.setattr(socket.socket, "connect_ex", guarded_connect_ex)
    monkeypatch.setattr(socket, "getaddrinfo", guarded_getaddrinfo)
    return ports


@pytest.fixture
def s3_bucket():
    client = boto3.client(
        "s3",
        endpoint_url=settings.AWS_S3_ENDPOINT_URL,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_S3_REGION_NAME,
        config=Config(connect_timeout=3, read_timeout=5, retries={"max_attempts": 1}),
    )
    bucket = f"test-{uuid.uuid4().hex}"
    client.create_bucket(Bucket=bucket)
    try:
        yield client, bucket
    finally:
        for page in client.get_paginator("list_objects_v2").paginate(Bucket=bucket):
            for item in page.get("Contents", []):
                client.delete_object(Bucket=bucket, Key=item["Key"])
        client.delete_bucket(Bucket=bucket)
