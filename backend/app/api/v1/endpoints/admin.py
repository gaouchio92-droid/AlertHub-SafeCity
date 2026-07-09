"""Administration endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies.auth import require_admin
from app.database.session import get_db
from app.models.identity import User
from app.schemas.identity import (
    GroupResponse,
    PermissionResponse,
    RbacSummaryResponse,
    RoleResponse,
    UserResponse,
)
from app.services.identity import IdentityService

router = APIRouter(dependencies=[Depends(require_admin)])


@router.get("/rbac", response_model=RbacSummaryResponse, summary="RBAC summary")
def rbac_summary(
    db: Annotated[Session, Depends(get_db)],
    _admin: Annotated[User, Depends(require_admin)],
) -> RbacSummaryResponse:
    """Return users, groups, roles, and permissions."""
    service = IdentityService(db)
    return RbacSummaryResponse(
        users=[
            UserResponse(
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
            for user in service.users()
        ],
        roles=[RoleResponse.model_validate(role) for role in service.roles()],
        groups=[GroupResponse.model_validate(group) for group in service.groups()],
        permissions=[
            PermissionResponse.model_validate(permission)
            for permission in service.permissions()
        ],
    )
