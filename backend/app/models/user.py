from sqlalchemy import Column, String, Boolean, ForeignKey, DateTime, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.session import Base
from app.models.base import BaseModel


class User(Base, BaseModel):
    """User model for authentication and authorization."""

    __tablename__ = "user"

    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenant.id", ondelete="CASCADE"), nullable=False, index=True)
    company_id = Column(UUID(as_uuid=True), ForeignKey("company.id", ondelete="CASCADE"), nullable=False, index=True)
    email = Column(String(255), nullable=False, unique=True)
    username = Column(String(150), nullable=False, unique=True)
    full_name = Column(String(255), nullable=False)
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    last_login_at = Column(DateTime(timezone=True))
    password_reset_token_hash = Column(String(255), index=True)
    password_reset_token_expires_at = Column(DateTime(timezone=True))
    settings = Column(JSON, default={})

    tenant = relationship("Tenant")
    company = relationship("Company")
    roles = relationship("Role", secondary="user_role", back_populates="users")
