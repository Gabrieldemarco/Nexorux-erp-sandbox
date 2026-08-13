from sqlalchemy import Column, String, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.session import Base
from app.models.base import BaseModel


class Role(Base, BaseModel):
    """Role model for RBAC."""

    __tablename__ = "role"

    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenant.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    key = Column(String(100), nullable=False)
    description = Column(String(500))
    is_default = Column(Boolean, nullable=False, default=False)

    tenant = relationship("Tenant")
    users = relationship("User", secondary="user_role", back_populates="roles")
    permissions = relationship("Permission", secondary="role_permission", back_populates="roles")
