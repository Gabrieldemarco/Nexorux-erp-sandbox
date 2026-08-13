"""Catalog of functional codes for the ERP UI (Uruguay / DGI).

Internal codes stay English/numeric for API + DGI. Labels are Spanish.
"""

from typing import Dict, List, Optional

from app.services.fiscal.cfe_types import CFE_TYPE_INFO, CFEType, is_credit_note
from app.services.fiscal.state_machine import FiscalState

INVOICE_STATUSES: List[Dict[str, object]] = [
    {"value": "draft", "label": "Borrador", "affects_stock": False, "affects_receivable": False, "allows_credit_note": True},
    {"value": "issued", "label": "Emitida", "affects_stock": True, "affects_receivable": True, "allows_credit_note": True},
    {"value": "paid", "label": "Pagada", "affects_stock": True, "affects_receivable": True, "allows_credit_note": True},
    {"value": "posted", "label": "Contabilizada", "affects_stock": True, "affects_receivable": True, "allows_credit_note": False},
    {"value": "confirmed", "label": "Confirmada", "affects_stock": True, "affects_receivable": True, "allows_credit_note": False},
    {"value": "cancelled", "label": "Anulada", "affects_stock": False, "affects_receivable": False, "allows_credit_note": False},
]

PAYMENT_STATUSES: List[Dict[str, object]] = [
    {"value": "pending", "label": "Pendiente", "counts_as_paid": False},
    {"value": "completed", "label": "Completado", "counts_as_paid": True},
    {"value": "failed", "label": "Fallido", "counts_as_paid": False},
    {"value": "cancelled", "label": "Anulado", "counts_as_paid": False},
]

PAYMENT_METHODS: List[Dict[str, str]] = [
    {"value": "cash", "label": "Efectivo"},
    {"value": "transfer", "label": "Transferencia"},
    {"value": "card", "label": "Tarjeta"},
    {"value": "check", "label": "Cheque"},
    {"value": "other", "label": "Otro"},
]

TENANT_STATUSES: List[Dict[str, str]] = [
    {"value": "active", "label": "Activo"},
    {"value": "inactive", "label": "Inactivo"},
    {"value": "suspended", "label": "Suspendido"},
]

RECEIPT_STATUSES: List[Dict[str, str]] = [
    {"value": "received", "label": "Recibida"},
    {"value": "draft", "label": "Borrador"},
    {"value": "cancelled", "label": "Anulada"},
]

FISCAL_STATE_LABELS = {
    FiscalState.DRAFT.value: "Borrador",
    FiscalState.PENDING_SIGN.value: "Pendiente de firma",
    FiscalState.PENDING_SEND.value: "Pendiente de envío",
    FiscalState.SENT.value: "Enviada a DGI",
    FiscalState.ACCEPTED.value: "Aceptada por DGI",
    FiscalState.REJECTED.value: "Rechazada por DGI",
    FiscalState.CANCELLED.value: "Anulada",
}

WOO_STATUSES: List[Dict[str, str]] = [
    {"value": "pending", "label": "Pendiente"},
    {"value": "processing", "label": "En proceso"},
    {"value": "on_hold", "label": "En espera"},
    {"value": "completed", "label": "Completado"},
    {"value": "cancelled", "label": "Anulado"},
    {"value": "canceled", "label": "Anulado"},
    {"value": "refunded", "label": "Reembolsado"},
    {"value": "failed", "label": "Fallido"},
    {"value": "trash", "label": "Papelera"},
]

DEFAULT_CURRENCY = "UYU"
DEFAULT_COUNTRY = "Uruguay"
DEFAULT_INVOICE_STATUS = "draft"
DEFAULT_PAYMENT_STATUS = "pending"
POS_INVOICE_STATUS = "paid"
INVOICE_PAID_STATUS = "paid"
INVOICE_OPEN_STATUS = "issued"


def _enum_code(value) -> Optional[str]:
    if value is None:
        return None
    return str(getattr(value, "value", value))


def _cfe_rows() -> List[Dict[str, object]]:
    rows = []
    for code, info in CFE_TYPE_INFO.items():
        credit = info.get("credit_note_type")
        code_value = _enum_code(code) or ""
        rows.append(
            {
                "value": code_value,
                "label": f"{info['name']} ({code_value})",
                "name": info["name"],
                "description": info.get("description") or "",
                "requires_receptor_rut": bool(info.get("requires_receptor_rut")),
                "is_ticket": not bool(info.get("requires_receptor_rut")),
                "is_credit_note": is_credit_note(code_value),
                "credit_note_type": _enum_code(credit),
                "pos_default": code_value == CFEType.E_TICKET,
                "invoice_form": code_value
                in {
                    CFEType.E_TICKET,
                    CFEType.E_FACTURA,
                    CFEType.NOTA_CREDITO_E_TICKET,
                    CFEType.NOTA_CREDITO_E_FACTURA,
                },
            }
        )
    rows.sort(key=lambda r: r["value"])
    return rows


def build_catalog() -> Dict[str, object]:
    cfe = _cfe_rows()
    ticket = next((r for r in cfe if r.get("pos_default")), None)
    invoice_form = [r for r in cfe if r.get("invoice_form")]
    return {
        "currency": DEFAULT_CURRENCY,
        "country": DEFAULT_COUNTRY,
        "defaults": {
            "invoice_status": DEFAULT_INVOICE_STATUS,
            "payment_status": DEFAULT_PAYMENT_STATUS,
            "pos_invoice_status": POS_INVOICE_STATUS,
            "invoice_paid_status": INVOICE_PAID_STATUS,
            "invoice_open_status": INVOICE_OPEN_STATUS,
            "pos_document_type": ticket["value"] if ticket else CFEType.E_TICKET,
            "invoice_document_type": ticket["value"] if ticket else CFEType.E_TICKET,
        },
        "invoice_statuses": INVOICE_STATUSES,
        "fiscal_states": [{"value": k, "label": v} for k, v in FISCAL_STATE_LABELS.items()],
        "payment_statuses": PAYMENT_STATUSES,
        "payment_methods": PAYMENT_METHODS,
        "tenant_statuses": TENANT_STATUSES,
        "receipt_statuses": RECEIPT_STATUSES,
        "woocommerce_statuses": WOO_STATUSES,
        "document_types": cfe,
        "invoice_form_document_types": invoice_form,
    }


def credit_note_type_for(document_type: str) -> Optional[str]:
    info = CFE_TYPE_INFO.get(document_type) or {}
    return _enum_code(info.get("credit_note_type"))
