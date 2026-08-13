from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict
from uuid import UUID
from datetime import datetime


class TenantBase(BaseModel):
    """Base tenant schema."""
    name: str = Field(..., min_length=1, max_length=255)
    status: Optional[str] = "active"
    settings: Optional[Dict] = {}


class TenantCreate(TenantBase):
    """Schema for creating a tenant."""
    pass


class TenantUpdate(BaseModel):
    """Schema for updating a tenant."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    status: Optional[str] = None
    settings: Optional[Dict] = None


class TenantResponse(TenantBase):
    """Schema for tenant response."""
    id: UUID
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
