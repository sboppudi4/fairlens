"""Auth business logic. Thin wrapper over models + security primitives."""
from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import http_400, http_401, http_404
from app.core.security import create_access_token, hash_password, verify_password
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
    token = create_access_token(user.id)
    return TokenResponse(access_token=token, user=UserOut.model_validate(user))


async def login_user(db: AsyncSession, data: UserLogin) -> TokenResponse:
    user = await db.scalar(select(User).where(User.email == data.email.lower()))
    if user is None or not verify_password(data.password, user.hashed_password):
        raise http_401("invalid email or password")
    if not user.is_active:
        raise http_401("account is disabled")
    token = create_access_token(user.id)
    return TokenResponse(access_token=token, user=UserOut.model_validate(user))


async def get_user_by_id(db: AsyncSession, user_id: UUID) -> User:
    user = await db.get(User, user_id)
    if user is None:
        raise http_404("user not found")
    return user
