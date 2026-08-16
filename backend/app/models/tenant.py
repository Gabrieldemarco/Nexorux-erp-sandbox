from sqlalchemy import Column, String, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.session import Base
from app.models.base import BaseModel


class Tenant(Base, BaseModel):
    """Tenant model for multi-tenancy."""
    
    __tablename__ = "tenant"
    
    name = Column(String(255), nullable=False)
    status = Column(String(50), nullable=False, default="active")
    settings = Column(JSON, default={})
    
    # Configuración fiscal multi-motor
    fiscal_engine_id = Column(String(50), nullable=False, default="dgi_uruguay")
    fiscal_config = Column(JSON, default={})
    
    # Relationships
    companies = relationship("Company", back_populates="tenant")
