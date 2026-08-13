from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.session import Base
from app.models.base import BaseModel


class Permission(Base, BaseModel):
    """Permission model for granular access control."""

    __tablename__ = "permission"

    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenant.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    code = Column(String(100), nullable=False)
    description = Column(String(500))

    tenant = relationship("Tenant")
    roles = relationship("Role", secondary="role_permission", back_populates="permissions")
