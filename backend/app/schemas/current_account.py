from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class CurrentAccountInvoiceLine(BaseModel):
    invoice_id: UUID
    series: str
    number: str
    document_type: str
    status: str
    issue_date: Optional[datetime] = None
    due_date: Optional[datetime] = None
    currency: str
    total: float
    signed_total: float
    paid_amount: float
    balance: float
    overdue: bool = False


class CurrentAccountPaymentLine(BaseModel):
    payment_id: UUID
    payment_date: datetime
    amount: float
    currency: str
    payment_method: str
    reference: Optional[str] = None
    status: str
    invoice_id: Optional[UUID] = None


class CurrentAccountBalance(BaseModel):
    customer_id: UUID
    legal_name: str
    trade_name: Optional[str] = None
    rut: str
    currency: str
    is_active: bool
    credit_limit: float
    invoiced: float
    paid: float
    balance: float
    available_credit: Optional[float] = None
    overdue: float = 0
    open_invoices: int = 0

    model_config = ConfigDict(from_attributes=True)


class CurrentAccountStatement(CurrentAccountBalance):
    invoices: List[CurrentAccountInvoiceLine]
    payments: List[CurrentAccountPaymentLine]
