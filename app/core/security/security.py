import typing as t
from datetime import datetime, timedelta, timezone

import jwt

from app.core.config import settings

ALGORITHM = "HS256"


def create_access_token(
    subject: int | str, expires_delta: timedelta | None = None
) -> str:
    expire = datetime.now(timezone.utc) + (
        expires_delta
        or timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    payload: dict[str, str | datetime] = {"sub": str(subject), "exp": expire}
    return jwt.encode(
        payload, settings.SECRET_KEY_FOR_JWT_AUTH, algorithm=ALGORITHM
    )


def decode_access_token(token: str) -> dict[str, t.Any]:
    return jwt.decode(
        token, settings.SECRET_KEY_FOR_JWT_AUTH, algorithms=[ALGORITHM]
    )


def create_verification_token(email: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        hours=settings.EMAIL_VERIFICATION_TOKEN_EXPIRE_HOURS
    )
    payload: dict[str, str | t.Any] = {
        "sub": email,
        "exp": expire,
        "type": "email_verification",
    }
    return jwt.encode(
        payload, settings.EMAIL_VERIFICATION_SECRET, algorithm=ALGORITHM
    )


def decode_verification_token(token: str) -> str:
    payload = jwt.decode(
        token, settings.EMAIL_VERIFICATION_SECRET, algorithms=[ALGORITHM]
    )
    if payload.get("type") != "email_verification":
        raise jwt.InvalidTokenError("Invalid token type")
    return payload["sub"]


def create_share_token(
    secret_id: int,
    owner_id: int,
    encryption_password: str,
    expires_minutes: int,
) -> str:
    payload: dict[str, t.Any] = {
        "sub": "share",
        "sid": secret_id,
        "oid": owner_id,
        "pwd": encryption_password,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=expires_minutes),
    }
    return jwt.encode(
        payload, settings.SECRET_KEY_FOR_JWT_AUTH, algorithm=ALGORITHM
    )


def decode_share_token(token: str) -> tuple[int, int, str]:
    payload = jwt.decode(
        token, settings.SECRET_KEY_FOR_JWT_AUTH, algorithms=[ALGORITHM]
    )
    if payload.get("sub") != "share":
        raise jwt.InvalidTokenError("Not a share token.")
    return int(payload["sid"]), int(payload["oid"]), payload["pwd"]
