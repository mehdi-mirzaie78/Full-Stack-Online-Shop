"""Identity capabilities; role ceilings remain authoritative over individual grants."""

from django.contrib.auth.models import Group, Permission
from django.db import transaction
from django.db.models import Q
from rest_framework.exceptions import APIException, PermissionDenied, ValidationError

from .models import User

CAPABILITIES = {
    "view_user": "View users and login sessions",
    "add_user": "Create customer accounts",
    "change_user": "Edit customer accounts",
    "revoke_loginsession": "Revoke customer login sessions",
}


class PermissionConflict(APIException):
    status_code = 409
    default_detail = "Permissions changed. Reload before saving."


def role_group(role: str) -> str:
    return f"identity-role:{role}"


def effective_permissions(user: User) -> set[str]:
    if not user.is_authenticated or not user.is_active or user.is_deleted:
        return set()
    if user.role == User.Role.SUPERADMIN and user.is_superuser:
        return set(CAPABILITIES)
    if user.role == User.Role.CUSTOMER:
        return set()
    permissions = set(
        Permission.objects.filter(
            Q(user=user) | Q(group__name=role_group(user.role)),
            content_type__app_label="identity",
            codename__in=CAPABILITIES,
        ).values_list("codename", flat=True)
    )
    return permissions & {"view_user"} if user.role == User.Role.AUDITOR else permissions


def require_capability(actor: User, capability: str = "view_user") -> None:
    granted = effective_permissions(actor)
    if "view_user" not in granted or capability not in granted:
        raise PermissionDenied("You do not have permission for this identity operation.")


def require_superadmin(actor: User) -> None:
    if not (
        actor.is_active
        and not actor.is_deleted
        and actor.is_superuser
        and actor.role == User.Role.SUPERADMIN
    ):
        raise PermissionDenied("Only a super administrator can manage passwords and permissions.")


def permission_records(codes: list[str]):
    if len(codes) != len(set(codes)) or set(codes) - CAPABILITIES.keys():
        raise ValidationError({"permissions": "Select distinct supported identity permissions."})
    return Permission.objects.filter(content_type__app_label="identity", codename__in=codes)


def direct_permissions(user: User) -> list[str]:
    return sorted(
        user.user_permissions.filter(
            content_type__app_label="identity",
            codename__in=CAPABILITIES,
        ).values_list("codename", flat=True)
    )


def inherited_permissions(role: str) -> list[str]:
    if role == User.Role.SUPERADMIN:
        return sorted(CAPABILITIES)
    return sorted(
        Permission.objects.filter(
            group__name=role_group(role),
            content_type__app_label="identity",
            codename__in=CAPABILITIES,
        ).values_list("codename", flat=True)
    )


def access_catalog() -> dict:
    return {
        "permissions": [{"codename": code, "label": label} for code, label in CAPABILITIES.items()],
        "roles": [{"role": role, "permissions": inherited_permissions(role)} for role in User.Role],
    }


def inspect_user_permissions(user: User) -> dict:
    return {
        "role": user.role,
        "permissions": direct_permissions(user),
        "inherited": inherited_permissions(user.role),
        "effective": sorted(effective_permissions(user)),
    }


def replace_permissions(
    actor: User, codes: list[str], expected: list[str], *, role=None, user_id=None
):
    with transaction.atomic():
        list(User.objects.select_for_update().filter(role=User.Role.SUPERADMIN).order_by("id"))
        require_superadmin(User.all_objects.get(pk=actor.pk))
        records = permission_records(codes)
        if role is not None:
            if role not in User.Role.values or role in (User.Role.SUPERADMIN, User.Role.CUSTOMER):
                raise ValidationError({"role": "This role has fixed permissions."})
            if role == User.Role.AUDITOR and set(codes) - {"view_user"}:
                raise ValidationError({"permissions": "Auditors must remain read-only."})
            group = Group.objects.select_for_update().get(name=role_group(role))
            current = inherited_permissions(role)
            relation = group.permissions
        else:
            user = User.all_objects.select_for_update().get(pk=user_id)
            if user.role in (User.Role.SUPERADMIN, User.Role.CUSTOMER):
                raise ValidationError({"permissions": "This account's role has fixed permissions."})
            if user.role == User.Role.AUDITOR and set(codes) - {"view_user"}:
                raise ValidationError({"permissions": "Auditors must remain read-only."})
            current = direct_permissions(user)
            relation = user.user_permissions
        if sorted(expected) != current:
            raise PermissionConflict()
        # This endpoint owns only its allowlisted identity grants; retain unrelated permissions.
        relation.remove(
            *relation.filter(content_type__app_label="identity", codename__in=CAPABILITIES)
        )
        relation.add(*records)
