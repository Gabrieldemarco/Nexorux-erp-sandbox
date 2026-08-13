from sqlalchemy import Column, String, ForeignKey, DateTime, Integer, JSON, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.session import Base
from app.models.base import BaseModel


class FiscalResponse(Base, BaseModel):
    """Fiscal response model for DGI responses."""

    __tablename__ = "fiscal_response"

    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenant.id", ondelete="CASCADE"), nullable=False, index=True)
    company_id = Column(UUID(as_uuid=True), ForeignKey("company.id", ondelete="CASCADE"), nullable=False, index=True)
    fiscal_document_id = Column(UUID(as_uuid=True), ForeignKey("fiscal_document.id", ondelete="CASCADE"), nullable=False, index=True)
    request_id = Column(String(255), nullable=False)
    correlation_id = Column(String(255))
    status_code = Column(String(100), nullable=False)
    status_message = Column(String(1000))
    raw_response = Column(JSON, default={})
    received_at = Column(DateTime(timezone=True), server_default=func.now())
    retry_count = Column(Integer, nullable=False, default=0)

    tenant = relationship("Tenant")
    company = relationship("Company")
    fiscal_document = relationship("FiscalDocument", back_populates="responses")
