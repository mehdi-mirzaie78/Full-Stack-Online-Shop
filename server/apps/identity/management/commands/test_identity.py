"""Synthetic browser fixtures only; never expose an HTTP test-code endpoint."""

from django.conf import settings
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand, CommandError

from apps.identity.access import CAPABILITIES, permission_records, role_group
from apps.identity.models import User
from apps.identity.otp import connection, fingerprint


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("action", choices=["seed", "code", "reset"])
        parser.add_argument("--phone")

    def handle(self, *args, **options):
        if settings.SETTINGS_MODULE != "config.test_settings":
            raise CommandError("This command requires isolated test settings.")
        if options["action"] == "reset":
            connection().flushdb()
            for role in User.Role:
                group, _ = Group.objects.get_or_create(name=role_group(role))
                group.permissions.set(
                    permission_records(["view_user"] if role == User.Role.AUDITOR else [])
                )
            User.user_permissions.through.objects.filter(
                permission__content_type__app_label="identity",
                permission__codename__in=CAPABILITIES,
            ).delete()
        elif options["action"] == "seed":
            for phone, role in [
                ("+989120000001", User.Role.SUPERADMIN),
                ("+989120000002", User.Role.AUDITOR),
                ("+989120000003", User.Role.CUSTOMER),
                ("+989120000004", User.Role.OPERATOR),
            ]:
                user, _ = User.objects.get_or_create(
                    phone=phone,
                    defaults={
                        "role": role,
                        "is_superuser": role == User.Role.SUPERADMIN,
                        "password": "!",
                        "first_name": "Test",
                        "last_name": role.title(),
                    },
                )
                if role == User.Role.SUPERADMIN:
                    user.set_password("isolated-browser-test-password")
                    user.save(update_fields=["password"])
        else:
            code = connection().get(f"test:sms:{fingerprint(options['phone'])}")
            if not code:
                raise CommandError("No synthetic message found.")
            self.stdout.write(code)
