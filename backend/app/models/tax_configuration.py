from sqlalchemy import Column, String, Numeric, DateTime, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.session import Base
from app.models.base import BaseModel


class TaxConfiguration(Base, BaseModel):
    """Tax configuration model for fiscal rules."""

    __tablename__ = "tax_configuration"

    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenant.id", ondelete="CASCADE"), nullable=False, index=True)
    company_id = Column(UUID(as_uuid=True), ForeignKey("company.id", ondelete="CASCADE"), nullable=False, index=True)
    tax_code = Column(String(100), nullable=False)
    description = Column(String(500))
    rate = Column(Numeric(5, 2), nullable=False, default=0)
    effective_from = Column(DateTime(timezone=True), nullable=False)
    effective_to = Column(DateTime(timezone=True))
    metadata_json = Column("metadata", JSON, default={})

    tenant = relationship("Tenant")
    company = relationship("Company")
