from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.session import Base
from app.models.base import BaseModel


class Company(Base, BaseModel):
    """Company model representing a business entity."""
    
    __tablename__ = "company"
    
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenant.id", ondelete="CASCADE"), nullable=False, index=True)
    legal_name = Column(String(255), nullable=False)
    trade_name = Column(String(255))
    rut = Column(String(20), nullable=False)
    fiscal_address = Column(String(500))
    phone = Column(String(50))
    email = Column(String(255))
    website = Column(String(255))
    country = Column(String(100), default="Uruguay")
    department = Column(String(100))
    locality = Column(String(100))
    currency = Column(String(10), default="UYU")
    tax_regime = Column(String(50))
    
    # Relationships
    tenant = relationship("Tenant", back_populates="companies")
