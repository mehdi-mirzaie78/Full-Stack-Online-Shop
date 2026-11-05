from uuid import UUID

from django.utils import timezone
from rest_framework.authentication import BaseAuthentication, CSRFCheck
from rest_framework.exceptions import AuthenticationFailed, PermissionDenied

from .models import LoginSession
from .tokens import decode


class CookieAuthentication(BaseAuthentication):
    def authenticate_header(self, request):
        return "Cookie"

    def authenticate(self, request):
        token = request.COOKIES.get("shop_access")
        if not token:
            return None
        claims = decode(token, "access")
        try:
            session = (
                LoginSession.objects.select_related("user")
                .filter(
                    pk=UUID(claims["sid"]),
                    user_id=UUID(claims["sub"]),
                    revoked_at__isnull=True,
                    is_active=True,
                    expires_at__gt=timezone.now(),
                    user__is_active=True,
                    user__is_deleted=False,
                )
                .first()
            )
        except (ValueError, TypeError) as error:
            raise AuthenticationFailed("Invalid session.") from error
        if not session:
            raise AuthenticationFailed("Invalid session.")
        check = CSRFCheck(lambda request: None)
        check.process_request(request)
        if check.process_view(request, None, (), {}):
            raise PermissionDenied("CSRF verification failed.")
        return session.user, session
