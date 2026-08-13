from sqlalchemy import Column, String, ForeignKey, Numeric, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.session import Base
from app.models.base import BaseModel


class Payment(Base, BaseModel):
    """Payment model for invoices."""

    __tablename__ = "payment"

    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenant.id", ondelete="CASCADE"), nullable=False, index=True)
    company_id = Column(UUID(as_uuid=True), ForeignKey("company.id", ondelete="CASCADE"), nullable=False, index=True)
    invoice_id = Column(UUID(as_uuid=True), ForeignKey("invoice.id", ondelete="SET NULL"), nullable=True, index=True)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customer.id", ondelete="SET NULL"), nullable=True, index=True)
    payment_date = Column(DateTime(timezone=True), nullable=False)
    amount = Column(Numeric(18, 6), nullable=False)
    currency = Column(String(10), nullable=False, default="UYU")
    payment_method = Column(String(100), nullable=False)
    reference = Column(String(255))
    status = Column(String(50), nullable=False, default="pending")

    tenant = relationship("Tenant")
    company = relationship("Company")
    invoice = relationship("Invoice")
    customer = relationship("Customer")
