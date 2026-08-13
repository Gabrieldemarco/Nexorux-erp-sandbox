from sqlalchemy import Column, String, ForeignKey, Numeric, DateTime, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.session import Base
from app.models.base import BaseModel


class Invoice(Base, BaseModel):
    """Invoice model for sales documents."""

    __tablename__ = "invoice"

    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenant.id", ondelete="CASCADE"), nullable=False, index=True)
    company_id = Column(UUID(as_uuid=True), ForeignKey("company.id", ondelete="CASCADE"), nullable=False, index=True)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customer.id", ondelete="SET NULL"), nullable=True, index=True)
    branch_id = Column(UUID(as_uuid=True), ForeignKey("branch.id", ondelete="SET NULL"), nullable=True, index=True)
    warehouse_id = Column(UUID(as_uuid=True), ForeignKey("warehouse.id", ondelete="SET NULL"), nullable=True, index=True)
    document_type = Column(String(50), nullable=False)
    series = Column(String(20), nullable=False)
    number = Column(String(50), nullable=False)
    status = Column(String(50), nullable=False, default="draft")
    issue_date = Column(DateTime(timezone=True))
    due_date = Column(DateTime(timezone=True))
    subtotal = Column(Numeric(18, 6), nullable=False, default=0)
    tax_total = Column(Numeric(18, 6), nullable=False, default=0)
    discount_total = Column(Numeric(18, 6), nullable=False, default=0)
    total = Column(Numeric(18, 6), nullable=False, default=0)
    currency = Column(String(10), nullable=False, default="UYU")
    exchange_rate = Column(Numeric(18, 6), nullable=False, default=1)
    notes = Column(String(1000))
    metadata_json = Column("metadata", JSON, default={})

    tenant = relationship("Tenant")
    company = relationship("Company")
    customer = relationship("Customer")
    branch = relationship("Branch")
    warehouse = relationship("Warehouse")
    items = relationship(
        "InvoiceItem",
        back_populates="invoice",
        passive_deletes=True,
    )
