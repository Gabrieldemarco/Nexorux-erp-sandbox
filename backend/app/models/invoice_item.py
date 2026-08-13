from sqlalchemy import Column, String, ForeignKey, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.session import Base
from app.models.base import BaseModel


class InvoiceItem(Base, BaseModel):
    """Invoice item model for line items."""

    __tablename__ = "invoice_item"

    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenant.id", ondelete="CASCADE"), nullable=False, index=True)
    company_id = Column(UUID(as_uuid=True), ForeignKey("company.id", ondelete="CASCADE"), nullable=False, index=True)
    invoice_id = Column(UUID(as_uuid=True), ForeignKey("invoice.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id = Column(UUID(as_uuid=True), ForeignKey("product.id", ondelete="SET NULL"), nullable=True, index=True)
    quantity = Column(Numeric(18, 6), nullable=False, default=0)
    unit_price = Column(Numeric(18, 6), nullable=False, default=0)
    discount = Column(Numeric(18, 6), nullable=False, default=0)
    tax_amount = Column(Numeric(18, 6), nullable=False, default=0)
    total = Column(Numeric(18, 6), nullable=False, default=0)
    description = Column(String(1000))

    invoice = relationship("Invoice", back_populates="items")
    product = relationship("Product")
