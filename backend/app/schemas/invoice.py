from datetime import datetime
from typing import Optional, Dict
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


class InvoiceBase(BaseModel):
    """Base invoice schema."""
    document_type: str = Field(..., max_length=50)
    series: str = Field(..., max_length=20)
    number: str = Field(..., max_length=50)
    status: Optional[str] = Field(None, max_length=50)
    issue_date: datetime
    due_date: datetime
    subtotal: float = Field(..., ge=0)
    tax_total: float = Field(..., ge=0)
    discount_total: float = Field(..., ge=0)
    total: float = Field(..., ge=0)
    currency: str = Field(..., max_length=3)
    exchange_rate: Optional[float] = Field(None, ge=0)
    notes: Optional[str] = None
    metadata: Optional[Dict] = Field(default=None, validation_alias="metadata_json")

    model_config = ConfigDict(populate_by_name=True)


class InvoiceCreate(InvoiceBase):
    """Schema for creating an invoice."""
    tenant_id: UUID
    company_id: UUID
    customer_id: UUID
    branch_id: UUID
    warehouse_id: UUID


class InvoiceUpdate(BaseModel):
    """Schema for updating an invoice."""
    document_type: Optional[str] = Field(None, max_length=50)
    series: Optional[str] = Field(None, max_length=20)
    number: Optional[str] = Field(None, max_length=50)
    status: Optional[str] = Field(None, max_length=50)
    issue_date: Optional[datetime] = None
    due_date: Optional[datetime] = None
    subtotal: Optional[float] = Field(None, ge=0)
    tax_total: Optional[float] = Field(None, ge=0)
    discount_total: Optional[float] = Field(None, ge=0)
    total: Optional[float] = Field(None, ge=0)
    currency: Optional[str] = Field(None, max_length=3)
    exchange_rate: Optional[float] = Field(None, ge=0)
    notes: Optional[str] = None
    metadata: Optional[Dict] = None
    tenant_id: Optional[UUID] = None
    company_id: Optional[UUID] = None
    customer_id: Optional[UUID] = None
    branch_id: Optional[UUID] = None
    warehouse_id: Optional[UUID] = None


class InvoiceResponse(InvoiceBase):
    """Schema for invoice response."""
    id: UUID
    tenant_id: UUID
    company_id: UUID
    customer_id: UUID
    branch_id: UUID
    warehouse_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
