"""Outbound email helpers (SMTP + local outbox for development)."""

from __future__ import annotations

import asyncio
import smtplib
import ssl
from datetime import datetime, timezone
from email.message import EmailMessage
from pathlib import Path

import structlog

from app.core.config import settings

logger = structlog.get_logger(__name__)


def _build_message(*, to_email: str, subject: str, body: str) -> EmailMessage:
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = settings.SMTP_FROM or settings.SMTP_USER or "noreply@nexorux.local"
    msg["To"] = to_email
    msg.set_content(body)
    return msg


def _send_outbox(*, to_email: str, subject: str, body: str) -> Path:
    """Write message to storage/mail_outbox (dev fallback / EMAIL_BACKEND=outbox)."""
    base = Path(settings.STORAGE_PATH or "./storage")
    outbox = base / "mail_outbox"
    outbox.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_%f")
    path = outbox / f"{stamp}_{to_email.replace('@', '_at_')}.txt"
    content = (
        f"To: {to_email}\n"
        f"From: {settings.SMTP_FROM or settings.SMTP_USER or 'noreply@nexorux.local'}\n"
        f"Subject: {subject}\n"
        f"Date: {stamp}\n"
        f"\n{body}\n"
    )
    path.write_text(content, encoding="utf-8")
    logger.info("smtp_outbox_written", path=str(path), to=to_email, subject=subject)
    return path


def _send_sync(*, to_email: str, subject: str, body: str) -> None:
    if (settings.EMAIL_BACKEND or "smtp").lower() == "outbox":
        _send_outbox(to_email=to_email, subject=subject, body=body)
        return

    if not settings.SMTP_HOST:
        raise RuntimeError("SMTP_HOST is not configured")

    msg = _build_message(to_email=to_email, subject=subject, body=body)
    host = settings.SMTP_HOST
    port = settings.SMTP_PORT

    if settings.SMTP_USE_SSL:
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(host, port, timeout=20, context=context) as smtp:
            if settings.SMTP_USER and settings.SMTP_PASSWORD:
                smtp.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            smtp.send_message(msg)
        return

    with smtplib.SMTP(host, port, timeout=20) as smtp:
        smtp.ehlo()
        if settings.SMTP_USE_TLS:
            smtp.starttls(context=ssl.create_default_context())
            smtp.ehlo()
        if settings.SMTP_USER and settings.SMTP_PASSWORD:
            smtp.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        smtp.send_message(msg)


def email_delivery_ready() -> bool:
    """True when we can deliver mail (SMTP or outbox backend)."""
    backend = (settings.EMAIL_BACKEND or "smtp").lower()
    if backend == "outbox":
        return True
    return bool(settings.SMTP_ENABLED and settings.SMTP_HOST)


# Back-compat alias used by auth endpoint / tests
def smtp_ready() -> bool:
    return email_delivery_ready()


async def send_email(*, to_email: str, subject: str, body: str) -> bool:
    """Deliver email via configured backend. Raises on failure."""
    backend = (settings.EMAIL_BACKEND or "smtp").lower()
    if backend == "smtp" and not settings.SMTP_ENABLED:
        # Auto-fallback to outbox in DEBUG so local recovery still works
        if settings.DEBUG:
            logger.warning("smtp_disabled_using_outbox", to=to_email)
            await asyncio.to_thread(
                _send_outbox, to_email=to_email, subject=subject, body=body
            )
            return True
        logger.info("smtp_disabled_skip_send", to=to_email, subject=subject)
        return False

    try:
        await asyncio.to_thread(_send_sync, to_email=to_email, subject=subject, body=body)
        logger.info("smtp_message_sent", to=to_email, subject=subject, backend=backend)
        return True
    except Exception as exc:  # noqa: BLE001
        # Last-resort outbox in DEBUG so the token is not lost
        if settings.DEBUG:
            logger.exception("smtp_send_failed_fallback_outbox", to=to_email, error=str(exc))
            await asyncio.to_thread(
                _send_outbox, to_email=to_email, subject=subject, body=body
            )
            return True
        logger.exception("smtp_send_failed", to=to_email, error=str(exc))
        raise


async def send_password_reset_email(*, to_email: str, reset_token: str) -> bool:
    base = (settings.PASSWORD_RESET_URL_BASE or "").rstrip("/")
    link = f"{base}?token={reset_token}"
    body = (
        "Recibimos un pedido para restablecer tu contraseña en Nexorux ERP.\n\n"
        f"Tu código / token de recuperación:\n{reset_token}\n\n"
        f"También podés abrir este enlace (válido por tiempo limitado):\n{link}\n\n"
        "Si no pediste este cambio, ignorá este correo.\n"
    )
    return await send_email(
        to_email=to_email,
        subject="Nexorux ERP — restablecer contraseña",
        body=body,
    )
