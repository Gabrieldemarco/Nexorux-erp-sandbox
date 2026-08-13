import uuid
import pytest
from datetime import datetime, timedelta
from fastapi import HTTPException
from fastapi.responses import JSONResponse

from app.api.v1.endpoints.auth import authenticate_user, _is_locked, _record_failed_attempt, _clear_attempts
from app.models.user import User
from app.core.security import get_password_hash
from tests.conftest import FakeSession


@pytest.mark.asyncio
async def test_account_lockout_after_max_attempts(fake_db, fake_user, fake_tenant):
    identifier = fake_user.email
    _clear_attempts(identifier)
    for _ in range(5):
        user = await authenticate_user(fake_db, identifier, "wrong-password")
        assert user is None
    assert _is_locked(identifier)


@pytest.mark.asyncio
async def test_successful_login_clears_failed_attempts(fake_db, fake_user, fake_tenant):
    identifier = fake_user.email
    _clear_attempts(identifier)
    for _ in range(2):
        await authenticate_user(fake_db, identifier, "wrong-password")
    assert not _is_locked(identifier)
    user = await authenticate_user(fake_db, identifier, "secret123")
    assert user == fake_user
    assert not _is_locked(identifier)


@pytest.mark.asyncio
async def test_security_headers_middleware(monkeypatch):
    from app.core import config
    from app.main import SecurityHeadersMiddleware

    monkeypatch.setattr(config.settings, "DEBUG", False)
    middleware = SecurityHeadersMiddleware(app=None)

    class FakeRequest:
        pass

    class FakeResponse:
        def __init__(self):
            self.headers = {}

    async def call_next(request):
        return FakeResponse()

    request = FakeRequest()
    response = await middleware.dispatch(request, call_next)
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["X-XSS-Protection"] == "1; mode=block"
    assert "max-age=31536000" in response.headers["Strict-Transport-Security"]


@pytest.mark.asyncio
async def test_security_headers_skip_hsts_in_debug(monkeypatch):
    from app.core import config
    from app.main import SecurityHeadersMiddleware

    monkeypatch.setattr(config.settings, "DEBUG", True)
    middleware = SecurityHeadersMiddleware(app=None)

    class FakeResponse:
        def __init__(self):
            self.headers = {}

    async def call_next(request):
        return FakeResponse()

    response = await middleware.dispatch(object(), call_next)
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert "Strict-Transport-Security" not in response.headers


@pytest.mark.asyncio
async def test_rate_limiter_allows_under_threshold():
    from app.core.rate_limit import InMemoryRateLimiter
    limiter = InMemoryRateLimiter(app=None)

    class FakeRequest:
        class client:
            host = "127.0.0.1"

    request = FakeRequest()

    async def call_next(request):
        return JSONResponse(status_code=200, content={"ok": True})

    for _ in range(10):
        response = await limiter.dispatch(request, call_next)
        assert response.status_code == 200


@pytest.mark.asyncio
async def test_rate_limiter_blocks_over_threshold():
    from app.core.rate_limit import InMemoryRateLimiter
    limiter = InMemoryRateLimiter(app=None)

    class FakeRequest:
        class client:
            host = "192.168.1.100"

    request = FakeRequest()

    async def call_next(request):
        return JSONResponse(status_code=200, content={"ok": True})

    for _ in range(60):
        response = await limiter.dispatch(request, call_next)
        assert response.status_code == 200

    response = await limiter.dispatch(request, call_next)
    assert response.status_code == 429
