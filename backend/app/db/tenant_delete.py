"""Tenant-scoped hard deletes using explicit SQL (rowcount-checked)."""

from __future__ import annotations

from typing import Any, Type
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession


async def delete_tenant_entity(
    db: AsyncSession,
    model: Type[Any],
    entity_id: str | UUID,
    tenant_id: UUID,
    *,
    not_found_detail: str = "Resource not found",
) -> None:
    """DELETE one row by id+tenant_id. Raises 404 if nothing was removed."""
    stmt = delete(model).where(
        model.id == entity_id,
        model.tenant_id == tenant_id,
    )
    result = await db.execute(stmt)
    if result.rowcount == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=not_found_detail,
        )
    await db.commit()
