from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from uuid import UUID
from datetime import datetime


class WarehouseBase(BaseModel):
    """Base warehouse schema."""
    branch_id: Optional[UUID] = None
    name: str = Field(..., min_length=1, max_length=255)
    code: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    is_active: bool = True


class WarehouseCreate(WarehouseBase):
    """Schema for creating a warehouse."""
    tenant_id: UUID
    company_id: UUID


class WarehouseUpdate(BaseModel):
    """Schema for updating a warehouse."""
    branch_id: Optional[UUID] = None
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    code: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    is_active: Optional[bool] = None


class WarehouseResponse(WarehouseBase):
    """Schema for warehouse response."""
    id: UUID
    tenant_id: UUID
    company_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
