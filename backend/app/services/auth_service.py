"""Auth business logic. Thin wrapper over models + security primitives."""
from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import http_400, http_401, http_404
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models.user import User
from app.schemas.user import TokenResponse, UserCreate, UserLogin, UserOut


async def register_user(db: AsyncSession, data: UserCreate) -> TokenResponse:
    existing = await db.scalar(select(User).where(User.email == data.email.lower()))
    if existing is not None:
        raise http_400("email already registered")
    user = User(
        email=data.email.lower(),
        hashed_password=hash_password(data.password),
        full_name=data.full_name,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return _token_response(user)


async def login_user(db: AsyncSession, data: UserLogin) -> TokenResponse:
    user = await db.scalar(select(User).where(User.email == data.email.lower()))
    if user is None or not verify_password(data.password, user.hashed_password):
        raise http_401("invalid email or password")
    if not user.is_active:
        raise http_401("account is disabled")
    return _token_response(user)


async def refresh_access(db: AsyncSession, refresh_token: str) -> TokenResponse:
    """Validate the refresh token and issue a fresh access + refresh pair."""
    try:
        payload = decode_token(refresh_token, expected_type="refresh")
    except ValueError as e:
        raise http_401("invalid or expired refresh token") from e
    sub = payload.get("sub")
    if not sub:
        raise http_401("invalid refresh token payload")
    try:
        user_id = UUID(sub)
    except ValueError as e:
        raise http_401("invalid token subject") from e
    user = await db.get(User, user_id)
    if user is None:
        raise http_401("user no longer exists")
    if not user.is_active:
        raise http_401("account is disabled")
    return _token_response(user)


async def get_user_by_id(db: AsyncSession, user_id: UUID) -> User:
    user = await db.get(User, user_id)
    if user is None:
        raise http_404("user not found")
    return user


def _token_response(user: User) -> TokenResponse:
    return TokenResponse(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
        user=UserOut.model_validate(user),
    )
