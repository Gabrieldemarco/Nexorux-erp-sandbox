from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


class StockMovementBase(BaseModel):
    """Base stock movement schema."""
    quantity: float = Field(..., ge=0)
    movement_type: str = Field(..., max_length=50)
    reference_id: Optional[UUID] = None
    reference_type: Optional[str] = Field(None, max_length=50)
    movement_date: datetime


class StockMovementCreate(StockMovementBase):
    """Schema for creating a stock movement."""
    tenant_id: UUID
    company_id: UUID
    warehouse_id: Optional[UUID] = None
    product_id: Optional[UUID] = None


class StockMovementUpdate(BaseModel):
    """Schema for updating a stock movement."""
    quantity: Optional[float] = Field(None, ge=0)
    movement_type: Optional[str] = Field(None, max_length=50)
    reference_id: Optional[UUID] = None
    reference_type: Optional[str] = Field(None, max_length=50)
    movement_date: Optional[datetime] = None
    tenant_id: Optional[UUID] = None
    company_id: Optional[UUID] = None
    warehouse_id: Optional[UUID] = None
    product_id: Optional[UUID] = None


class StockMovementResponse(StockMovementBase):
    """Schema for stock movement response."""
    id: UUID
    tenant_id: UUID
    company_id: UUID
    warehouse_id: UUID
    product_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
