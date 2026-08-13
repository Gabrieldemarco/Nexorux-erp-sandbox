"""Unit tests for optional SMTP / outbox helpers (no network)."""

from pathlib import Path

import pytest

from app.services.email import email_delivery_ready, send_password_reset_email, smtp_ready


def test_smtp_ready_false_by_default(monkeypatch):
    from app.core import config

    monkeypatch.setattr(config.settings, "EMAIL_BACKEND", "smtp")
    monkeypatch.setattr(config.settings, "SMTP_ENABLED", False)
    monkeypatch.setattr(config.settings, "SMTP_HOST", None)
    assert smtp_ready() is False
    assert email_delivery_ready() is False


def test_smtp_ready_requires_host(monkeypatch):
    from app.core import config

    monkeypatch.setattr(config.settings, "EMAIL_BACKEND", "smtp")
    monkeypatch.setattr(config.settings, "SMTP_ENABLED", True)
    monkeypatch.setattr(config.settings, "SMTP_HOST", None)
    assert smtp_ready() is False

    monkeypatch.setattr(config.settings, "SMTP_HOST", "smtp.example.com")
    assert smtp_ready() is True


def test_outbox_backend_always_ready(monkeypatch):
    from app.core import config

    monkeypatch.setattr(config.settings, "EMAIL_BACKEND", "outbox")
    monkeypatch.setattr(config.settings, "SMTP_ENABLED", False)
    assert email_delivery_ready() is True


@pytest.mark.asyncio
async def test_send_password_reset_writes_outbox(monkeypatch, tmp_path: Path):
    from app.core import config

    monkeypatch.setattr(config.settings, "EMAIL_BACKEND", "outbox")
    monkeypatch.setattr(config.settings, "STORAGE_PATH", str(tmp_path))
    monkeypatch.setattr(
        config.settings, "PASSWORD_RESET_URL_BASE", "http://localhost:3000/recover-password"
    )

    ok = await send_password_reset_email(
        to_email="user@example.com", reset_token="tok_" + ("a" * 40)
    )
    assert ok is True
    files = list((tmp_path / "mail_outbox").glob("*.txt"))
    assert len(files) == 1
    text = files[0].read_text(encoding="utf-8")
    assert "tok_" in text
    assert "user@example.com" in text
