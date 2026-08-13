from pydantic import BaseModel, Field, ConfigDict, AliasChoices
from typing import Optional
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
    metadata_json: Optional[dict] = Field(
        default=None,
        validation_alias=AliasChoices("metadata", "metadata_json"),
        serialization_alias="metadata",
    )

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
    metadata_json: Optional[dict] = Field(
        default=None,
        validation_alias=AliasChoices("metadata", "metadata_json"),
        serialization_alias="metadata",
    )

    model_config = ConfigDict(populate_by_name=True)


class CertificateResponse(CertificateBase):
    """Schema for certificate response."""

    id: UUID
    tenant_id: UUID
    company_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
