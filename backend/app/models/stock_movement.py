from sqlalchemy import Column, String, ForeignKey, Numeric, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.session import Base
from app.models.base import BaseModel


class StockMovement(Base, BaseModel):
    """Stock movement model for inventory tracking."""

    __tablename__ = "stock_movement"

    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenant.id", ondelete="CASCADE"), nullable=False, index=True)
    company_id = Column(UUID(as_uuid=True), ForeignKey("company.id", ondelete="CASCADE"), nullable=False, index=True)
    warehouse_id = Column(UUID(as_uuid=True), ForeignKey("warehouse.id", ondelete="SET NULL"), nullable=True, index=True)
    product_id = Column(UUID(as_uuid=True), ForeignKey("product.id", ondelete="SET NULL"), nullable=True, index=True)
    quantity = Column(Numeric(18, 6), nullable=False, default=0)
    movement_type = Column(String(50), nullable=False)
    reference_id = Column(UUID(as_uuid=True))
    reference_type = Column(String(100))
    movement_date = Column(DateTime(timezone=True), nullable=False)

    tenant = relationship("Tenant")
    company = relationship("Company")
    warehouse = relationship("Warehouse")
    product = relationship("Product")
