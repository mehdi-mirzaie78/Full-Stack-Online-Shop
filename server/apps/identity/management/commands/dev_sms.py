from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from apps.identity.otp import connection, fingerprint


class Command(BaseCommand):
    help = "Read a short-lived development-only SMS code from Redis."

    def add_arguments(self, parser):
        parser.add_argument("phone")

    def handle(self, *args, **options):
        if not settings.DEBUG or not settings.DEV_SMS_REDIS:
            raise CommandError("Development SMS inspection is disabled.")
        code = connection().get(f"dev:sms:{fingerprint(options['phone'])}")
        if not code:
            raise CommandError("No development code found, or it expired.")
        self.stdout.write(code)
