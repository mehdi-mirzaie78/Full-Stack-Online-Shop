"""Redis owns OTP expiry, request windows and single-use verification atomically."""

import hashlib
import hmac
import secrets

import redis
from django.conf import settings
from rest_framework.exceptions import APIException, ValidationError


class DeliveryUnavailable(APIException):
    status_code = 503
    default_detail = "SMS delivery is not configured."


class RateLimited(APIException):
    status_code = 429
    default_detail = "Too many attempts. Please try again later."


def fingerprint(value: str) -> str:
    return hmac.new(settings.SECRET_KEY.encode(), value.encode(), hashlib.sha256).hexdigest()


def connection() -> redis.Redis:
    return redis.Redis.from_url(
        settings.REDIS_URL, socket_connect_timeout=3, socket_timeout=3, decode_responses=True
    )


REQUEST_LIMIT = """
local t = redis.call('TIME')
local now = t[1] * 1000 + math.floor(t[2] / 1000)
for i=1,2 do
    redis.call('ZREMRANGEBYSCORE', KEYS[i], '-inf', now - 600000)
    if redis.call('ZCARD', KEYS[i]) >= 3 then return 0 end
end
for i=1,2 do
    redis.call('ZADD', KEYS[i], now, ARGV[1])
    redis.call('PEXPIRE', KEYS[i], 600000)
end
"""
REQUEST = (
    REQUEST_LIMIT
    + """
redis.call('HSET', KEYS[3], 'digest', ARGV[2], 'attempts', 0)
redis.call('EXPIRE', KEYS[3], 120)
return 1
"""
)
VERIFY = """
local digest = redis.call('HGET', KEYS[1], 'digest')
if not digest then return 0 end
if digest == ARGV[1] then redis.call('DEL', KEYS[1]); return 1 end
if redis.call('HINCRBY', KEYS[1], 'attempts', 1) >= 5 then redis.call('DEL', KEYS[1]) end
return 0
"""


def request_code(phone: str, ip: str) -> None:
    # No real sender is selected yet; never log codes or silently claim delivery.
    testing = settings.TESTING_SMS_SENDER and getattr(settings, "TESTING", False)
    development = settings.DEBUG and settings.DEV_SMS_REDIS
    if not (testing or development):
        raise DeliveryUnavailable()
    code = f"{secrets.randbelow(1000000):06d}"
    client = connection()
    accepted = client.eval(
        REQUEST,
        3,
        f"otp:phone:{fingerprint(phone)}",
        f"otp:ip:{fingerprint(ip)}",
        f"otp:code:{fingerprint(phone)}",
        secrets.token_hex(16),
        fingerprint(phone + code),
    )
    if not accepted:
        raise RateLimited()
    # Test-only mailbox; no HTTP endpoint exposes it. Browser fixtures read it via CLI.
    prefix = "test:sms" if testing else "dev:sms"
    client.set(f"{prefix}:{fingerprint(phone)}", code, ex=120)


def verify_code(phone: str, code: str) -> None:
    if not connection().eval(
        VERIFY, 1, f"otp:code:{fingerprint(phone)}", fingerprint(phone + code)
    ):
        raise ValidationError({"code": "Invalid or expired code."})


def limit_password_attempt(phone: str, ip: str) -> None:
    accepted = connection().eval(
        REQUEST_LIMIT + "return 1",
        2,
        f"otp:phone:{fingerprint(phone)}",
        f"otp:ip:{fingerprint(ip)}",
        secrets.token_hex(16),
    )
    if not accepted:
        raise RateLimited()
