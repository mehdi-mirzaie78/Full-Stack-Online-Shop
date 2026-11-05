"""Synthetic browser fixtures only; never expose an HTTP test-code endpoint."""

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

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
        elif options["action"] == "seed":
            for phone, role in [
                ("+989120000001", User.Role.SUPERADMIN),
                ("+989120000002", User.Role.AUDITOR),
                ("+989120000003", User.Role.CUSTOMER),
            ]:
                user, _ = User.objects.get_or_create(
                    phone=phone,
                    defaults={
                        "role": role,
                        "is_superuser": role == User.Role.SUPERADMIN,
                        "password": "!",
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
