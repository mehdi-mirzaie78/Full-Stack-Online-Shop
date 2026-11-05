import hashlib
import secrets
from datetime import timedelta
from uuid import UUID

import jwt
from django.conf import settings
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import AuthenticationFailed

from .models import LoginSession, User


def digest(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def encode(session: LoginSession, kind: str, nonce: str) -> str:
    now = timezone.now()
    expiry = (
        min(session.expires_at, now + timedelta(minutes=15))
        if kind == "access"
        else session.expires_at
    )
    return jwt.encode(
        {
            "sub": str(session.user_id),
            "sid": str(session.pk),
            "type": kind,
            "jti": nonce,
            "iat": now,
            "exp": expiry,
            "iss": "shop-identity",
            "aud": "shop",
        },
        settings.JWT_SECRET_KEY,
        algorithm="HS256",
    )


def decode(token: str, kind: str) -> dict:
    try:
        claims = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=["HS256"],
            issuer="shop-identity",
            audience="shop",
            options={"require": ["sub", "sid", "type", "jti", "iat", "exp"]},
        )
        UUID(claims["sub"])
        UUID(claims["sid"])
        if not isinstance(claims["jti"], str) or not claims["jti"]:
            raise AuthenticationFailed("Invalid session.")
        if claims["type"] != kind:
            raise AuthenticationFailed("Invalid session.")
        return claims
    except (jwt.InvalidTokenError, ValueError, TypeError) as error:
        raise AuthenticationFailed("Invalid or expired session.") from error


def issue_session(user: User) -> tuple[str, str]:
    nonce = secrets.token_hex(32)
    session = LoginSession.objects.create(
        user=user, refresh_digest=digest(nonce), expires_at=timezone.now() + timedelta(days=7)
    )
    return encode(session, "access", secrets.token_hex(16)), encode(session, "refresh", nonce)


def rotate_session(token: str) -> tuple[str, str]:
    claims = decode(token, "refresh")
    invalid = False
    with transaction.atomic():
        session = (
            LoginSession.objects.select_for_update(of=("self",))
            .filter(
                pk=claims["sid"],
                user_id=claims["sub"],
                revoked_at__isnull=True,
                is_active=True,
                expires_at__gt=timezone.now(),
                user__is_active=True,
                user__is_deleted=False,
            )
            .first()
        )
        if session is None:
            raise AuthenticationFailed("Invalid session.")
        if not secrets.compare_digest(session.refresh_digest, digest(claims["jti"])):
            session.revoked_at = timezone.now()
            invalid = True
        else:
            nonce = secrets.token_hex(32)
            session.refresh_digest = digest(nonce)
        session.save(update_fields=["refresh_digest", "revoked_at", "updated_at"])
    # Commit revocation before raising; rolling it back would permit replay.
    if invalid:
        raise AuthenticationFailed("Refresh token replay detected. Sign in again.")
    return encode(session, "access", secrets.token_hex(16)), encode(session, "refresh", nonce)
