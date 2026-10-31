from django.urls import path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

from apps.core.health import health_check, health_db, health_redis

urlpatterns = [
    # Global Health Check Endpoints
    path("api/health/", health_check, name="health-check"),
    path("api/health/db/", health_db, name="health-db"),
    path("api/health/redis/", health_redis, name="health-redis"),
    # OpenAPI Documentation Endpoints
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
]
