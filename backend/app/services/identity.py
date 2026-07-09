"""Identity and RBAC services."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.config.settings import Settings
from app.core.security import create_access_token, hash_password, verify_password
from app.models.identity import Group, Permission, Role, User

PERMISSIONS: dict[str, tuple[str, str]] = {
    "dashboard:read": ("dashboard", "View dashboard and operational metrics."),
    "events:read": ("events", "View normalized events."),
    "events:sync": ("events", "Trigger connector synchronization."),
    "reports:read": ("reports", "View reports."),
    "reports:export": ("reports", "Export reports."),
    "reports:push_discord": ("reports", "Push reports to Discord."),
    "connectors:admin": ("connectors", "View and manage connector configuration."),
    "settings:admin": ("settings", "View and manage platform settings."),
    "users:admin": ("identity", "Manage users, groups, roles, and permissions."),
    "audit:read": ("identity", "View security audit information."),
}

ROLE_PERMISSIONS: dict[str, list[str]] = {
    "viewer": ["dashboard:read", "events:read", "reports:read", "reports:export"],
    "operator": [
        "dashboard:read",
        "events:read",
        "events:sync",
        "reports:read",
        "reports:export",
        "reports:push_discord",
    ],
    "admin": list(PERMISSIONS.keys()),
}

ROLE_DESCRIPTIONS = {
    "viewer": "Read-only operational visibility.",
    "operator": "Daily operations without connector or settings administration.",
    "admin": "Full platform administration.",
}


class IdentityService:
    """Manage users, groups, roles, and permissions."""

    def __init__(self, db: Session) -> None:
        self._db = db

    def bootstrap(self, settings: Settings) -> None:
        """Create baseline RBAC objects and the bootstrap admin user."""
        permissions = self._bootstrap_permissions()
        roles = self._bootstrap_roles(permissions)
        admin_group = self._get_or_create_group(
            name="Administrators",
            description="System administrators with full platform access.",
            is_system=True,
        )
        if roles["admin"] not in admin_group.roles:
            admin_group.roles.append(roles["admin"])

        admin_user = self._db.scalar(
            select(User).where(
                or_(
                    User.email == settings.bootstrap_admin_email,
                    User.username == settings.bootstrap_admin_username,
                )
            )
        )
        if not admin_user:
            admin_user = User(
                email=settings.bootstrap_admin_email,
                username=settings.bootstrap_admin_username,
                full_name="AlertHub Administrator",
                password_hash=hash_password(settings.bootstrap_admin_password),
                is_active=True,
                is_superuser=True,
            )
            self._db.add(admin_user)
        elif not verify_password(settings.bootstrap_admin_password, admin_user.password_hash):
            admin_user.password_hash = hash_password(settings.bootstrap_admin_password)
        if roles["admin"] not in admin_user.roles:
            admin_user.roles.append(roles["admin"])
        if admin_group not in admin_user.groups:
            admin_user.groups.append(admin_group)
        self._db.commit()

    def authenticate(self, username: str, password: str) -> User | None:
        """Authenticate a user by username or email."""
        user = self._db.scalar(
            select(User).where(or_(User.username == username, User.email == username))
        )
        if not user or not user.is_active:
            return None
        if not verify_password(password, user.password_hash):
            return None
        user.last_login_at = datetime.now(UTC)
        self._db.commit()
        self._db.refresh(user)
        return user

    def create_token(self, user: User) -> str:
        """Create a bearer token for a user."""
        return create_access_token(
            subject=str(user.id),
            roles=self.role_names(user),
            permissions=self.permission_codes(user),
        )

    def get_user_by_id(self, user_id: str) -> User | None:
        """Return a user by UUID string."""
        return self._db.get(User, user_id)

    def role_names(self, user: User) -> list[str]:
        """Return direct and group role names."""
        return sorted({role.name for role in self._effective_roles(user)})

    def group_names(self, user: User) -> list[str]:
        """Return group names."""
        return sorted(group.name for group in user.groups)

    def permission_codes(self, user: User) -> list[str]:
        """Return all effective permission codes."""
        if user.is_superuser:
            return sorted(PERMISSIONS)
        permissions = {
            permission.code
            for role in self._effective_roles(user)
            for permission in role.permissions
        }
        return sorted(permissions)

    def users(self) -> list[User]:
        """Return all users."""
        return list(self._db.scalars(select(User).order_by(User.username)).all())

    def roles(self) -> list[Role]:
        """Return all roles."""
        return list(self._db.scalars(select(Role).order_by(Role.name)).all())

    def groups(self) -> list[Group]:
        """Return all groups."""
        return list(self._db.scalars(select(Group).order_by(Group.name)).all())

    def permissions(self) -> list[Permission]:
        """Return all permissions."""
        return list(self._db.scalars(select(Permission).order_by(Permission.code)).all())

    def _bootstrap_permissions(self) -> dict[str, Permission]:
        permissions: dict[str, Permission] = {}
        for code, (category, description) in PERMISSIONS.items():
            permission = self._db.scalar(select(Permission).where(Permission.code == code))
            if not permission:
                permission = Permission(code=code, category=category, description=description)
                self._db.add(permission)
            permissions[code] = permission
        return permissions

    def _bootstrap_roles(self, permissions: dict[str, Permission]) -> dict[str, Role]:
        roles: dict[str, Role] = {}
        for name, permission_codes in ROLE_PERMISSIONS.items():
            role = self._db.scalar(select(Role).where(Role.name == name))
            if not role:
                role = Role(
                    name=name,
                    description=ROLE_DESCRIPTIONS[name],
                    is_system=True,
                )
                self._db.add(role)
            for permission_code in permission_codes:
                permission = permissions[permission_code]
                if permission not in role.permissions:
                    role.permissions.append(permission)
            roles[name] = role
        return roles

    def _get_or_create_group(self, name: str, description: str, is_system: bool) -> Group:
        group = self._db.scalar(select(Group).where(Group.name == name))
        if group:
            return group
        group = Group(name=name, description=description, is_system=is_system)
        self._db.add(group)
        return group

    @staticmethod
    def _effective_roles(user: User) -> list[Role]:
        roles = {role.name: role for role in user.roles}
        for group in user.groups:
            for role in group.roles:
                roles.setdefault(role.name, role)
        return list(roles.values())
