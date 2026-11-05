from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied, ValidationError

from .models import LoginSession, User


def require_user_management(actor: User, *, write: bool = False) -> None:
    allowed = [User.Role.SUPERADMIN] if write else [User.Role.SUPERADMIN, User.Role.AUDITOR]
    if (
        not actor.is_authenticated
        or not actor.is_active
        or actor.is_deleted
        or actor.role not in allowed
    ):
        raise PermissionDenied("You cannot manage staff identities.")


def inspect_users(actor: User):
    require_user_management(actor)
    return User.all_objects.all().order_by("phone")


def save_user(actor: User, data: dict, identifier=None) -> User:
    require_user_management(actor, write=True)
    with transaction.atomic():
        # Serialize staff mutations so two administrators cannot remove each other concurrently.
        list(User.objects.select_for_update().filter(role=User.Role.SUPERADMIN).order_by("id"))
        actor = User.all_objects.get(pk=actor.pk)
        require_user_management(actor, write=True)
        user = User.all_objects.select_for_update().get(pk=identifier) if identifier else User()
        if user.pk == actor.pk and any(
            data.get(key, getattr(user, key)) != getattr(user, key)
            for key in ("role", "is_active", "is_deleted")
        ):
            raise ValidationError("Use another administrator to change your own access.")
        for key, value in data.items():
            setattr(user, key, value)
        user.deleted_at = (user.deleted_at or timezone.now()) if user.is_deleted else None
        user.is_superuser = user.role == User.Role.SUPERADMIN
        if not identifier:
            user.set_unusable_password()
        user.full_clean(exclude=["password"])
        user.save()
        if not user.is_active or user.is_deleted:
            user.revoke_sessions()
    return user


def revoke_session(actor: User, session: LoginSession) -> None:
    require_user_management(actor, write=True)
    LoginSession.objects.filter(pk=session.pk, revoked_at__isnull=True).update(
        revoked_at=timezone.now()
    )
