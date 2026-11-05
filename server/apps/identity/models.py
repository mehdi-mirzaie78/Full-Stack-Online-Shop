from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.core.validators import RegexValidator
from django.db import models, transaction
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.core.models import BaseModel, SoftDeleteManager

phone_validator = RegexValidator(
    r"^\+[1-9][0-9]{7,14}$", _("Use an international phone number, such as +989121234567.")
)


class UserManager(BaseUserManager, SoftDeleteManager):
    def create_user(self, phone: str, password: str | None = None, **fields):
        fields["is_superuser"] = fields.get("role", User.Role.CUSTOMER) == User.Role.SUPERADMIN
        user = self.model(phone=phone, **fields)
        user.full_clean(exclude=["password"])
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, phone: str, password: str | None = None, **fields):
        fields.update(role=User.Role.SUPERADMIN, is_superuser=True, is_active=True)
        return self.create_user(phone, password, **fields)


class User(BaseModel, AbstractBaseUser, PermissionsMixin):
    class Role(models.TextChoices):
        SUPERADMIN = "SUPERADMIN", _("Super administrator")
        PRODUCT_MANAGER = "PRODUCT_MANAGER", _("Product manager")
        OPERATOR = "OPERATOR", _("Operator")
        AUDITOR = "AUDITOR", _("Auditor")
        CUSTOMER = "CUSTOMER", _("Customer")

    phone = models.CharField(
        _("Phone number"),
        max_length=16,
        unique=True,
        validators=[phone_validator],
        help_text=_("International number with country code."),
    )
    first_name = models.CharField(
        _("First name"),
        max_length=150,
        blank=True,
        default="",
        help_text=_("Given name; required when staff create an account."),
    )
    last_name = models.CharField(
        _("Last name"),
        max_length=150,
        blank=True,
        default="",
        help_text=_("Family name; required when staff create an account."),
    )
    role = models.CharField(
        _("Role"),
        max_length=20,
        choices=Role.choices,
        default=Role.CUSTOMER,
        help_text=_("Business access role."),
    )
    objects = UserManager()
    USERNAME_FIELD = "phone"
    REQUIRED_FIELDS = ["first_name", "last_name"]

    def revoke_sessions(self) -> None:
        LoginSession.all_objects.filter(user=self, revoked_at__isnull=True).update(
            revoked_at=timezone.now()
        )

    def delete(self, using=None, keep_parents=False, hard: bool = False):
        with transaction.atomic():
            self.revoke_sessions()
            return super().delete(using=using, keep_parents=keep_parents, hard=hard)

    @property
    def is_staff(self) -> bool:
        return self.role != self.Role.CUSTOMER and self.is_active and not self.is_deleted

    class Meta(BaseModel.Meta):
        verbose_name = _("User")
        verbose_name_plural = _("Users")
        permissions = [("revoke_loginsession", _("Can revoke customer login sessions"))]
        constraints = [
            models.CheckConstraint(
                condition=(
                    models.Q(role="SUPERADMIN", is_superuser=True)
                    | (~models.Q(role="SUPERADMIN") & models.Q(is_superuser=False))
                ),
                name="identity_superuser_matches_role",
            ),
            models.CheckConstraint(
                condition=models.Q(phone__regex=r"^\+[1-9][0-9]{7,14}$"),
                name="identity_phone_international",
            ),
            models.CheckConstraint(
                condition=models.Q(
                    role__in=["SUPERADMIN", "PRODUCT_MANAGER", "OPERATOR", "AUDITOR", "CUSTOMER"]
                ),
                name="identity_valid_role",
            ),
        ]


class LoginSession(BaseModel):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="login_sessions",
        verbose_name=_("User"),
        help_text=_("Owner of the login session."),
    )
    refresh_digest = models.CharField(
        _("Refresh digest"),
        max_length=64,
        help_text=_("Hash of the current refresh token identifier."),
    )
    expires_at = models.DateTimeField(_("Expires at"), help_text=_("Absolute session expiry."))
    revoked_at = models.DateTimeField(
        _("Revoked at"), null=True, blank=True, help_text=_("Revocation time, if revoked.")
    )

    class Meta(BaseModel.Meta):
        verbose_name = _("Login session")
        verbose_name_plural = _("Login sessions")
