"""Capability boundaries and password writes against real isolated PostgreSQL."""

from datetime import timedelta
from unittest.mock import patch

import pytest
from django.contrib.auth.models import Group, Permission
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied
from rest_framework.test import APIClient

from apps.identity import access, services, tokens
from apps.identity.models import LoginSession, User

pytestmark = [pytest.mark.integration, pytest.mark.django_db]
BASE = "/api/v1/"
PASSWORD = "Synthetic-Account-Password-942!"


@pytest.fixture(autouse=True)
def role_defaults():
    for role in User.Role:
        group, _ = Group.objects.get_or_create(name=access.role_group(role))
        group.permissions.clear()
        if role == User.Role.AUDITOR:
            group.permissions.add(
                Permission.objects.get(content_type__app_label="identity", codename="view_user")
            )


@pytest.fixture
def admin():
    return User.objects.create_superuser("+989120000001", PASSWORD)


@pytest.fixture
def client(admin):
    client = APIClient()
    client.force_authenticate(admin)
    return client


def grant(user, *codes):
    user.user_permissions.set(access.permission_records(list(codes)))


def create_customer(client, **extra):
    return client.post(
        BASE + "staff/users",
        {"phone": "+989120000099", "first_name": "Test", "last_name": "Customer", **extra},
        format="json",
    )


def test_password_create_is_hashed_write_only_and_authenticates(client):
    response = create_customer(client, password=PASSWORD)
    assert response.status_code == 201, response.data
    assert "password" not in response.data
    user = User.objects.get(pk=response.data["id"])
    assert user.password != PASSWORD and user.check_password(PASSWORD)
    anonymous = APIClient(enforce_csrf_checks=True)
    csrf = anonymous.get(BASE + "auth/csrf").data["csrfToken"]
    with patch("apps.identity.otp.limit_password_attempt"):
        login = anonymous.post(
            BASE + "auth/password",
            {"phone": user.phone, "password": PASSWORD},
            format="json",
            HTTP_X_CSRFTOKEN=csrf,
        )
    assert login.status_code == 200
    assert anonymous.get(BASE + "auth/me").data["id"] == str(user.pk)


@pytest.mark.parametrize("password", ["", "short", "123456789", "password", "x" * 129])
def test_invalid_password_does_not_create_account(client, password):
    response = create_customer(client, password=password)
    assert response.status_code == 400
    assert not User.objects.filter(phone="+989120000099").exists()


def test_omitted_password_remains_unusable_and_patch_preserves_hash(client):
    response = create_customer(client)
    user = User.objects.get(pk=response.data["id"])
    assert not user.has_usable_password()
    user.set_password(PASSWORD)
    user.save()
    original = user.password
    response = client.patch(BASE + f"staff/users/{user.pk}", {"is_active": True}, format="json")
    assert response.status_code == 200
    user.refresh_from_db()
    assert user.password == original


def test_reset_password_revokes_existing_access_and_refresh(client):
    user = User.objects.create_user("+989120000099", PASSWORD)
    token, refresh = tokens.issue_session(user)
    response = client.patch(
        BASE + f"staff/users/{user.pk}", {"password": PASSWORD + "-new"}, format="json"
    )
    assert response.status_code == 200
    user.refresh_from_db()
    assert user.check_password(PASSWORD + "-new")
    assert user.login_sessions.get().revoked_at is not None
    browser = APIClient()
    browser.cookies["shop_access"] = token
    assert browser.get(BASE + "auth/me").status_code == 401
    from rest_framework.exceptions import AuthenticationFailed

    with pytest.raises(AuthenticationFailed):
        tokens.rotate_session(refresh)


@pytest.mark.parametrize(
    "role", [User.Role.OPERATOR, User.Role.PRODUCT_MANAGER, User.Role.AUDITOR, User.Role.CUSTOMER]
)
def test_non_superadmin_cannot_set_password_or_grant_permissions(client, role):
    actor = User.objects.create_user("+989120000005", role=role)
    grant(actor, *access.CAPABILITIES)
    client.force_authenticate(actor)
    assert create_customer(client, password=PASSWORD).status_code == 403
    assert client.get(BASE + "staff/access").status_code == 403
    assert (
        client.patch(
            BASE + "staff/roles/OPERATOR/permissions",
            {"permissions": ["view_user"], "expected_permissions": []},
            format="json",
        ).status_code
        == 403
    )
    assert (
        client.patch(
            BASE + f"staff/users/{actor.pk}/permissions",
            {"permissions": [], "expected_permissions": []},
            format="json",
        ).status_code
        == 403
    )


def test_role_and_direct_grants_are_effective_on_next_request(client):
    operator = User.objects.create_user("+989120000005", role="OPERATOR")
    browser = APIClient()
    browser.cookies["shop_access"] = tokens.issue_session(operator)[0]
    assert browser.get(BASE + "staff/users").status_code == 403
    response = client.patch(
        BASE + "staff/roles/OPERATOR/permissions",
        {"permissions": ["view_user"], "expected_permissions": []},
        format="json",
    )
    assert response.status_code == 200
    assert browser.get(BASE + "staff/users").status_code == 200
    assert browser.get(BASE + "auth/me").data["permissions"] == ["view_user"]
    response = client.patch(
        BASE + f"staff/users/{operator.pk}/permissions",
        {"permissions": ["add_user"], "expected_permissions": []},
        format="json",
    )
    assert response.status_code == 200
    delegated = APIClient()
    delegated.force_authenticate(operator)
    assert create_customer(delegated).status_code == 201
    assert create_customer(delegated, role="SUPERADMIN").status_code == 403
    assert (
        client.patch(
            BASE + "staff/roles/OPERATOR/permissions",
            {"permissions": [], "expected_permissions": ["view_user"]},
            format="json",
        ).status_code
        == 200
    )
    assert browser.get(BASE + "staff/users").status_code == 403


def test_delegated_editor_only_changes_customers_and_cannot_elevate(client, admin):
    operator = User.objects.create_user("+989120000005", role="OPERATOR")
    customer = User.objects.create_user("+989120000099")
    grant(operator, "view_user", "change_user", "revoke_loginsession")
    client.force_authenticate(operator)
    assert (
        client.patch(
            BASE + f"staff/users/{customer.pk}", {"phone": "+989120000098"}, format="json"
        ).status_code
        == 200
    )
    for data, target in [
        ({"role": "OPERATOR"}, customer),
        ({"is_active": False}, admin),
        ({"password": PASSWORD}, customer),
    ]:
        assert (
            client.patch(BASE + f"staff/users/{target.pk}", data, format="json").status_code == 403
        )
    session = LoginSession.objects.create(
        user=customer, refresh_digest="synthetic", expires_at=timezone.now() + timedelta(days=1)
    )
    assert client.post(BASE + f"staff/sessions/{session.pk}/revoke").status_code == 204
    session = LoginSession.objects.create(
        user=admin, refresh_digest="synthetic", expires_at=timezone.now() + timedelta(days=1)
    )
    assert client.post(BASE + f"staff/sessions/{session.pk}/revoke").status_code == 403


@pytest.mark.parametrize(
    "role, codes",
    [
        ("AUDITOR", ["change_user"]),
        ("CUSTOMER", ["view_user"]),
        ("SUPERADMIN", []),
        ("UNKNOWN", []),
    ],
)
def test_fixed_role_ceilings(client, role, codes):
    response = client.patch(
        BASE + f"staff/roles/{role}/permissions",
        {"permissions": codes, "expected_permissions": []},
        format="json",
    )
    assert response.status_code == 400


def test_unknown_duplicate_and_stale_grants_rejected(client):
    for codes in [["delete_user"], ["view_user", "view_user"]]:
        assert (
            client.patch(
                BASE + "staff/roles/OPERATOR/permissions",
                {"permissions": codes, "expected_permissions": []},
                format="json",
            ).status_code
            == 400
        )
    data = {"permissions": ["view_user"], "expected_permissions": []}
    assert (
        client.patch(BASE + "staff/roles/OPERATOR/permissions", data, format="json").status_code
        == 200
    )
    assert (
        client.patch(BASE + "staff/roles/OPERATOR/permissions", data, format="json").status_code
        == 409
    )
    assert access.inherited_permissions("OPERATOR") == ["view_user"]


def test_use_cases_recheck_authorization_and_prevent_mass_assignment(admin):
    admin.is_active = False
    admin.save()
    with pytest.raises(PermissionDenied):
        services.save_user(admin, {"phone": "+989120000099", "password": PASSWORD})
    admin.is_active = True
    admin.save()
    client = APIClient()
    client.force_authenticate(admin)
    for field in ["is_superuser", "user_permissions", "groups", "permissions"]:
        assert create_customer(client, **{field: True}).status_code == 400


def test_cookie_permission_changes_require_csrf(admin):
    client = APIClient(enforce_csrf_checks=True)
    client.cookies["shop_access"] = tokens.issue_session(admin)[0]
    assert (
        client.patch(
            BASE + "staff/roles/OPERATOR/permissions",
            {"permissions": [], "expected_permissions": []},
            format="json",
        ).status_code
        == 403
    )


def test_use_case_reloads_stale_actor_before_writing(admin):
    User.all_objects.filter(pk=admin.pk).update(is_active=False)
    assert admin.is_active  # Caller still holds the earlier instance.
    with pytest.raises(PermissionDenied):
        services.save_user(admin, {"phone": "+989120000099"})
    assert not User.objects.filter(phone="+989120000099").exists()


def test_direct_grant_removal_and_stale_edit_do_not_remove_inherited_access(client):
    user = User.objects.create_user("+989120000005", role="OPERATOR")
    Group.objects.get(name=access.role_group("OPERATOR")).permissions.add(
        *access.permission_records(["view_user"])
    )
    grant(user, "change_user")
    path = BASE + f"staff/users/{user.pk}/permissions"
    response = client.patch(
        path, {"permissions": [], "expected_permissions": ["change_user"]}, format="json"
    )
    assert response.status_code == 200
    assert response.data["permissions"] == []
    assert response.data["inherited"] == ["view_user"]
    assert (
        client.patch(
            path,
            {"permissions": ["add_user"], "expected_permissions": ["change_user"]},
            format="json",
        ).status_code
        == 409
    )
    assert access.effective_permissions(user) == {"view_user"}


@pytest.mark.parametrize(
    "role,expected",
    [("OPERATOR", 403), ("PRODUCT_MANAGER", 403), ("CUSTOMER", 403), ("AUDITOR", 200)],
)
def test_initial_role_access_without_individual_grants(client, role, expected):
    actor = User.objects.create_user("+989120000005", role=role)
    client.force_authenticate(actor)
    assert client.get(BASE + "staff/users").status_code == expected
    assert create_customer(client).status_code == 403


def test_names_create_projection_edit_and_partial_updates(client):
    response = create_customer(client, first_name="  علی  ", last_name=" آزمایشی ")
    assert response.status_code == 201
    assert response.data["first_name"] == "علی"
    assert response.data["last_name"] == "آزمایشی"
    user = User.objects.get(pk=response.data["id"])
    path = BASE + f"staff/users/{user.pk}"
    assert client.get(path).data["user"]["last_name"] == "آزمایشی"
    assert client.patch(path, {"first_name": "سارا"}, format="json").status_code == 200
    user.refresh_from_db()
    assert (user.first_name, user.last_name) == ("سارا", "آزمایشی")
    assert client.patch(path, {"is_active": False}, format="json").status_code == 200
    user.refresh_from_db()
    assert user.first_name == "سارا"


@pytest.mark.parametrize("field", ["first_name", "last_name"])
@pytest.mark.parametrize("value", ["", "   ", "x" * 151, None])
def test_invalid_names_cannot_create_or_replace_existing_names(client, field, value):
    assert create_customer(client, **{field: value}).status_code == 400
    user = User.objects.create_user("+989120000098", first_name="Test", last_name="User")
    assert (
        client.patch(BASE + f"staff/users/{user.pk}", {field: value}, format="json").status_code
        == 400
    )
    user.refresh_from_db()
    assert (user.first_name, user.last_name) == ("Test", "User")


def test_staff_creation_requires_both_names_but_legacy_accounts_stay_readable(client, admin):
    response = client.post(BASE + "staff/users", {"phone": "+989120000099"}, format="json")
    assert response.status_code == 400
    assert set(response.data) == {"first_name", "last_name"}
    response = client.get(BASE + f"staff/users/{admin.pk}")
    assert response.status_code == 200
    assert response.data["user"]["first_name"] == ""
    assert (
        client.patch(
            BASE + f"staff/users/{admin.pk}", {"phone": admin.phone}, format="json"
        ).status_code
        == 200
    )
