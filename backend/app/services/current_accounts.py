"""Customer current accounts (cuentas corrientes) from invoices + payments."""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional, Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.catalog import (
    INVOICE_OPEN_STATUS,
    INVOICE_PAID_STATUS,
    INVOICE_STATUSES,
    PAYMENT_STATUSES,
)
from app.models.customer import Customer
from app.models.invoice import Invoice
from app.models.payment import Payment
from app.schemas.current_account import (
    CurrentAccountBalance,
    CurrentAccountInvoiceLine,
    CurrentAccountPaymentLine,
    CurrentAccountStatement,
)
from app.services.fiscal.cfe_types import is_credit_note

RECEIVABLE_STATUSES = frozenset(
    str(row["value"]) for row in INVOICE_STATUSES if row.get("affects_receivable")
)
COMPLETED_PAYMENT_STATUSES = frozenset(
    str(row["value"]) for row in PAYMENT_STATUSES if row.get("counts_as_paid")
)
SKIP_INVOICE_STATUS_SYNC = frozenset({"draft", "cancelled"})


def _as_decimal(value) -> Decimal:
    if value is None:
        return Decimal("0")
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def _money(value: Decimal) -> float:
    return float(value.quantize(Decimal("0.01")))


def invoice_affects_receivable(invoice: Invoice) -> bool:
    return (invoice.status or "").strip().lower() in RECEIVABLE_STATUSES


def payment_counts_as_paid(payment: Payment) -> bool:
    return (payment.status or "").strip().lower() in COMPLETED_PAYMENT_STATUSES


def invoice_signed_total(invoice: Invoice) -> Decimal:
    total = _as_decimal(invoice.total)
    if is_credit_note(str(invoice.document_type or "")):
        return -total
    return total


async def _load_customers(
    db: AsyncSession,
    tenant_id: UUID,
    company_id: Optional[UUID] = None,
    customer_id: Optional[UUID] = None,
) -> List[Customer]:
    stmt = select(Customer).where(Customer.tenant_id == tenant_id)
    result = await db.execute(stmt)
    rows = list(result.scalars().all())
    if company_id:
        rows = [c for c in rows if str(c.company_id) == str(company_id)]
    if customer_id:
        rows = [c for c in rows if str(c.id) == str(customer_id)]
    return rows


async def _load_invoices(db: AsyncSession, tenant_id: UUID) -> List[Invoice]:
    stmt = select(Invoice).where(Invoice.tenant_id == tenant_id)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def _load_payments(db: AsyncSession, tenant_id: UUID) -> List[Payment]:
    stmt = select(Payment).where(Payment.tenant_id == tenant_id)
    result = await db.execute(stmt)
    return list(result.scalars().all())


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _aware(value: Optional[datetime]) -> datetime:
    if value is None:
        return datetime.min.replace(tzinfo=timezone.utc)
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


def _is_overdue(invoice: Invoice, remaining: Decimal, now: datetime) -> bool:
    if remaining <= 0:
        return False
    due = invoice.due_date
    if due is None:
        return False
    if due.tzinfo is None:
        due = due.replace(tzinfo=timezone.utc)
    return due < now


def _payments_for_invoice(payments: Sequence[Payment], invoice_id) -> Decimal:
    total = Decimal("0")
    for pay in payments:
        if not payment_counts_as_paid(pay):
            continue
        if pay.invoice_id is None:
            continue
        if str(pay.invoice_id) != str(invoice_id):
            continue
        total += _as_decimal(pay.amount)
    return total


def _customer_payments(payments: Sequence[Payment], customer_id) -> Decimal:
    total = Decimal("0")
    for pay in payments:
        if not payment_counts_as_paid(pay):
            continue
        if pay.customer_id is None:
            continue
        if str(pay.customer_id) != str(customer_id):
            continue
        total += _as_decimal(pay.amount)
    return total


def _build_invoice_line(
    invoice: Invoice,
    payments: Sequence[Payment],
    now: datetime,
) -> CurrentAccountInvoiceLine:
    signed = invoice_signed_total(invoice)
    paid = _payments_for_invoice(payments, invoice.id)
    # Remaining follows the document sign: NC remaining goes toward zero from negative.
    if signed < 0:
        remaining = signed + paid
    else:
        remaining = signed - paid
    return CurrentAccountInvoiceLine(
        invoice_id=invoice.id,
        series=invoice.series,
        number=invoice.number,
        document_type=invoice.document_type,
        status=invoice.status,
        issue_date=invoice.issue_date,
        due_date=invoice.due_date,
        currency=invoice.currency,
        total=_money(_as_decimal(invoice.total)),
        signed_total=_money(signed),
        paid_amount=_money(paid),
        balance=_money(remaining),
        overdue=_is_overdue(invoice, remaining if remaining > 0 else Decimal("0"), now),
    )


def _build_balance(
    customer: Customer,
    invoices: Sequence[Invoice],
    payments: Sequence[Payment],
    now: datetime,
) -> CurrentAccountBalance:
    invoiced = Decimal("0")
    overdue = Decimal("0")
    open_invoices = 0
    cust_invoices = [
        inv
        for inv in invoices
        if inv.customer_id is not None
        and str(inv.customer_id) == str(customer.id)
        and invoice_affects_receivable(inv)
    ]
    for inv in cust_invoices:
        line = _build_invoice_line(inv, payments, now)
        invoiced += _as_decimal(line.signed_total)
        if _as_decimal(line.balance) > 0:
            open_invoices += 1
            if line.overdue:
                overdue += _as_decimal(line.balance)

    paid = _customer_payments(payments, customer.id)
    balance = invoiced - paid
    credit_limit = _as_decimal(customer.credit_limit)
    available = None
    if credit_limit > 0:
        available = _money(credit_limit - balance)

    return CurrentAccountBalance(
        customer_id=customer.id,
        legal_name=customer.legal_name,
        trade_name=customer.trade_name,
        rut=customer.rut,
        currency=customer.currency,
        is_active=bool(customer.is_active),
        credit_limit=_money(credit_limit),
        invoiced=_money(invoiced),
        paid=_money(paid),
        balance=_money(balance),
        available_credit=available,
        overdue=_money(overdue),
        open_invoices=open_invoices,
    )


async def list_current_accounts(
    db: AsyncSession,
    tenant_id: UUID,
    company_id: Optional[UUID] = None,
) -> List[CurrentAccountBalance]:
    customers = await _load_customers(db, tenant_id, company_id=company_id)
    invoices = await _load_invoices(db, tenant_id)
    payments = await _load_payments(db, tenant_id)
    now = _now()
    rows = [_build_balance(c, invoices, payments, now) for c in customers]
    rows.sort(key=lambda r: (abs(r.balance) * -1, r.legal_name.lower()))
    return rows


async def get_current_account(
    db: AsyncSession,
    tenant_id: UUID,
    customer_id: UUID,
    company_id: Optional[UUID] = None,
) -> Optional[CurrentAccountStatement]:
    customers = await _load_customers(
        db, tenant_id, company_id=company_id, customer_id=customer_id
    )
    if not customers:
        return None
    customer = customers[0]
    invoices = await _load_invoices(db, tenant_id)
    payments = await _load_payments(db, tenant_id)
    now = _now()
    summary = _build_balance(customer, invoices, payments, now)

    invoice_lines = [
        _build_invoice_line(inv, payments, now)
        for inv in invoices
        if inv.customer_id is not None
        and str(inv.customer_id) == str(customer.id)
        and invoice_affects_receivable(inv)
    ]
    invoice_lines.sort(key=lambda r: _aware(r.issue_date), reverse=True)

    payment_lines = [
        CurrentAccountPaymentLine(
            payment_id=pay.id,
            payment_date=pay.payment_date,
            amount=_money(_as_decimal(pay.amount)),
            currency=pay.currency,
            payment_method=pay.payment_method,
            reference=pay.reference,
            status=pay.status,
            invoice_id=pay.invoice_id,
        )
        for pay in payments
        if pay.customer_id is not None and str(pay.customer_id) == str(customer.id)
    ]
    payment_lines.sort(key=lambda r: _aware(r.payment_date), reverse=True)

    return CurrentAccountStatement(
        **summary.model_dump(),
        invoices=invoice_lines,
        payments=payment_lines,
    )


async def sync_invoice_payment_status(
    db: AsyncSession,
    invoice_id: Optional[UUID],
    tenant_id: UUID,
) -> Optional[Invoice]:
    """Mark invoice paid when cobros cubren el total; reopen if they no longer do."""
    if invoice_id is None:
        return None
    stmt = select(Invoice).where(Invoice.id == invoice_id, Invoice.tenant_id == tenant_id)
    result = await db.execute(stmt)
    invoice = result.scalar_one_or_none()
    if not invoice:
        return None
    status_value = (invoice.status or "").strip().lower()
    if status_value in SKIP_INVOICE_STATUS_SYNC:
        return invoice

    pay_stmt = select(Payment).where(Payment.tenant_id == tenant_id)
    pay_result = await db.execute(pay_stmt)
    payments = list(pay_result.scalars().all())
    paid = _payments_for_invoice(payments, invoice.id)
    total = _as_decimal(invoice.total)
    remaining = total - paid
    epsilon = Decimal("0.01")

    if remaining <= epsilon:
        if status_value != INVOICE_PAID_STATUS:
            invoice.status = INVOICE_PAID_STATUS
    elif status_value == INVOICE_PAID_STATUS:
        invoice.status = INVOICE_OPEN_STATUS
    return invoice


async def resolve_payment_customer(
    db: AsyncSession,
    tenant_id: UUID,
    invoice_id: Optional[UUID],
    customer_id: Optional[UUID],
) -> Optional[UUID]:
    if customer_id:
        return customer_id
    if not invoice_id:
        return None
    stmt = select(Invoice).where(Invoice.id == invoice_id, Invoice.tenant_id == tenant_id)
    result = await db.execute(stmt)
    invoice = result.scalar_one_or_none()
    if invoice and invoice.customer_id:
        return invoice.customer_id
    return None
