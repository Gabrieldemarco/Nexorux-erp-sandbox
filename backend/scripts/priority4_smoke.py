#!/usr/bin/env python3
"""Smoke checks for Priority 4 security hardening."""

from __future__ import annotations

import asyncio
import uuid
import sys
from pathlib import Path
import os

from fastapi.testclient import TestClient
from sqlalchemy import func, select

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Smoke: evitar dependencia de Redis local si no está levantado.
# Queremos validar: audit middleware + RLS context (Postgres).
# Forzamos explícitamente porque el entorno del shell podría traer DEBUG/LOCKOUT_USE_REDIS previos.
os.environ["DEBUG"] = "true"
os.environ["LOCKOUT_USE_REDIS"] = "false"
os.environ["RLS_TENANT_CONTEXT_ENABLED"] = "true"
os.environ["RATE_LIMIT_ENABLED"] = "false"

from app.api.v1.endpoints.auth import _is_locked_async
from app.main import app
from app.db.session import AsyncSessionLocal
from app.models.audit_log import AuditLog


def _register_payload(prefix: str) -> dict:
    suffix = uuid.uuid4().hex[:8]
    return {
        "email": f"{prefix}_{suffix}@example.com",
        "username": f"{prefix}_{suffix}",
        "full_name": f"{prefix.title()} User",
        "password": "secret123",
        "tenant_id": None,
        "company_id": None,
        "is_active": True,
        "settings": {},
    }


async def _count_audit_logs_for_user(user_id: str) -> int:
    async with AsyncSessionLocal() as db:
        stmt = select(func.count()).select_from(AuditLog).where(AuditLog.user_id == user_id)
        result = await db.execute(stmt)
        return int(result.scalar_one())


def main() -> None:
    client = TestClient(app, base_url="http://localhost")

    # 1) Lockout smoke
    lockout_user = _register_payload("lockout")
    reg = client.post("/api/v1/auth/register", json=lockout_user)
    assert reg.status_code == 201, f"register failed: {reg.status_code} {reg.text}"

    for _ in range(5):
        fail = client.post(
            "/api/v1/auth/token",
            data={"username": lockout_user["email"], "password": "wrong-password"},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        assert fail.status_code == 401

    locked = asyncio.run(_is_locked_async(lockout_user["email"]))
    assert locked is True, "lockout did not activate after max attempts"
    print("lockout_smoke: ok")

    # 2) Audit middleware smoke
    audit_user = _register_payload("audit")
    reg2 = client.post("/api/v1/auth/register", json=audit_user)
    assert reg2.status_code == 201, f"register 2 failed: {reg2.status_code} {reg2.text}"
    audit_user_id = reg2.json()["id"]

    token_resp = client.post(
        "/api/v1/auth/token",
        data={"username": audit_user["email"], "password": audit_user["password"]},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert token_resp.status_code == 200, f"login failed: {token_resp.status_code} {token_resp.text}"
    access_token = token_resp.json()["access_token"]

    before = asyncio.run(_count_audit_logs_for_user(audit_user_id))
    mutate = client.post(
        "/api/v1/products/",
        json={},
        headers={"Authorization": f"Bearer {access_token}"},
    )
    # Any status here is acceptable for smoke (usually 422), we only care audit write.
    assert mutate.status_code in (200, 201, 400, 401, 403, 404, 422)
    after = asyncio.run(_count_audit_logs_for_user(audit_user_id))
    assert after >= before + 1, f"audit log did not increase (before={before}, after={after})"
    print("audit_middleware_smoke: ok")

    print("priority4_smoke: success")


if __name__ == "__main__":
    main()
