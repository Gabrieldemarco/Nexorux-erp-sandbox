from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from uuid import UUID
from datetime import datetime


class FiscalResponseBase(BaseModel):
    """Base fiscal response schema."""
    fiscal_document_id: UUID
    request_id: Optional[str] = Field(None, max_length=255)
    correlation_id: Optional[str] = Field(None, max_length=255)
    status_code: int
    status_message: Optional[str] = Field(None, max_length=500)
    raw_response: Optional[dict] = None
    received_at: Optional[datetime] = None
    retry_count: Optional[int] = 0


class FiscalResponseCreate(FiscalResponseBase):
    """Schema for creating a fiscal response."""
    tenant_id: UUID
    company_id: UUID


class FiscalResponseUpdate(BaseModel):
    """Schema for updating a fiscal response."""
    fiscal_document_id: Optional[UUID] = None
    request_id: Optional[str] = Field(None, max_length=255)
    correlation_id: Optional[str] = Field(None, max_length=255)
    status_code: Optional[int] = None
    status_message: Optional[str] = Field(None, max_length=500)
    raw_response: Optional[dict] = None
    received_at: Optional[datetime] = None
    retry_count: Optional[int] = None


class FiscalResponseResponse(FiscalResponseBase):
    """Schema for fiscal response response."""
    id: UUID
    tenant_id: UUID
    company_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
