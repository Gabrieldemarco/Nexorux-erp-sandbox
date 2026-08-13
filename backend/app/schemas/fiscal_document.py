from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from uuid import UUID
from datetime import datetime


class FiscalDocumentBase(BaseModel):
    """Base fiscal document schema."""
    invoice_id: Optional[UUID] = None
    document_type: Optional[str] = Field(None, max_length=50)
    series: Optional[str] = Field(None, max_length=50)
    number: Optional[str] = Field(None, max_length=50)
    state: Optional[str] = Field(None, max_length=50)
    issued_at: Optional[datetime] = None
    signed_at: Optional[datetime] = None
    sent_at: Optional[datetime] = None
    response_at: Optional[datetime] = None
    is_contingency: Optional[bool] = False
    xml_reference: Optional[str] = Field(None, max_length=500)
    raw_payload: Optional[dict] = None


class FiscalDocumentCreate(FiscalDocumentBase):
    """Schema for creating a fiscal document."""
    tenant_id: UUID
    company_id: UUID
    invoice_id: UUID
    document_type: str = Field(..., max_length=50)
    series: str = Field(..., max_length=50)
    number: str = Field(..., max_length=50)


class FiscalDocumentUpdate(BaseModel):
    """Schema for updating a fiscal document."""
    invoice_id: Optional[UUID] = None
    document_type: Optional[str] = Field(None, max_length=50)
    series: Optional[str] = Field(None, max_length=50)
    number: Optional[str] = Field(None, max_length=50)
    state: Optional[str] = Field(None, max_length=50)
    issued_at: Optional[datetime] = None
    signed_at: Optional[datetime] = None
    sent_at: Optional[datetime] = None
    response_at: Optional[datetime] = None
    is_contingency: Optional[bool] = None
    xml_reference: Optional[str] = Field(None, max_length=255)
    raw_payload: Optional[dict] = None


class FiscalDocumentResponse(FiscalDocumentBase):
    """Schema for fiscal document response."""
    id: UUID
    tenant_id: UUID
    company_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class FiscalDocumentIssueRequest(BaseModel):
    """Schema for issuing a fiscal document."""
    certificate_id: UUID


class FiscalDocumentSendRequest(BaseModel):
    """Schema for sending a fiscal document to DGI."""
    environment: Optional[str] = None
    certificate_id: Optional[UUID] = None


class FiscalDocumentRetryRequest(BaseModel):
    """Schema for retrying a rejected fiscal document."""
    certificate_id: Optional[UUID] = None


class FiscalDocumentSendTaskResponse(BaseModel):
    """Schema for async send task response."""
    task_id: str
    status: str
    fiscal_document_id: UUID
