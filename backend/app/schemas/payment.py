from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


class PaymentBase(BaseModel):
    """Base payment schema."""
    payment_date: datetime
    amount: float = Field(..., ge=0)
    currency: str = Field(..., max_length=3)
    payment_method: str = Field(..., max_length=50)
    reference: Optional[str] = None
    status: Optional[str] = Field(None, max_length=50)


class PaymentCreate(PaymentBase):
    """Schema for creating a payment."""
    tenant_id: UUID
    company_id: UUID
    invoice_id: Optional[UUID] = None
    customer_id: Optional[UUID] = None


class PaymentUpdate(BaseModel):
    """Schema for updating a payment."""
    payment_date: Optional[datetime] = None
    amount: Optional[float] = Field(None, ge=0)
    currency: Optional[str] = Field(None, max_length=3)
    payment_method: Optional[str] = Field(None, max_length=50)
    reference: Optional[str] = None
    status: Optional[str] = Field(None, max_length=50)
    tenant_id: Optional[UUID] = None
    company_id: Optional[UUID] = None
    invoice_id: Optional[UUID] = None
    customer_id: Optional[UUID] = None


class PaymentResponse(PaymentBase):
    """Schema for payment response."""
    id: UUID
    tenant_id: UUID
    company_id: UUID
    invoice_id: Optional[UUID] = None
    customer_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
