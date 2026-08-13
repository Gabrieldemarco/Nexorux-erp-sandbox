from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict
from uuid import UUID
from datetime import datetime


class ProductBase(BaseModel):
    """Base product schema."""
    name: str = Field(..., min_length=1, max_length=255)
    sku: str = Field(..., min_length=1, max_length=100)
    barcode: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = Field(None, max_length=1000)
    product_type: str = Field(..., min_length=1, max_length=50)
    unit_of_measure: str = Field(..., min_length=1, max_length=50)
    sales_price: float = Field(..., ge=0)
    cost_price: float = Field(..., ge=0)
    tax_rate: float = Field(..., ge=0)
    is_service: bool = False
    is_active: bool = True
    metadata: Optional[Dict] = Field(default=None, validation_alias="metadata_json")

    model_config = ConfigDict(populate_by_name=True)


class ProductCreate(ProductBase):
    """Schema for creating a product."""
    tenant_id: UUID
    company_id: UUID


class ProductUpdate(BaseModel):
    """Schema for updating a product."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    sku: Optional[str] = Field(None, min_length=1, max_length=100)
    barcode: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = Field(None, max_length=1000)
    product_type: Optional[str] = Field(None, min_length=1, max_length=50)
    unit_of_measure: Optional[str] = Field(None, min_length=1, max_length=50)
    sales_price: Optional[float] = Field(None, ge=0)
    cost_price: Optional[float] = Field(None, ge=0)
    tax_rate: Optional[float] = Field(None, ge=0)
    is_service: Optional[bool] = None
    is_active: Optional[bool] = None
    metadata: Optional[Dict] = None


class ProductResponse(ProductBase):
    """Schema for product response."""
    id: UUID
    tenant_id: UUID
    company_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
