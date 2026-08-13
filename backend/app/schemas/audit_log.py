from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from uuid import UUID
from datetime import datetime


class AuditLogBase(BaseModel):
    """Base audit log schema."""
    user_id: UUID
    action: str = Field(..., max_length=100)
    entity: str = Field(..., max_length=100)
    entity_id: UUID
    changes: Optional[dict] = None
    ip_address: Optional[str] = Field(None, max_length=45)
    request_id: Optional[str] = Field(None, max_length=255)
    timestamp: Optional[datetime] = None


class AuditLogCreate(AuditLogBase):
    """Schema for creating an audit log."""
    tenant_id: UUID
    company_id: UUID


class AuditLogUpdate(BaseModel):
    """Schema for updating an audit log."""
    user_id: Optional[UUID] = None
    action: Optional[str] = Field(None, max_length=100)
    entity: Optional[str] = Field(None, max_length=100)
    entity_id: Optional[UUID] = None
    changes: Optional[dict] = None
    ip_address: Optional[str] = Field(None, max_length=45)
    request_id: Optional[str] = Field(None, max_length=255)
    timestamp: Optional[datetime] = None


class AuditLogResponse(AuditLogBase):
    """Schema for audit log response."""
    id: UUID
    tenant_id: UUID
    company_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
