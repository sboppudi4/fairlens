"""FastAPI dependency injection: DB session, current user.

Auth resolution order (most specific first):
1. ``Authorization: Bearer <token>`` header (preferred for API clients).
2. ``fl_access`` httpOnly cookie (preferred for browser clients).
"""
from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import Cookie, Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import http_401
from app.core.security import decode_token
from app.models.user import User
from app.services.auth_service import get_user_by_id


async def get_current_user(
    db: Annotated[AsyncSession, Depends(get_db)],
    authorization: Annotated[str | None, Header()] = None,
    fl_access: Annotated[str | None, Cookie()] = None,
) -> User:
    token: str | None = None
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1].strip()
    elif fl_access:
        token = fl_access

    if not token:
        raise http_401("missing access token")

    try:
        payload = decode_token(token, expected_type="access")
    except ValueError as e:
        raise http_401("invalid or expired token") from e

    sub = payload.get("sub")
    if not sub:
        raise http_401("invalid token payload")
    try:
        user_id = UUID(sub)
    except ValueError as e:
        raise http_401("invalid token subject") from e
    return await get_user_by_id(db, user_id)


CurrentUser = Annotated[User, Depends(get_current_user)]
DBSession = Annotated[AsyncSession, Depends(get_db)]
