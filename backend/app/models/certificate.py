from sqlalchemy import Column, String, Boolean, DateTime, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.session import Base
from app.models.base import BaseModel


class Certificate(Base, BaseModel):
    """Certificate model for fiscal certificates and signing metadata."""

    __tablename__ = "certificate"

    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenant.id", ondelete="CASCADE"), nullable=False, index=True)
    company_id = Column(UUID(as_uuid=True), ForeignKey("company.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    thumbprint = Column(String(255), nullable=False)
    issued_at = Column(DateTime(timezone=True))
    expires_at = Column(DateTime(timezone=True))
    usage = Column(String(100))
    is_active = Column(Boolean, nullable=False, default=True)
    metadata_json = Column("metadata", JSON, default={})

    tenant = relationship("Tenant")
    company = relationship("Company")
