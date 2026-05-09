from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import get_settings

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)
_settings = get_settings()


def hash_password(password: str) -> str:
    return _pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return _pwd_context.verify(plain, hashed)


def create_access_token(subject: str | UUID, expires_minutes: int | None = None) -> str:
    expire = datetime.now(UTC) + timedelta(
        minutes=expires_minutes or _settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    payload: dict[str, Any] = {
        "sub": str(subject),
        "exp": expire,
        "iat": datetime.now(UTC),
        "type": "access",
    }
    return jwt.encode(payload, _settings.SECRET_KEY, algorithm=_settings.ALGORITHM)


def create_refresh_token(subject: str | UUID, expires_days: int = 30) -> str:
    expire = datetime.now(UTC) + timedelta(days=expires_days)
    payload: dict[str, Any] = {
        "sub": str(subject),
        "exp": expire,
        "iat": datetime.now(UTC),
        "type": "refresh",
    }
    return jwt.encode(payload, _settings.SECRET_KEY, algorithm=_settings.ALGORITHM)


def decode_token(token: str, *, expected_type: str | None = None) -> dict[str, Any]:
    try:
        payload = jwt.decode(token, _settings.SECRET_KEY, algorithms=[_settings.ALGORITHM])
    except JWTError as e:
        raise ValueError("invalid token") from e
    if expected_type and payload.get("type") != expected_type:
        raise ValueError(f"expected token of type {expected_type}, got {payload.get('type')}")
    return payload
