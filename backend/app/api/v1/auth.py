from fastapi import APIRouter, status

from app.dependencies import CurrentUser, DBSession
from app.schemas.user import TokenResponse, UserCreate, UserLogin, UserOut, UserUpdate
from app.services.auth_service import login_user, register_user

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(payload: UserCreate, db: DBSession) -> TokenResponse:
    """Create a new account and return an access token."""
    return await register_user(db, payload)


@router.post("/login", response_model=TokenResponse)
async def login(payload: UserLogin, db: DBSession) -> TokenResponse:
    """Exchange email + password for an access token."""
    return await login_user(db, payload)


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
