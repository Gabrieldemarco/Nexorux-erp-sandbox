from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict
from uuid import UUID
from datetime import datetime


class TaxConfigurationBase(BaseModel):
    """Base tax configuration schema."""

    tax_code: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    rate: float
    effective_from: Optional[datetime] = None
    effective_to: Optional[datetime] = None
    # Prefer ORM attr metadata_json; never alias first to SQLAlchemy .metadata
    metadata: Optional[Dict] = Field(default=None, validation_alias="metadata_json")

    model_config = ConfigDict(populate_by_name=True)


class TaxConfigurationCreate(TaxConfigurationBase):
    """Schema for creating a tax configuration."""

    tenant_id: UUID
    company_id: UUID


class TaxConfigurationUpdate(BaseModel):
    """Schema for updating a tax configuration."""

    tax_code: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    rate: Optional[float] = None
    effective_from: Optional[datetime] = None
    effective_to: Optional[datetime] = None
    metadata: Optional[Dict] = Field(default=None, validation_alias="metadata_json")

    model_config = ConfigDict(populate_by_name=True)


class TaxConfigurationResponse(TaxConfigurationBase):
    """Schema for tax configuration response."""

    id: UUID
    tenant_id: UUID
    company_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
