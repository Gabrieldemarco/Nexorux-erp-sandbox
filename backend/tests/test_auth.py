import pytest
import uuid
from fastapi import HTTPException
from app.api.v1.endpoints.auth import (
    authenticate_user,
    create_access_token,
    create_refresh_token,
    decode_token,
    get_current_user,
    register_user,
    get_user_by_email,
    get_user_by_username,
)
from app.core.security import get_password_hash
from app.models.user import User
from app.schemas.user import UserCreate


@pytest.mark.asyncio
async def test_get_user_by_email(fake_db, fake_user):
    user = await get_user_by_email(fake_db, "existing@example.com")
    assert user is not None
    assert user.email == "existing@example.com"


@pytest.mark.asyncio
async def test_get_user_by_username(fake_db, fake_user):
    user = await get_user_by_username(fake_db, "existing_user")
    assert user is not None
    assert user.username == "existing_user"


@pytest.mark.asyncio
async def test_authenticate_user_success(fake_db, fake_user):
    user = await authenticate_user(fake_db, "existing@example.com", "secret123")
    assert user is not None
    assert user.email == "existing@example.com"


@pytest.mark.asyncio
async def test_authenticate_user_failure(fake_db):
    user = await authenticate_user(fake_db, "missing@example.com", "secret123")
    assert user is None


def test_create_and_verify_tokens():
    data = {"sub": str(uuid.uuid4()), "email": "test@example.com", "type": "access"}
    access_token = create_access_token(data)
    refresh_token = create_refresh_token({"sub": data["sub"], "email": data["email"]})

    assert access_token is not None
    assert refresh_token is not None

    payload = decode_token(access_token)
    assert payload is not None
    assert payload["sub"] == data["sub"]
    assert payload["type"] == "access"

    refresh_payload = decode_token(refresh_token)
    assert refresh_payload is not None
    assert refresh_payload["type"] == "refresh"


@pytest.mark.asyncio
async def test_register_user_success(fake_db, fake_tenant, fake_company):
    user_data = UserCreate(
        email="newuser@example.com",
        username="new_user",
        full_name="New User",
        password="password123",
        tenant_id=str(fake_tenant.id),
        company_id=str(fake_company.id),
    )

    user = await register_user(user_data, fake_db)
    assert user is not None
    assert user.email == "newuser@example.com"
    assert user.username == "new_user"
    assert user.tenant_id == fake_tenant.id
    assert user.company_id == fake_company.id


@pytest.mark.asyncio
async def test_register_user_duplicate_email(fake_db, fake_tenant, fake_company):
    user_data = UserCreate(
        email="existing@example.com",
        username="new_user2",
        full_name="New User 2",
        password="password123",
        tenant_id=str(fake_tenant.id),
        company_id=str(fake_company.id),
    )

    with pytest.raises(HTTPException) as excinfo:
        await register_user(user_data, fake_db)

    assert excinfo.value.status_code == 400
    assert "email" in excinfo.value.detail


@pytest.mark.asyncio
async def test_register_user_invalid_company(fake_db, fake_tenant):
    user_data = UserCreate(
        email="another@example.com",
        username="another_user",
        full_name="Another User",
        password="password123",
        tenant_id=str(fake_tenant.id),
        company_id=str(uuid.uuid4()),
    )

    with pytest.raises(HTTPException) as excinfo:
        await register_user(user_data, fake_db)

    assert excinfo.value.status_code == 400
    assert "Company does not exist" in excinfo.value.detail


@pytest.mark.asyncio
async def test_get_current_user_token_invalid(fake_db):
    from app.core.security import create_access_token

    token = create_access_token({"sub": "invalid-uuid", "email": "x@example.com", "type": "access"})

    with pytest.raises(HTTPException):
        await get_current_user(token=token, db=fake_db)
