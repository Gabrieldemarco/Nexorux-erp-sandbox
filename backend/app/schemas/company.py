from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional
from uuid import UUID
from datetime import datetime

from app.core.validators import validate_uruguayan_rut, validate_email


class CompanyBase(BaseModel):
    """Base company schema."""
    legal_name: str = Field(..., min_length=1, max_length=255)
    trade_name: Optional[str] = Field(None, max_length=255)
    rut: str = Field(..., min_length=1, max_length=20)
    fiscal_address: Optional[str] = Field(None, max_length=500)
    phone: Optional[str] = Field(None, max_length=50)
    email: Optional[str] = Field(None, max_length=255)
    website: Optional[str] = Field(None, max_length=255)
    country: str = "Uruguay"
    department: Optional[str] = Field(None, max_length=100)
    locality: Optional[str] = Field(None, max_length=100)
    currency: str = "UYU"
    tax_regime: Optional[str] = None

    @field_validator("rut")
    @classmethod
    def normalize_rut(cls, v: str) -> str:
        return validate_uruguayan_rut(v)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: Optional[str]) -> Optional[str]:
        if v is None or v.strip() == "":
            return v
        return validate_email(v)


class CompanyCreate(CompanyBase):
    """Schema for creating a company."""
    tenant_id: UUID


class CompanyUpdate(BaseModel):
    """Schema for updating a company."""
    legal_name: Optional[str] = Field(None, min_length=1, max_length=255)
    trade_name: Optional[str] = Field(None, max_length=255)
    rut: Optional[str] = Field(None, min_length=1, max_length=20)
    fiscal_address: Optional[str] = Field(None, max_length=500)
    phone: Optional[str] = Field(None, max_length=50)
    email: Optional[str] = Field(None, max_length=255)
    website: Optional[str] = Field(None, max_length=255)
    country: Optional[str] = None
    department: Optional[str] = Field(None, max_length=100)
    locality: Optional[str] = Field(None, max_length=100)
    currency: Optional[str] = None
    tax_regime: Optional[str] = None


class CompanyResponse(BaseModel):
    """Schema for company response (no strict create-time validators)."""
    legal_name: str
    trade_name: Optional[str] = None
    rut: str
    fiscal_address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    country: str = "Uruguay"
    department: Optional[str] = None
    locality: Optional[str] = None
    currency: str = "UYU"
    tax_regime: Optional[str] = None
    id: UUID
    tenant_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
