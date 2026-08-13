from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.session import Base
from app.models.base import BaseModel


class PriceList(Base, BaseModel):
    """Price list model for pricing strategies."""

    __tablename__ = "price_list"

    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenant.id", ondelete="CASCADE"), nullable=False, index=True)
    company_id = Column(UUID(as_uuid=True), ForeignKey("company.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    currency = Column(String(10), nullable=False, default="UYU")
    valid_from = Column(DateTime(timezone=True), nullable=False)
    valid_to = Column(DateTime(timezone=True))
    is_default = Column(Boolean, nullable=False, default=False)

    tenant = relationship("Tenant")
    company = relationship("Company")
