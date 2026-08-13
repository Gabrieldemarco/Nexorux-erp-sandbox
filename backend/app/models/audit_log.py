from sqlalchemy import Column, String, JSON, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.session import Base
from app.models.base import BaseModel


class AuditLog(Base, BaseModel):
    """Audit log model for tracking system changes."""

    __tablename__ = "audit_log"

    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenant.id", ondelete="CASCADE"), nullable=False, index=True)
    company_id = Column(UUID(as_uuid=True), ForeignKey("company.id", ondelete="CASCADE"), nullable=True, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("user.id", ondelete="SET NULL"), nullable=True, index=True)
    action = Column(String(100), nullable=False)
    entity = Column(String(100), nullable=False)
    entity_id = Column(UUID(as_uuid=True), nullable=False)
    changes = Column(JSON, default={})
    ip_address = Column(String(50))
    request_id = Column(String(255))
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

    tenant = relationship("Tenant")
    company = relationship("Company")
    user = relationship("User")
