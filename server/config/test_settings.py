"""Fixed, disposable resources; inherited development URLs are never used."""

from .settings import *  # noqa: F403

TESTING = True
SECRET_KEY = "test-only-not-a-production-secret"
DEBUG = False
ALLOWED_HOSTS = ["localhost", "127.0.0.1", "testserver"]
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "HOST": "127.0.0.1",
        "PORT": "55432",
        "NAME": "shop_test",
        "USER": "shop_test",
        "PASSWORD": "test-only",
        "TEST": {"NAME": "test_shop_test"},
    }
}
REDIS_URL = "redis://127.0.0.1:56379/15"
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": REDIS_URL,
        "KEY_PREFIX": "shop-tests",
    }
}
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
CELERY_BROKER_URL = "memory://"
CELERY_RESULT_BACKEND = "cache+memory://"
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.InMemoryStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}
AWS_ACCESS_KEY_ID = "shop-test"
AWS_SECRET_ACCESS_KEY = "test-only"
AWS_STORAGE_BUCKET_NAME = "shop-test-media"
AWS_S3_ENDPOINT_URL = "http://127.0.0.1:59000"
AWS_S3_REGION_NAME = "us-east-1"
OTEL_ENABLED = False
OTEL_EXPORTER_OTLP_ENDPOINT = ""

AUTH_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
CSRF_TRUSTED_ORIGINS = ["http://127.0.0.1:3100"]
CORS_ALLOWED_ORIGINS = ["http://127.0.0.1:3100"]
TESTING_SMS_SENDER = True

JWT_SECRET_KEY = "isolated-test-jwt-signing-key-not-for-production"
