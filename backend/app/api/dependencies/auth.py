"""Authentication dependencies."""

from collections.abc import Callable
from typing import Annotated

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.database.session import get_db
from app.models.identity import User
from app.services.identity import IdentityService


def current_user(
    db: Annotated[Session, Depends(get_db)],
    authorization: Annotated[str | None, Header()] = None,
) -> User:
    """Return the authenticated user from the bearer token."""
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )
    token = authorization.split(" ", 1)[1]
    payload = decode_access_token(token)
    if not payload or not isinstance(payload.get("sub"), str):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )
    user = IdentityService(db).get_user_by_id(payload["sub"])
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Inactive or unknown user",
        )
    return user


def require_permission(permission: str) -> Callable[..., User]:
    """Build a dependency requiring a specific permission."""

    def dependency(
        db: Annotated[Session, Depends(get_db)],
        user: Annotated[User, Depends(current_user)],
    ) -> User:
        service = IdentityService(db)
        if permission not in service.permission_codes(user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission required: {permission}",
            )
        return user

    return dependency


def require_admin(
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(current_user)],
) -> User:
    """Require platform administration permission."""
    service = IdentityService(db)
    permissions = set(service.permission_codes(user))
    if not {"connectors:admin", "settings:admin", "users:admin"}.issubset(permissions):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator role required",
        )
    return user
