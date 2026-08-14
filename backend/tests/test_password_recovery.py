"""Password recovery: registered email → deliver token → reset password."""

from pathlib import Path

import pytest
from fastapi import HTTPException

from app.api.v1.endpoints.auth import request_password_reset, reset_password
from app.core.config import settings
from app.core.security import verify_password
from app.schemas.user import PasswordRecoveryRequest, PasswordResetRequest


@pytest.mark.asyncio
async def test_forgot_requires_registered_email(fake_db):
    with pytest.raises(HTTPException) as exc:
        await request_password_reset(
            PasswordRecoveryRequest(email="nobody@example.com"),
            fake_db,
        )
    assert exc.value.status_code == 404
    assert "registrada" in exc.value.detail.lower()


@pytest.mark.asyncio
async def test_forgot_rejects_missing_email():
    with pytest.raises(HTTPException) as exc:
        await request_password_reset(
            PasswordRecoveryRequest(email=None),
            None,  # type: ignore[arg-type]
        )
    assert exc.value.status_code == 422


@pytest.mark.asyncio
async def test_forgot_sends_token_then_reset(fake_db, fake_user, monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "EMAIL_BACKEND", "outbox")
    monkeypatch.setattr(settings, "SMTP_ENABLED", False)
    monkeypatch.setattr(settings, "DEBUG", True)
    monkeypatch.setattr(settings, "STORAGE_PATH", str(tmp_path))
    monkeypatch.setattr(
        settings, "PASSWORD_RESET_URL_BASE", "http://localhost:3000/recover-password"
    )

    result = await request_password_reset(
        PasswordRecoveryRequest(email="existing@example.com"),
        fake_db,
    )
    assert "existing@example.com" in result["message"]
    assert result.get("reset_token") is None

    outbox = Path(tmp_path) / "mail_outbox"
    files = list(outbox.glob("*.txt"))
    assert len(files) == 1
    mail_text = files[0].read_text(encoding="utf-8")

    token = None
    lines = mail_text.splitlines()
    for i, line in enumerate(lines):
        if "token" in line.lower() and i + 1 < len(lines):
            candidate = lines[i + 1].strip()
            if len(candidate) >= 16 and " " not in candidate:
                token = candidate
                break
    if token is None:
        token = max(
            (
                ln.strip()
                for ln in lines
                if len(ln.strip()) >= 32 and " " not in ln.strip() and "://" not in ln
            ),
            default=None,
        )
    assert token, f"token not found in outbox mail:\n{mail_text}"

    reset = await reset_password(
        PasswordResetRequest(token=token, new_password="newpassword1"),
        fake_db,
    )
    assert "actualizada" in reset["message"].lower()
    assert verify_password("newpassword1", fake_user.password_hash)
    assert fake_user.password_reset_token_hash is None
