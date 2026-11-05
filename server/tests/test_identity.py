import concurrent.futures
from datetime import timedelta
from unittest.mock import patch

import jwt
import pytest
from django.conf import settings
from django.db import IntegrityError, transaction
from django.test import override_settings
from django.utils import timezone
from rest_framework.exceptions import AuthenticationFailed, ValidationError
from rest_framework.test import APIClient

from apps.identity import otp, tokens
from apps.identity.models import LoginSession, User

pytestmark = [pytest.mark.integration, pytest.mark.django_db]
BASE = "/api/v1/"
PHONE = "+989121234567"


@pytest.fixture(autouse=True)
def clean_redis():
    client = otp.connection()
    client.flushdb()
    yield
    client.flushdb()


@pytest.fixture
def client():
    return APIClient(enforce_csrf_checks=True)


def post(client, path, data=None):
    if path == "staff/users":
        data = {"first_name": "Test", "last_name": "Customer", **(data or {})}
    csrf = client.get(BASE + "auth/csrf").json()["csrfToken"]
    return client.post(BASE + path, data or {}, format="json", HTTP_X_CSRFTOKEN=csrf)


def signin(client, phone=PHONE):
    assert post(client, "auth/otp/request", {"phone": phone}).status_code == 202
    code = otp.connection().get(f"test:sms:{otp.fingerprint(phone)}")
    return post(client, "auth/otp/verify", {"phone": phone, "code": code})


def as_role(client, role):
    user = User.objects.create_user(PHONE, role=role)
    access, refresh = tokens.issue_session(user)
    client.cookies["shop_access"] = access
    client.cookies["shop_refresh"] = refresh
    return user


def test_signup_cookie_security_and_logout(client):
    response = signin(client)
    assert response.status_code == 200
    assert "code" not in response.json()
    assert response.cookies["shop_access"]["httponly"]
    assert response.cookies["shop_refresh"]["samesite"] == "Lax"
    me = client.get(BASE + "auth/me")
    assert me.json()["role"] == User.Role.CUSTOMER
    assert "no-store" in me["Cache-Control"]
    assert "Cookie" in me["Vary"]
    assert not User.objects.get(phone=PHONE).has_usable_password()
    assert post(client, "auth/logout").status_code == 204
    assert client.get(BASE + "auth/me").status_code == 401
    assert LoginSession.objects.get().revoked_at is not None


def test_csrf_required_for_anonymous_login_and_cookie_writes(client):
    assert client.post(BASE + "auth/otp/request", {"phone": PHONE}).status_code == 403
    as_role(client, User.Role.SUPERADMIN)
    assert client.post(BASE + "staff/users", {"phone": "+989129999999"}).status_code == 403
    csrf = client.get(BASE + "auth/csrf").json()["csrfToken"]
    assert (
        client.post(
            BASE + "auth/otp/request",
            {"phone": PHONE},
            HTTP_X_CSRFTOKEN=csrf,
            HTTP_ORIGIN="https://attacker.invalid",
        ).status_code
        == 403
    )


def test_unconfigured_sender_returns_503_without_claiming_delivery(client):
    with override_settings(TESTING_SMS_SENDER=False):
        assert post(client, "auth/otp/request", {"phone": PHONE}).status_code == 503
    with override_settings(TESTING=False):
        assert post(client, "auth/otp/request", {"phone": PHONE}).status_code == 503
    assert not otp.connection().exists(f"otp:code:{otp.fingerprint(PHONE)}")


def test_redis_outage_returns_503(client):
    import redis

    with patch("apps.identity.otp.connection", side_effect=redis.ConnectionError("private")):
        response = post(client, "auth/otp/request", {"phone": PHONE})
    assert response.status_code == 503
    assert "private" not in str(response.content)


@pytest.mark.parametrize("phone", ["09121234567", "+0123456789", "+98<script>", "123", ""])
def test_phone_boundary_validation(client, phone):
    assert post(client, "auth/otp/request", {"phone": phone}).status_code == 400


def test_otp_ttl_attempt_limit_expiry_and_replay(client):
    otp.request_code(PHONE, "127.0.0.1")
    key = f"otp:code:{otp.fingerprint(PHONE)}"
    assert 115 <= otp.connection().ttl(key) <= 120
    code = otp.connection().get(f"test:sms:{otp.fingerprint(PHONE)}")
    with pytest.raises(ValidationError):
        otp.verify_code(PHONE, "invalid")
    otp.verify_code(PHONE, code)
    with pytest.raises(ValidationError):
        otp.verify_code(PHONE, code)
    otp.request_code(PHONE, "127.0.0.1")
    for _ in range(5):
        with pytest.raises(ValidationError):
            otp.verify_code(PHONE, "invalid")
    assert not otp.connection().exists(key)
    otp.request_code(PHONE, "127.0.0.1")
    otp.connection().delete(key)
    with pytest.raises(ValidationError):
        otp.verify_code(PHONE, code)


def test_request_rate_limits_phone_and_ip_and_expires_old_window(client):
    for _ in range(3):
        otp.request_code(PHONE, "127.0.0.1")
    with pytest.raises(otp.RateLimited):
        otp.request_code(PHONE, "127.0.0.2")
    assert post(client, "auth/otp/request", {"phone": "+989120000009"}).status_code == 429
    for key in otp.connection().scan_iter("otp:*phone:*"):
        otp.connection().zadd(key, dict.fromkeys(otp.connection().zrange(key, 0, -1), 0))
    for key in otp.connection().scan_iter("otp:ip:*"):
        otp.connection().zadd(key, dict.fromkeys(otp.connection().zrange(key, 0, -1), 0))
    otp.request_code(PHONE, "127.0.0.1")


def test_otp_single_use_under_concurrent_verification():
    otp.request_code(PHONE, "127.0.0.1")
    code = otp.connection().get(f"test:sms:{otp.fingerprint(PHONE)}")

    def verify():
        try:
            otp.verify_code(PHONE, code)
            return True
        except ValidationError:
            return False

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        assert sorted(pool.map(lambda _: verify(), range(2))) == [False, True]


def test_refresh_rotation_replay_revokes_access(client):
    assert signin(client).status_code == 200
    old_refresh = client.cookies["shop_refresh"].value
    assert post(client, "auth/refresh").status_code == 200
    assert client.cookies["shop_refresh"].value != old_refresh
    assert client.get(BASE + "auth/me").status_code == 200
    client.cookies["shop_refresh"] = old_refresh
    assert post(client, "auth/refresh").status_code == 401
    assert client.get(BASE + "auth/me").status_code == 401
    assert LoginSession.objects.get().revoked_at


def test_expired_access_can_refresh_and_wrong_type_rejected(client):
    user = as_role(client, User.Role.CUSTOMER)
    session = LoginSession.objects.get(user=user)
    expired = jwt.encode(
        {
            "sub": str(user.pk),
            "sid": str(session.pk),
            "type": "access",
            "jti": "test",
            "iat": timezone.now() - timedelta(hours=1),
            "exp": timezone.now() - timedelta(seconds=1),
            "iss": "shop-identity",
            "aud": "shop",
        },
        settings.JWT_SECRET_KEY,
        algorithm="HS256",
    )
    client.cookies["shop_access"] = expired
    assert client.get(BASE + "auth/me").status_code == 401
    assert post(client, "auth/refresh").status_code == 200
    assert client.get(BASE + "auth/me").status_code == 200
    with pytest.raises(AuthenticationFailed):
        tokens.decode(client.cookies["shop_refresh"].value, "access")
    client.cookies["shop_refresh"] = "invalid"
    assert post(client, "auth/logout").status_code == 204


@pytest.mark.parametrize(
    "role", [User.Role.CUSTOMER, User.Role.OPERATOR, User.Role.PRODUCT_MANAGER]
)
def test_roles_cannot_inspect_or_mutate_identities(client, role):
    actor = as_role(client, role)
    assert client.get(BASE + "staff/users").status_code == 403
    assert client.get(BASE + f"staff/users/{actor.pk}").status_code == 403
    assert (
        post(client, "staff/users", {"phone": "+989120000099", "role": "SUPERADMIN"}).status_code
        == 403
    )


def test_auditor_read_only_and_sessions_do_not_expose_tokens(client):
    actor = as_role(client, User.Role.AUDITOR)
    assert client.get(BASE + "staff/users").status_code == 200
    response = client.get(BASE + f"staff/users/{actor.pk}")
    assert response.status_code == 200
    assert set(response.json()["sessions"][0]) == {"id", "created_at", "expires_at", "revoked_at"}
    assert post(client, "staff/users", {"phone": "+989120000099"}).status_code == 403
    assert post(client, f"staff/sessions/{LoginSession.objects.get().pk}/revoke").status_code == 403


def patch_user(client, user, data):
    csrf = client.get(BASE + "auth/csrf").json()["csrfToken"]
    return client.patch(BASE + f"staff/users/{user.pk}", data, format="json", HTTP_X_CSRFTOKEN=csrf)


def test_staff_user_create_search_edit_archive_restore_and_revoke(client):
    actor = as_role(client, User.Role.SUPERADMIN)
    response = post(client, "staff/users", {"phone": "+989120000099", "role": "OPERATOR"})
    assert response.status_code == 201, response.content
    user = User.objects.get(pk=response.json()["id"])
    assert client.get(BASE + "staff/users?search=000099").json()["count"] == 1
    assert post(client, "staff/users", {"phone": user.phone}).status_code == 400
    tokens.issue_session(user)
    assert patch_user(client, user, {"is_deleted": True}).status_code == 200
    assert not User.objects.filter(pk=user.pk).exists()
    assert User.all_objects.get(pk=user.pk).deleted_at is not None
    assert user.login_sessions.get().revoked_at
    assert (
        patch_user(client, user, {"is_deleted": False, "role": "PRODUCT_MANAGER"}).status_code
        == 200
    )
    assert User.objects.get(pk=user.pk).role == "PRODUCT_MANAGER"
    assert patch_user(client, actor, {"role": "CUSTOMER"}).status_code == 400
    assert post(client, f"staff/sessions/{actor.login_sessions.get().pk}/revoke").status_code == 204
    assert client.get(BASE + "auth/me").status_code == 401


@pytest.mark.parametrize("flag", ["is_active", "is_deleted"])
def test_unavailable_account_cannot_sign_in(client, flag):
    User.all_objects.create(phone=PHONE, **{flag: flag == "is_deleted"})
    assert signin(client).status_code == 403
    assert not LoginSession.objects.exists()


def test_user_manager_password_superuser_and_database_constraints():
    user = User.objects.create_superuser(PHONE, "test-password")
    assert user.is_staff and user.is_superuser and user.check_password("test-password")
    tokens.issue_session(user)
    user.delete()
    User.objects.restore()
    assert user.login_sessions.get().revoked_at is not None
    user.delete()
    assert not User.objects.filter(pk=user.pk).exists()
    assert User.all_objects.filter(pk=user.pk).exists()
    with pytest.raises(IntegrityError), transaction.atomic():
        User.all_objects.create(phone="invalid")
    with pytest.raises(IntegrityError), transaction.atomic():
        User.all_objects.create(phone="+989120000099", role="UNKNOWN")


def test_development_mailbox_is_debug_only(client):
    with override_settings(DEBUG=True, DEV_SMS_REDIS=True, TESTING=False, TESTING_SMS_SENDER=False):
        otp.request_code(PHONE, "127.0.0.1")
        key = f"dev:sms:{otp.fingerprint(PHONE)}"
        assert len(otp.connection().get(key)) == 6
        assert 115 <= otp.connection().ttl(key) <= 120
        assert not otp.connection().exists(f"test:sms:{otp.fingerprint(PHONE)}")
    with override_settings(DEBUG=False, DEV_SMS_REDIS=True, TESTING_SMS_SENDER=False):
        with pytest.raises(otp.DeliveryUnavailable):
            otp.request_code(PHONE, "127.0.0.1")


def test_password_login_cookie_session_and_csrf(client):
    User.objects.create_user(PHONE, "a-long-local-test-password", role=User.Role.SUPERADMIN)
    assert (
        client.post(
            BASE + "auth/password", {"phone": PHONE, "password": "a-long-local-test-password"}
        ).status_code
        == 403
    )
    assert post(client, "auth/password", {"phone": PHONE, "password": "wrong"}).status_code == 401
    response = post(
        client, "auth/password", {"phone": PHONE, "password": "a-long-local-test-password"}
    )
    assert response.status_code == 200
    assert response.cookies["shop_access"]["httponly"]
    assert client.get(BASE + "staff/users").status_code == 200
    assert post(client, "auth/logout").status_code == 204


def test_password_attempt_limit_and_unavailable_user(client):
    User.objects.create_user(PHONE, "a-long-local-test-password", is_active=False)
    for _ in range(3):
        assert (
            post(
                client, "auth/password", {"phone": PHONE, "password": "a-long-local-test-password"}
            ).status_code
            == 401
        )
    assert (
        post(
            client, "auth/password", {"phone": PHONE, "password": "a-long-local-test-password"}
        ).status_code
        == 429
    )
    assert not LoginSession.objects.exists()
