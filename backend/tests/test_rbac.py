import uuid
import pytest
from fastapi import HTTPException

from app.core.permissions import PERMISSION_ALL, PERMISSION_PRODUCTS_READ, PERMISSION_PRODUCTS_CREATE
from app.core.rbac import require_permissions, require_any_permission, require_role
from app.models.role import Role
from app.models.permission import Permission
from app.models.user import User
from app.core.security import get_password_hash
from tests.conftest import FakeSession


@pytest.mark.asyncio
async def test_require_permissions_allows_when_permission_present(fake_user):
    fake_user.permission_codes = [PERMISSION_PRODUCTS_READ, PERMISSION_PRODUCTS_CREATE]
    dependency = require_permissions(PERMISSION_PRODUCTS_READ, PERMISSION_PRODUCTS_CREATE)
    result = await dependency(fake_user)
    assert result == fake_user


@pytest.mark.asyncio
async def test_require_permissions_denies_when_missing(fake_user):
    fake_user.permission_codes = [PERMISSION_PRODUCTS_READ]
    dependency = require_permissions(PERMISSION_PRODUCTS_READ, PERMISSION_PRODUCTS_CREATE)
    with pytest.raises(HTTPException) as exc_info:
        await dependency(fake_user)
    assert exc_info.value.status_code == 403
    assert "Missing permissions" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_require_permissions_allows_all_wildcard(fake_user):
    fake_user.permission_codes = [PERMISSION_ALL]
    dependency = require_permissions("anything.here")
    result = await dependency(fake_user)
    assert result == fake_user


@pytest.mark.asyncio
async def test_require_any_permission_allows_one(fake_user):
    fake_user.permission_codes = [PERMISSION_PRODUCTS_READ]
    dependency = require_any_permission(PERMISSION_PRODUCTS_READ, PERMISSION_PRODUCTS_CREATE)
    result = await dependency(fake_user)
    assert result == fake_user


@pytest.mark.asyncio
async def test_require_any_permission_denies_when_none(fake_user):
    fake_user.permission_codes = []
    dependency = require_any_permission(PERMISSION_PRODUCTS_READ, PERMISSION_PRODUCTS_CREATE)
    with pytest.raises(HTTPException) as exc_info:
        await dependency(fake_user)
    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_require_role_allows_when_role_present(fake_user):
    fake_user.roles = [Role(key="admin")]
    dependency = require_role("admin", "superadmin")
    result = await dependency(fake_user)
    assert result == fake_user


@pytest.mark.asyncio
async def test_require_role_denies_when_missing(fake_user):
    fake_user.roles = []
    dependency = require_role("admin", "superadmin")
    with pytest.raises(HTTPException) as exc_info:
        await dependency(fake_user)
    assert exc_info.value.status_code == 403
