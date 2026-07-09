"""Authentication endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies.auth import current_user
from app.core.config.settings import Settings, get_settings
from app.database.session import get_db
from app.models.identity import User
from app.schemas.identity import LoginRequest, TokenResponse, UserResponse
from app.services.identity import IdentityService

router = APIRouter()


@router.post("/login", response_model=TokenResponse, summary="Login")
def login(
    payload: LoginRequest,
    db: Annotated[Session, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> TokenResponse:
    """Authenticate a user and return a bearer token."""
    service = IdentityService(db)
    user = service.authenticate(payload.username, payload.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )
    return TokenResponse(
        access_token=service.create_token(user),
        expires_in_minutes=settings.jwt_expire_minutes,
    )


@router.get("/me", response_model=UserResponse, summary="Current user")
def me(
    user: Annotated[User, Depends(current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> UserResponse:
    """Return the authenticated user profile."""
    service = IdentityService(db)
    return UserResponse(
        id=user.id,
        email=user.email,
        username=user.username,
        full_name=user.full_name,
        is_active=user.is_active,
        is_superuser=user.is_superuser,
        roles=service.role_names(user),
        groups=service.group_names(user),
        permissions=service.permission_codes(user),
    )
