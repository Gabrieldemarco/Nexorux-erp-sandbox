from sqlalchemy import Column, String, Boolean, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.session import Base
from app.models.base import BaseModel


class Supplier(Base, BaseModel):
    """Supplier model for purchases and procurement."""

    __tablename__ = "supplier"

    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenant.id", ondelete="CASCADE"), nullable=False, index=True)
    company_id = Column(UUID(as_uuid=True), ForeignKey("company.id", ondelete="CASCADE"), nullable=False, index=True)
    legal_name = Column(String(255), nullable=False)
    trade_name = Column(String(255))
    rut = Column(String(20), nullable=False)
    document_type = Column(String(50))
    address = Column(String(500))
    email = Column(String(255))
    phone = Column(String(50))
    currency = Column(String(10), nullable=False, default="UYU")
    payment_terms = Column(String(100))
    is_active = Column(Boolean, nullable=False, default=True)
    metadata_json = Column("metadata", JSON, default={})

    tenant = relationship("Tenant")
    company = relationship("Company")
