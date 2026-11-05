import redis
from django.conf import settings
from django.contrib.auth import authenticate
from django.core.exceptions import ValidationError as ModelValidationError
from django.db import IntegrityError
from django.middleware.csrf import get_token, rotate_token
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.cache import patch_vary_headers
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie
from rest_framework import status
from rest_framework.exceptions import AuthenticationFailed, ValidationError
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from . import otp, services, tokens
from .models import LoginSession, User
from .serializers import CodeInput, PasswordInput, PhoneInput, SessionSerializer, UserSerializer


def cookie_response(pair: tuple[str, str]) -> Response:
    response = Response({"detail": "Signed in."})
    for name, value, seconds in [("shop_access", pair[0], 900), ("shop_refresh", pair[1], 604800)]:
        response.set_cookie(
            name,
            value,
            max_age=seconds,
            httponly=True,
            secure=settings.AUTH_COOKIE_SECURE,
            samesite="Lax",
            path="/",
        )
    return response


class IdentityView(APIView):
    def finalize_response(self, request, response, *args, **kwargs):
        response = super().finalize_response(request, response, *args, **kwargs)
        response["Cache-Control"] = "private, no-store"
        patch_vary_headers(response, ["Cookie"])
        return response


@method_decorator(csrf_protect, name="dispatch")
class PublicAuthView(IdentityView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def get_authenticate_header(self, request):
        return "Cookie"

    def handle_exception(self, error):
        if isinstance(error, redis.RedisError):
            return Response({"detail": "Authentication service is unavailable."}, status=503)
        return super().handle_exception(error)


@method_decorator(ensure_csrf_cookie, name="dispatch")
class CsrfView(PublicAuthView):
    def get(self, request):
        return Response({"csrfToken": get_token(request)})


class RequestCodeView(PublicAuthView):
    def post(self, request):
        serializer = PhoneInput(data=request.data)
        serializer.is_valid(raise_exception=True)
        otp.request_code(serializer.validated_data["phone"], request.META["REMOTE_ADDR"])
        return Response({"detail": "Code sent.", "expiresIn": 120}, status=status.HTTP_202_ACCEPTED)


class VerifyCodeView(PublicAuthView):
    def post(self, request):
        serializer = CodeInput(data=request.data)
        serializer.is_valid(raise_exception=True)
        phone = serializer.validated_data["phone"]
        otp.verify_code(phone, serializer.validated_data["code"])
        user, _ = User.all_objects.get_or_create(phone=phone, defaults={"password": "!"})
        if not user.is_active or user.is_deleted:
            return Response({"detail": "Account is unavailable."}, status=403)
        rotate_token(request)
        return cookie_response(tokens.issue_session(user))


class PasswordLoginView(PublicAuthView):
    def post(self, request):
        serializer = PasswordInput(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        otp.limit_password_attempt(data["phone"], request.META["REMOTE_ADDR"])
        user = authenticate(request=request, phone=data["phone"], password=data["password"])
        if user is None:
            raise AuthenticationFailed("Invalid phone number or password.")
        rotate_token(request)
        return cookie_response(tokens.issue_session(user))


class RefreshView(PublicAuthView):
    def post(self, request):
        return cookie_response(tokens.rotate_session(request.COOKIES.get("shop_refresh", "")))


class LogoutView(PublicAuthView):
    def post(self, request):
        token = request.COOKIES.get("shop_refresh")
        if token:
            try:
                claims = tokens.decode(token, "refresh")
            except AuthenticationFailed:
                claims = None
            if claims:
                LoginSession.objects.filter(
                    pk=claims["sid"], user_id=claims["sub"], revoked_at__isnull=True
                ).update(revoked_at=timezone.now())
        response = Response(status=204)
        for name in ("shop_access", "shop_refresh"):
            response.delete_cookie(name, path="/", samesite="Lax")
        return response


class MeView(IdentityView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user).data)


class UserPagination(PageNumberPagination):
    page_size = 25


class UsersView(IdentityView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        users = services.inspect_users(request.user)
        if search := request.query_params.get("search", "")[:32]:
            users = users.filter(phone__icontains=search)
        paginator = UserPagination()
        return paginator.get_paginated_response(
            UserSerializer(paginator.paginate_queryset(users, request), many=True).data
        )

    def post(self, request):
        services.require_user_management(request.user, write=True)
        return self.save(request)

    def save(self, request, identifier=None):
        serializer = UserSerializer(data=request.data, partial=bool(identifier))
        serializer.is_valid(raise_exception=True)
        try:
            user = services.save_user(request.user, serializer.validated_data, identifier)
        except ModelValidationError as error:
            raise ValidationError(error.message_dict) from error
        except IntegrityError as error:
            raise ValidationError({"phone": "Phone number is already registered."}) from error
        return Response(UserSerializer(user).data, status=200 if identifier else 201)


class UserDetailView(UsersView):
    def get(self, request, identifier):
        user = get_object_or_404(services.inspect_users(request.user), pk=identifier)
        return Response(
            {
                "user": UserSerializer(user).data,
                "sessions": SessionSerializer(user.login_sessions.all()[:50], many=True).data,
            }
        )

    def post(self, request, identifier):
        return Response(status=405)

    def patch(self, request, identifier):
        services.require_user_management(request.user, write=True)
        get_object_or_404(User.all_objects, pk=identifier)
        return self.save(request, identifier)


class RevokeSessionView(IdentityView):
    permission_classes = [IsAuthenticated]

    def post(self, request, identifier):
        services.require_user_management(request.user, write=True)
        services.revoke_session(
            request.user, get_object_or_404(LoginSession.objects, pk=identifier)
        )
        return Response(status=204)
