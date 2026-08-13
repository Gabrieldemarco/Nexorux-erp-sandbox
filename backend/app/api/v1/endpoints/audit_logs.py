from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.db.session import get_db
from app.models.audit_log import AuditLog
from app.schemas.audit_log import AuditLogResponse
from app.core.rbac import require_permissions
from app.core.permissions import (
    PERMISSION_AUDIT_LOGS_READ
)

from app.models.user import User
import structlog

logger = structlog.get_logger(__name__)

router = APIRouter()


@router.get("/", response_model=List[AuditLogResponse])
async def list_audit_logs(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions(PERMISSION_AUDIT_LOGS_READ)),
):
    """List audit logs for the current user's tenant."""
    logger.info("list_audit_logs_called", skip=skip, limit=limit, tenant_id=current_user.tenant_id)
    stmt = select(AuditLog).where(AuditLog.tenant_id == current_user.tenant_id).offset(skip).limit(limit)
    result = await db.execute(stmt)
    audit_logs = result.scalars().all()
    return audit_logs


@router.get("/{audit_log_id}", response_model=AuditLogResponse)
async def get_audit_log(
    audit_log_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions(PERMISSION_AUDIT_LOGS_READ)),
):
    """Get a specific audit log by ID for the current tenant."""
    logger.info("get_audit_log_called", audit_log_id=audit_log_id, tenant_id=current_user.tenant_id)
    stmt = select(AuditLog).where(
        AuditLog.id == audit_log_id,
        AuditLog.tenant_id == current_user.tenant_id,
    )
    result = await db.execute(stmt)
    audit_log_obj = result.scalar_one_or_none()
    if not audit_log_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audit log not found",
        )
    return audit_log_obj