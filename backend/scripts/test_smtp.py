"""Send a test email using current .env SMTP settings.

Usage:
  python scripts/test_smtp.py destinatario@gmail.com
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


async def main() -> int:
    to = (sys.argv[1] if len(sys.argv) > 1 else "").strip()
    if not to or "@" not in to:
        print("Uso: python scripts/test_smtp.py destinatario@gmail.com")
        return 2

    from app.core.config import settings
    from app.services.email import send_email

    print("EMAIL_BACKEND =", settings.EMAIL_BACKEND)
    print("SMTP_ENABLED  =", settings.SMTP_ENABLED)
    print("SMTP_HOST     =", settings.SMTP_HOST)
    print("SMTP_PORT     =", settings.SMTP_PORT)
    print("SMTP_USER     =", settings.SMTP_USER)
    print("SMTP_FROM     =", settings.SMTP_FROM)
    print("SMTP_USE_TLS  =", settings.SMTP_USE_TLS)
    print("To            =", to)

    if (settings.SMTP_HOST or "") in ("127.0.0.1", "localhost", "mailpit"):
        print(
            "\nAVISO: SMTP_HOST es local (Mailpit). El mail NO llegará a Gmail real.\n"
            "Configurá smtp.gmail.com — ver docs/EMAIL.md\n"
        )

    await send_email(
        to_email=to,
        subject="Nexorux ERP — prueba SMTP",
        body="Si leés esto, el SMTP está funcionando.\n",
    )
    print("OK: envío solicitado sin excepción.")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
