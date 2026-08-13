from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from uuid import UUID
from datetime import datetime


class PriceListBase(BaseModel):
    """Base price list schema."""
    name: str = Field(..., min_length=1, max_length=255)
    currency: str = Field(..., max_length=3)
    valid_from: Optional[datetime] = None
    valid_to: Optional[datetime] = None
    is_default: Optional[bool] = False


class PriceListCreate(PriceListBase):
    """Schema for creating a price list."""
    tenant_id: UUID
    company_id: UUID


class PriceListUpdate(BaseModel):
    """Schema for updating a price list."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    currency: Optional[str] = Field(None, max_length=3)
    valid_from: Optional[datetime] = None
    valid_to: Optional[datetime] = None
    is_default: Optional[bool] = None


class PriceListResponse(PriceListBase):
    """Schema for price list response."""
    id: UUID
    tenant_id: UUID
    company_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
