from typing import List, Optional, Sequence

from fastapi import Depends, HTTPException, status

from app.core.permissions import PERMISSION_ALL
from app.models.permission import Permission
from app.models.role import Role
from app.models.user import User
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db


from app.core.auth import get_current_user


async def get_current_user_with_permissions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Return the current user with roles and permissions loaded."""
    if hasattr(current_user, "permission_codes") and current_user.permission_codes is not None:
        if not hasattr(current_user, "role_keys") or current_user.role_keys is None:
            roles = getattr(current_user, "roles", None) or []
            current_user.role_keys = [role.key for role in roles]
        return current_user

    stmt = select(User).where(User.id == current_user.id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    roles_stmt = select(Role).join(Role.users).where(User.id == user.id)
    roles_result = await db.execute(roles_stmt)
    roles = roles_result.scalars().all()
    user.role_keys = [role.key for role in roles]

    permissions_stmt = (
        select(Permission.code)
        .join(Permission.roles)
        .join(Role.users)
        .where(User.id == user.id)
        .distinct()
    )
    permissions_result = await db.execute(permissions_stmt)
    user.permission_codes = [row[0] for row in permissions_result.all()]

    return user


def _has_permission(user: User, permission_code: str) -> bool:
    user_permissions = getattr(user, "permission_codes", [])
    if PERMISSION_ALL in user_permissions:
        return True
    return permission_code in user_permissions


def require_permissions(*permission_codes: str):
    """Dependency factory: require the current user to have ALL specified permissions."""
    async def dependency(current_user: User = Depends(get_current_user_with_permissions)) -> User:
        missing = [code for code in permission_codes if not _has_permission(current_user, code)]
        if missing:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing permissions: {', '.join(missing)}",
            )
        return current_user
    return dependency


def require_any_permission(*permission_codes: str):
    """Dependency factory: require the current user to have AT LEAST ONE of the specified permissions."""
    async def dependency(current_user: User = Depends(get_current_user_with_permissions)) -> User:
        if not any(_has_permission(current_user, code) for code in permission_codes):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing any of permissions: {', '.join(permission_codes)}",
            )
        return current_user
    return dependency


def require_role(*role_keys: str):
    """Dependency factory: require the current user to have AT LEAST ONE of the specified roles."""
    async def dependency(current_user: User = Depends(get_current_user_with_permissions)) -> User:
        user_roles = getattr(current_user, "role_keys", None)
        if user_roles is None:
            roles = getattr(current_user, "roles", None) or []
            user_roles = [getattr(role, "key", role) for role in roles]
        if not any(key in user_roles for key in role_keys):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing any of roles: {', '.join(role_keys)}",
            )
        return current_user
    return dependency
