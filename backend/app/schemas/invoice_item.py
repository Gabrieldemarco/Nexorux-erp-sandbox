from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


class InvoiceItemBase(BaseModel):
    """Base invoice item schema."""
    tenant_id: UUID
    company_id: UUID
    invoice_id: UUID
    product_id: Optional[UUID] = None
    quantity: float = Field(..., ge=0)
    unit_price: float = Field(..., ge=0)
    discount: Optional[float] = Field(None, ge=0)
    tax_amount: float = Field(..., ge=0)
    total: float = Field(..., ge=0)
    description: Optional[str] = None


class InvoiceItemCreate(InvoiceItemBase):
    """Schema for creating an invoice item."""


class InvoiceItemUpdate(BaseModel):
    """Schema for updating an invoice item."""
    tenant_id: Optional[UUID] = None
    company_id: Optional[UUID] = None
    invoice_id: Optional[UUID] = None
    product_id: Optional[UUID] = None
    quantity: Optional[float] = Field(None, ge=0)
    unit_price: Optional[float] = Field(None, ge=0)
    discount: Optional[float] = Field(None, ge=0)
    tax_amount: Optional[float] = Field(None, ge=0)
    total: Optional[float] = Field(None, ge=0)
    description: Optional[str] = None


class InvoiceItemResponse(InvoiceItemBase):
    """Schema for invoice item response."""
    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
