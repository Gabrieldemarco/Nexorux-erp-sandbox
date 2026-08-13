import uuid
from typing import Optional

import structlog
from fastapi import Request
from sqlalchemy import select
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.security import decode_token
from app.db.session import AsyncSessionLocal
from app.models.audit_log import AuditLog
from app.models.user import User

logger = structlog.get_logger(__name__)

MUTATING_METHODS = {"POST", "PUT", "PATCH", "DELETE"}
AUDIT_EXCLUDED_PREFIXES = (
    "/api/v1/auth/token",
    "/api/v1/auth/password",
    "/api/v1/audit-logs",
)


def _extract_entity(path: str) -> tuple[str, uuid.UUID]:
    parts = [part for part in path.split("/") if part]
    # /api/v1/{entity}/{id?}
    entity = parts[2] if len(parts) >= 3 else "unknown"
    entity_id = uuid.UUID(int=0)
    if len(parts) >= 4:
        try:
            entity_id = uuid.UUID(parts[3])
        except ValueError:
            pass
    return entity, entity_id


def _extract_token(request: Request) -> Optional[str]:
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        return auth_header[7:]
    return None


class AuditLoggingMiddleware(BaseHTTPMiddleware):
    """Persist audit logs for mutating API requests."""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        if request.method not in MUTATING_METHODS:
            return response
        if not request.url.path.startswith("/api/v1/"):
            return response
        if any(request.url.path.startswith(prefix) for prefix in AUDIT_EXCLUDED_PREFIXES):
            return response

        token = _extract_token(request)
        if not token:
            return response
        payload = decode_token(token)
        if not payload or payload.get("type") != "access":
            return response

        user_id_raw = payload.get("sub")
        if not user_id_raw:
            return response
        try:
            user_id = uuid.UUID(str(user_id_raw))
        except ValueError:
            return response

        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        entity, entity_id = _extract_entity(request.url.path)

        try:
            async with AsyncSessionLocal() as db:
                result = await db.execute(select(User).where(User.id == user_id))
                user = result.scalar_one_or_none()
                if not user:
                    return response

                log = AuditLog(
                    tenant_id=user.tenant_id,
                    company_id=user.company_id,
                    user_id=user.id,
                    action=request.method,
                    entity=entity,
                    entity_id=entity_id,
                    changes={
                        "path": request.url.path,
                        "query": str(request.url.query),
                        "status_code": response.status_code,
                    },
                    ip_address=request.client.host if request.client else None,
                    request_id=request_id,
                )
                db.add(log)
                await db.commit()
        except Exception as exc:
            logger.warning("audit_log_write_failed", error=str(exc), path=request.url.path)

        return response
