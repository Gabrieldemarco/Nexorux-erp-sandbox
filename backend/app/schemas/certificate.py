from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict
from uuid import UUID
from datetime import datetime


class CertificateBase(BaseModel):
    """Base certificate schema."""

    name: str = Field(..., min_length=1, max_length=255)
    thumbprint: str = Field(..., min_length=1, max_length=255)
    issued_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    usage: Optional[str] = Field(None, max_length=100)
    is_active: Optional[bool] = True
    # Python name must NOT be validation_alias "metadata" first: SQLAlchemy
    # DeclarativeBase exposes .metadata as MetaData, which breaks from_attributes.
    metadata: Optional[Dict] = Field(default=None, validation_alias="metadata_json")

    model_config = ConfigDict(populate_by_name=True)


class CertificateCreate(CertificateBase):
    """Schema for creating a certificate."""

    tenant_id: UUID
    company_id: UUID


class CertificateUpdate(BaseModel):
    """Schema for updating a certificate."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    thumbprint: Optional[str] = Field(None, min_length=1, max_length=255)
    issued_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    usage: Optional[str] = Field(None, max_length=100)
    is_active: Optional[bool] = None
    metadata: Optional[Dict] = Field(default=None, validation_alias="metadata_json")

    model_config = ConfigDict(populate_by_name=True)


class CertificateResponse(CertificateBase):
    """Schema for certificate response."""

    id: UUID
    tenant_id: UUID
    company_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
