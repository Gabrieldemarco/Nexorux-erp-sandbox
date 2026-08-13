from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict
from typing import Optional, Dict
from uuid import UUID
from datetime import datetime

from app.core.validators import validate_uruguayan_rut, validate_email


class CustomerBase(BaseModel):
    """Base customer schema."""
    customer_type: str = Field(..., min_length=1, max_length=50)
    legal_name: str = Field(..., min_length=1, max_length=255)
    trade_name: Optional[str] = Field(None, max_length=255)
    rut: str = Field(..., min_length=1, max_length=20)
    document_type: Optional[str] = Field(None, max_length=50)
    address: Optional[str] = Field(None, max_length=500)
    email: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=50)
    currency: str = Field(..., min_length=1, max_length=10)
    credit_limit: float = Field(..., ge=0)
    payment_terms: Optional[str] = Field(None, max_length=100)
    is_active: bool = True
    metadata: Optional[Dict] = Field(default=None, validation_alias="metadata_json")

    model_config = ConfigDict(populate_by_name=True)

    @model_validator(mode="before")
    @classmethod
    def default_final_consumer_rut(cls, data):
        if isinstance(data, dict) and data.get("customer_type") == "final_consumer":
            rut = data.get("rut")
            if rut is None or str(rut).strip() == "":
                data["rut"] = "00000000"
        return data

    @field_validator('rut')
    @classmethod
    def normalize_rut(cls, v: str) -> str:
        cleaned = (v or "").strip()
        if cleaned in {"00000000", "0", "CF"}:
            return "00000000"
        return validate_uruguayan_rut(v)

    @field_validator('email')
    @classmethod
    def normalize_email(cls, v: Optional[str]) -> Optional[str]:
        if v is None or v.strip() == '':
            return v
        return validate_email(v)


class CustomerCreate(CustomerBase):
    """Schema for creating a customer."""
    tenant_id: UUID
    company_id: UUID


class CustomerUpdate(BaseModel):
    """Schema for updating a customer."""
    customer_type: Optional[str] = Field(None, min_length=1, max_length=50)
    legal_name: Optional[str] = Field(None, min_length=1, max_length=255)
    trade_name: Optional[str] = Field(None, max_length=255)
    rut: Optional[str] = Field(None, min_length=1, max_length=20)
    document_type: Optional[str] = Field(None, max_length=50)
    address: Optional[str] = Field(None, max_length=500)
    email: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=50)
    currency: Optional[str] = Field(None, min_length=1, max_length=10)
    credit_limit: Optional[float] = Field(None, ge=0)
    payment_terms: Optional[str] = Field(None, max_length=100)
    is_active: Optional[bool] = None
    metadata: Optional[Dict] = None


class CustomerResponse(BaseModel):
    """Schema for customer response."""
    customer_type: str
    legal_name: str
    trade_name: Optional[str] = None
    rut: str
    document_type: Optional[str] = None
    address: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    currency: str
    credit_limit: float
    payment_terms: Optional[str] = None
    is_active: bool = True
    metadata: Optional[Dict] = Field(default=None, validation_alias="metadata_json")
    id: UUID
    tenant_id: UUID
    company_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
