import logging

from django.core.cache import cache
from django.db import connection
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

logger = logging.getLogger(__name__)


def check_database() -> tuple[bool, str]:
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1;")
            cursor.fetchone()
        return True, "ok"
    except Exception:
        logger.exception("database_unavailable", extra={"event": "database_unavailable"})
        return False, "unavailable"


def check_redis() -> tuple[bool, str]:
    try:
        cache.set("health_ping", "pong", timeout=10)
        val = cache.get("health_ping")
        if val == "pong":
            return True, "ok"
        logger.warning("cache_mismatch", extra={"event": "cache_mismatch"})
        return False, "cache read mismatch"
    except Exception:
        logger.exception("redis_unavailable", extra={"event": "redis_unavailable"})
        return False, "unavailable"


@api_view(["GET"])
@permission_classes([AllowAny])
def health_check(request):
    """Aggregate health check for all core services."""
    db_ok, db_msg = check_database()
    redis_ok, redis_msg = check_redis()

    all_ok = db_ok and redis_ok
    status_code = status.HTTP_200_OK if all_ok else status.HTTP_503_SERVICE_UNAVAILABLE

    return Response(
        {
            "status": "healthy" if all_ok else "unhealthy",
            "services": {
                "database": {"status": "ok" if db_ok else "error", "detail": db_msg},
                "redis": {"status": "ok" if redis_ok else "error", "detail": redis_msg},
            },
        },
        status=status_code,
    )


@api_view(["GET"])
@permission_classes([AllowAny])
def health_db(request):
    """Database connectivity health check."""
    ok, msg = check_database()
    status_code = status.HTTP_200_OK if ok else status.HTTP_503_SERVICE_UNAVAILABLE
    return Response(
        {"service": "database", "status": "ok" if ok else "error", "detail": msg},
        status=status_code,
    )


@api_view(["GET"])
@permission_classes([AllowAny])
def health_redis(request):
    """Redis cache connectivity health check."""
    ok, msg = check_redis()
    status_code = status.HTTP_200_OK if ok else status.HTTP_503_SERVICE_UNAVAILABLE
    return Response(
        {"service": "redis", "status": "ok" if ok else "error", "detail": msg},
        status=status_code,
    )
