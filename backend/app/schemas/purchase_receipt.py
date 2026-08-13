from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


class PurchaseReceiptItemCreate(BaseModel):
    product_id: UUID
    quantity: float = Field(..., gt=0)
    unit_cost: float = Field(0, ge=0)
    description: Optional[str] = Field(None, max_length=500)


class PurchaseReceiptItemResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    company_id: UUID
    receipt_id: UUID
    product_id: Optional[UUID] = None
    quantity: float
    unit_cost: float
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PurchaseReceiptCreate(BaseModel):
    tenant_id: UUID
    company_id: UUID
    supplier_id: UUID
    warehouse_id: UUID
    number: Optional[str] = Field(None, max_length=50)
    receipt_date: datetime
    notes: Optional[str] = None
    items: List[PurchaseReceiptItemCreate] = Field(..., min_length=1)


class PurchaseReceiptResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    company_id: UUID
    supplier_id: Optional[UUID] = None
    warehouse_id: Optional[UUID] = None
    number: str
    receipt_date: datetime
    notes: Optional[str] = None
    status: str
    items: List[PurchaseReceiptItemResponse] = []
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
