from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as PasswordValidationError
from django.db import transaction
from django.utils import timezone
from django.views.decorators.debug import sensitive_variables
from rest_framework.exceptions import PermissionDenied, ValidationError

from .access import require_capability, require_superadmin
from .models import LoginSession, User


def inspect_users(actor: User):
    require_capability(actor)
    return User.all_objects.all().order_by("phone")


@sensitive_variables("data", "password")
def save_user(actor: User, data: dict, identifier=None) -> User:
    capability = "change_user" if identifier else "add_user"
    require_capability(actor, capability)
    with transaction.atomic():
        # Serialize staff mutations so two administrators cannot remove each other concurrently.
        list(User.objects.select_for_update().filter(role=User.Role.SUPERADMIN).order_by("id"))
        actor = User.all_objects.get(pk=actor.pk)
        require_capability(actor, capability)
        user = User.all_objects.select_for_update().get(pk=identifier) if identifier else User()
        password = data.get("password")
        if password is not None:
            require_superadmin(actor)
        if actor.role != User.Role.SUPERADMIN and (
            user.role != User.Role.CUSTOMER or data.get("role", user.role) != User.Role.CUSTOMER
        ):
            raise PermissionDenied("Delegated editors can manage customer accounts only.")
        if user.pk == actor.pk and any(
            data.get(key, getattr(user, key)) != getattr(user, key)
            for key in ("role", "is_active", "is_deleted")
        ):
            raise ValidationError("Use another administrator to change your own access.")
        if set(data) - {
            "phone",
            "first_name",
            "last_name",
            "role",
            "is_active",
            "is_deleted",
            "password",
        }:
            raise ValidationError("Unsupported account fields.")
        for field in ("first_name", "last_name"):
            if field in data or not identifier:
                value = data.get(field, "")
                if not isinstance(value, str) or not value.strip() or len(value.strip()) > 150:
                    raise ValidationError({field: "Enter a name of 1 to 150 characters."})
                setattr(user, field, value.strip())
        for key in ("phone", "role", "is_active", "is_deleted"):
            if key in data:
                setattr(user, key, data[key])
        user.deleted_at = (user.deleted_at or timezone.now()) if user.is_deleted else None
        user.is_superuser = user.role == User.Role.SUPERADMIN
        if not identifier:
            user.set_unusable_password()
        if password is not None:
            if not isinstance(password, str) or not password or len(password) > 128:
                raise ValidationError({"password": "Enter a password of at most 128 characters."})
            try:
                validate_password(password, user)
            except PasswordValidationError as error:
                raise ValidationError({"password": error.messages}) from error
            user.set_password(password)
        user.full_clean(exclude=["password"])
        user.save()
        if password is not None or not user.is_active or user.is_deleted:
            user.revoke_sessions()
    return user


def revoke_session(actor: User, session: LoginSession) -> None:
    with transaction.atomic():
        list(User.objects.select_for_update().filter(role=User.Role.SUPERADMIN).order_by("id"))
        actor = User.all_objects.get(pk=actor.pk)
        require_capability(actor, "revoke_loginsession")
        target = User.all_objects.select_for_update().get(pk=session.user_id)
        if actor.role != User.Role.SUPERADMIN and target.role != User.Role.CUSTOMER:
            raise PermissionDenied("Delegated editors can revoke customer sessions only.")
        LoginSession.objects.filter(pk=session.pk, revoked_at__isnull=True).update(
            revoked_at=timezone.now()
        )
