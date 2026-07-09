"""Identity and access-management schemas."""

from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class LoginRequest(BaseModel):
    """Login request body."""

    username: str = Field(min_length=1, max_length=255)
    password: str = Field(min_length=1, max_length=255)


class TokenResponse(BaseModel):
    """Bearer token response."""

    access_token: str
    token_type: str = "bearer"
    expires_in_minutes: int


class PermissionResponse(BaseModel):
    """Permission response."""

    model_config = ConfigDict(from_attributes=True)

    code: str
    description: str
    category: str


class RoleResponse(BaseModel):
    """Role response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    description: str
    is_system: bool


class GroupResponse(BaseModel):
    """Group response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    description: str
    is_system: bool


class UserResponse(BaseModel):
    """Authenticated user response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: str
    username: str
    full_name: str | None
    is_active: bool
    is_superuser: bool
    roles: list[str]
    groups: list[str]
    permissions: list[str]


class RbacSummaryResponse(BaseModel):
    """RBAC administration summary."""

    users: list[UserResponse]
    roles: list[RoleResponse]
    groups: list[GroupResponse]
    permissions: list[PermissionResponse]
