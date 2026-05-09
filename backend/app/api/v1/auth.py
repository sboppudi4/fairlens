from fastapi import APIRouter, Response, status

from app.config import get_settings
from app.dependencies import CurrentUser, DBSession
from app.schemas.user import (
    RefreshRequest,
    TokenResponse,
    UserCreate,
    UserLogin,
    UserOut,
    UserUpdate,
)
from app.services.auth_service import login_user, refresh_access, register_user

router = APIRouter(prefix="/auth", tags=["auth"])

# Cookie names — kept identical for access and refresh tokens to make middleware simple.
ACCESS_COOKIE = "fl_access"
REFRESH_COOKIE = "fl_refresh"


def _set_auth_cookies(response: Response, access: str, refresh: str | None) -> None:
    """Write JWTs to httpOnly Secure cookies. Browsers will send them automatically."""
    settings = get_settings()
    secure = settings.ENVIRONMENT == "production"
    samesite = "lax"
    response.set_cookie(
        ACCESS_COOKIE,
        access,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        httponly=True,
        secure=secure,
        samesite=samesite,
        path="/",
    )
    if refresh:
        response.set_cookie(
            REFRESH_COOKIE,
            refresh,
            max_age=30 * 24 * 60 * 60,
            httponly=True,
            secure=secure,
            samesite=samesite,
            path="/",
        )


def _clear_auth_cookies(response: Response) -> None:
    response.delete_cookie(ACCESS_COOKIE, path="/")
    response.delete_cookie(REFRESH_COOKIE, path="/")


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(payload: UserCreate, db: DBSession, response: Response) -> TokenResponse:
    """Create a new account, set httpOnly cookies, and return a Bearer token for API clients."""
    tokens = await register_user(db, payload)
    _set_auth_cookies(response, tokens.access_token, tokens.refresh_token)
    return tokens


@router.post("/login", response_model=TokenResponse)
async def login(payload: UserLogin, db: DBSession, response: Response) -> TokenResponse:
    """Exchange email + password for an access + refresh token pair (also set as cookies)."""
    tokens = await login_user(db, payload)
    _set_auth_cookies(response, tokens.access_token, tokens.refresh_token)
    return tokens


@router.post("/refresh", response_model=TokenResponse)
async def refresh(payload: RefreshRequest, db: DBSession, response: Response) -> TokenResponse:
    """Exchange a refresh token for a fresh access + refresh pair."""
    tokens = await refresh_access(db, payload.refresh_token)
    _set_auth_cookies(response, tokens.access_token, tokens.refresh_token)
    return tokens


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(response: Response) -> None:
    """Clear auth cookies. Stateless on the server (no refresh-token revocation list yet)."""
    _clear_auth_cookies(response)


@router.get("/me", response_model=UserOut)
async def me(user: CurrentUser) -> UserOut:
    """Return the authenticated user."""
    return UserOut.model_validate(user)


@router.put("/me", response_model=UserOut)
async def update_me(payload: UserUpdate, user: CurrentUser, db: DBSession) -> UserOut:
    """Update the authenticated user's profile."""
    if payload.full_name is not None:
        user.full_name = payload.full_name
    await db.commit()
    await db.refresh(user)
    return UserOut.model_validate(user)
