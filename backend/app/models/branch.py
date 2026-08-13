from sqlalchemy import Column, String, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.session import Base
from app.models.base import BaseModel


class Branch(Base, BaseModel):
    """Branch model for company locations."""

    __tablename__ = "branch"

    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenant.id", ondelete="CASCADE"), nullable=False, index=True)
    company_id = Column(UUID(as_uuid=True), ForeignKey("company.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    code = Column(String(100), nullable=False)
    address = Column(String(500))
    phone = Column(String(50))
    email = Column(String(255))
    is_active = Column(Boolean, nullable=False, default=True)

    tenant = relationship("Tenant")
    company = relationship("Company")
