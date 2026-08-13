from sqlalchemy import Column, String, ForeignKey, Numeric, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.session import Base
from app.models.base import BaseModel


class PurchaseReceipt(Base, BaseModel):
    """Goods receipt from a supplier — increases warehouse stock."""

    __tablename__ = "purchase_receipt"

    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenant.id", ondelete="CASCADE"), nullable=False, index=True)
    company_id = Column(UUID(as_uuid=True), ForeignKey("company.id", ondelete="CASCADE"), nullable=False, index=True)
    supplier_id = Column(UUID(as_uuid=True), ForeignKey("supplier.id", ondelete="SET NULL"), nullable=True, index=True)
    warehouse_id = Column(UUID(as_uuid=True), ForeignKey("warehouse.id", ondelete="SET NULL"), nullable=True, index=True)
    number = Column(String(50), nullable=False)
    receipt_date = Column(DateTime(timezone=True), nullable=False)
    notes = Column(Text)
    status = Column(String(50), nullable=False, default="received")

    tenant = relationship("Tenant")
    company = relationship("Company")
    supplier = relationship("Supplier")
    warehouse = relationship("Warehouse")
    items = relationship(
        "PurchaseReceiptItem",
        back_populates="receipt",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class PurchaseReceiptItem(Base, BaseModel):
    """Line on a supplier goods receipt."""

    __tablename__ = "purchase_receipt_item"

    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenant.id", ondelete="CASCADE"), nullable=False, index=True)
    company_id = Column(UUID(as_uuid=True), ForeignKey("company.id", ondelete="CASCADE"), nullable=False, index=True)
    receipt_id = Column(
        UUID(as_uuid=True),
        ForeignKey("purchase_receipt.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    product_id = Column(UUID(as_uuid=True), ForeignKey("product.id", ondelete="SET NULL"), nullable=True, index=True)
    quantity = Column(Numeric(18, 6), nullable=False, default=0)
    unit_cost = Column(Numeric(18, 6), nullable=False, default=0)
    description = Column(String(500))

    tenant = relationship("Tenant")
    company = relationship("Company")
    receipt = relationship("PurchaseReceipt", back_populates="items")
    product = relationship("Product")
