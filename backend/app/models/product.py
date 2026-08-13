from sqlalchemy import Column, String, Boolean, ForeignKey, Numeric, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.session import Base
from app.models.base import BaseModel


class Product(Base, BaseModel):
    """Product model for goods and services."""

    __tablename__ = "product"

    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenant.id", ondelete="CASCADE"), nullable=False, index=True)
    company_id = Column(UUID(as_uuid=True), ForeignKey("company.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    sku = Column(String(100), nullable=False)
    barcode = Column(String(100))
    description = Column(String(1000))
    product_type = Column(String(50), nullable=False, default="good")
    unit_of_measure = Column(String(50), nullable=False, default="unit")
    sales_price = Column(Numeric(18, 6), nullable=False, default=0)
    cost_price = Column(Numeric(18, 6), nullable=False, default=0)
    tax_rate = Column(Numeric(5, 2), nullable=False, default=0)
    is_service = Column(Boolean, nullable=False, default=False)
    is_active = Column(Boolean, nullable=False, default=True)
    metadata_json = Column("metadata", JSON, default={})

    tenant = relationship("Tenant")
    company = relationship("Company")
