from sqlalchemy import Column, String, ForeignKey, DateTime, Boolean, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.session import Base
from app.models.base import BaseModel


class FiscalDocument(Base, BaseModel):
    """Fiscal document model for electronic documents."""

    __tablename__ = "fiscal_document"

    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenant.id", ondelete="CASCADE"), nullable=False, index=True)
    company_id = Column(UUID(as_uuid=True), ForeignKey("company.id", ondelete="CASCADE"), nullable=False, index=True)
    invoice_id = Column(UUID(as_uuid=True), ForeignKey("invoice.id", ondelete="CASCADE"), nullable=False, index=True)
    document_type = Column(String(50), nullable=False)
    series = Column(String(20), nullable=False)
    number = Column(String(50), nullable=False)
    state = Column(String(50), nullable=False, default="draft")
    issued_at = Column(DateTime(timezone=True))
    signed_at = Column(DateTime(timezone=True))
    sent_at = Column(DateTime(timezone=True))
    response_at = Column(DateTime(timezone=True))
    is_contingency = Column(Boolean, nullable=False, default=False)
    xml_reference = Column(String(500))
    raw_payload = Column(JSON, default={})

    tenant = relationship("Tenant")
    company = relationship("Company")
    invoice = relationship("Invoice")
    responses = relationship("FiscalResponse", back_populates="fiscal_document")
