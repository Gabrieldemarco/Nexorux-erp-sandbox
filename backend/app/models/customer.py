from sqlalchemy import Column, String, Boolean, ForeignKey, Numeric, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.session import Base
from app.models.base import BaseModel


class Customer(Base, BaseModel):
    """Customer model for sales and billing."""

    __tablename__ = "customer"

    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenant.id", ondelete="CASCADE"), nullable=False, index=True)
    company_id = Column(UUID(as_uuid=True), ForeignKey("company.id", ondelete="CASCADE"), nullable=False, index=True)
    customer_type = Column(String(50), nullable=False, default="company")
    legal_name = Column(String(255), nullable=False)
    trade_name = Column(String(255))
    rut = Column(String(20), nullable=False)
    document_type = Column(String(50))
    address = Column(String(500))
    email = Column(String(255))
    phone = Column(String(50))
    currency = Column(String(10), nullable=False, default="UYU")
    credit_limit = Column(Numeric(18, 6), nullable=False, default=0)
    payment_terms = Column(String(100))
    is_active = Column(Boolean, nullable=False, default=True)
    metadata_json = Column("metadata", JSON, default={})

    tenant = relationship("Tenant")
    company = relationship("Company")
