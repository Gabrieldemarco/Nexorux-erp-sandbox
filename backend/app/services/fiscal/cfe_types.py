from enum import Enum
from typing import Dict, Optional, Set


class CFEType(str, Enum):
    E_FACTURA = "111"
    E_TICKET = "101"
    NOTA_CREDITO_E_FACTURA = "112"
    NOTA_DEBITO_E_FACTURA = "113"
    NOTA_CREDITO_E_TICKET = "102"
    NOTA_DEBITO_E_TICKET = "103"
    E_TICKET_CONTINGENCIA = "201"
    NOTA_CREDITO_E_TICKET_CONTINGENCIA = "202"
    NOTA_DEBITO_E_TICKET_CONTINGENCIA = "203"
    E_FACTURA_CONTINGENCIA = "211"
    NOTA_CREDITO_E_FACTURA_CONTINGENCIA = "212"
    NOTA_DEBITO_E_FACTURA_CONTINGENCIA = "213"


CFE_TYPE_INFO: Dict[str, Dict] = {
    CFEType.E_FACTURA: {
        "code": CFEType.E_FACTURA,
        "name": "e-Factura",
        "description": "Factura electrónica para ventas a contribuyentes identificados (B2B)",
        "requires_receptor_rut": True,
        "allows_credit_fiscal": True,
        "credit_note_type": CFEType.NOTA_CREDITO_E_FACTURA,
        "debit_note_type": CFEType.NOTA_DEBITO_E_FACTURA,
    },
    CFEType.E_TICKET: {
        "code": CFEType.E_TICKET,
        "name": "e-Ticket",
        "description": "Ticket electrónico para ventas a consumidor final (B2C)",
        "requires_receptor_rut": False,
        "allows_credit_fiscal": False,
        "credit_note_type": CFEType.NOTA_CREDITO_E_TICKET,
        "debit_note_type": CFEType.NOTA_DEBITO_E_TICKET,
    },
    CFEType.NOTA_CREDITO_E_FACTURA: {
        "code": CFEType.NOTA_CREDITO_E_FACTURA,
        "name": "Nota de Crédito e-Factura",
        "description": "Ajuste/devolución sobre e-Factura",
        "requires_receptor_rut": True,
        "allows_credit_fiscal": True,
        "credit_note_type": None,
        "debit_note_type": None,
    },
    CFEType.NOTA_DEBITO_E_FACTURA: {
        "code": CFEType.NOTA_DEBITO_E_FACTURA,
        "name": "Nota de Débito e-Factura",
        "description": "Cargo adicional sobre e-Factura",
        "requires_receptor_rut": True,
        "allows_credit_fiscal": True,
        "credit_note_type": None,
        "debit_note_type": None,
    },
    CFEType.NOTA_CREDITO_E_TICKET: {
        "code": CFEType.NOTA_CREDITO_E_TICKET,
        "name": "Nota de Crédito e-Ticket",
        "description": "Ajuste/devolución sobre e-Ticket",
        "requires_receptor_rut": False,
        "allows_credit_fiscal": False,
        "credit_note_type": None,
        "debit_note_type": None,
    },
    CFEType.NOTA_DEBITO_E_TICKET: {
        "code": CFEType.NOTA_DEBITO_E_TICKET,
        "name": "Nota de Débito e-Ticket",
        "description": "Cargo adicional sobre e-Ticket",
        "requires_receptor_rut": False,
        "allows_credit_fiscal": False,
        "credit_note_type": None,
        "debit_note_type": None,
    },
    CFEType.E_TICKET_CONTINGENCIA: {
        "code": CFEType.E_TICKET_CONTINGENCIA,
        "name": "e-Ticket Contingencia",
        "description": "Ticket electrónico emitido en régimen de contingencia",
        "requires_receptor_rut": False,
        "allows_credit_fiscal": False,
        "credit_note_type": CFEType.NOTA_CREDITO_E_TICKET_CONTINGENCIA,
        "debit_note_type": CFEType.NOTA_DEBITO_E_TICKET_CONTINGENCIA,
    },
    CFEType.NOTA_CREDITO_E_TICKET_CONTINGENCIA: {
        "code": CFEType.NOTA_CREDITO_E_TICKET_CONTINGENCIA,
        "name": "Nota de Crédito e-Ticket Contingencia",
        "description": "Ajuste/devolución sobre e-Ticket en contingencia",
        "requires_receptor_rut": False,
        "allows_credit_fiscal": False,
        "credit_note_type": None,
        "debit_note_type": None,
    },
    CFEType.NOTA_DEBITO_E_TICKET_CONTINGENCIA: {
        "code": CFEType.NOTA_DEBITO_E_TICKET_CONTINGENCIA,
        "name": "Nota de Débito e-Ticket Contingencia",
        "description": "Cargo adicional sobre e-Ticket en contingencia",
        "requires_receptor_rut": False,
        "allows_credit_fiscal": False,
        "credit_note_type": None,
        "debit_note_type": None,
    },
    CFEType.E_FACTURA_CONTINGENCIA: {
        "code": CFEType.E_FACTURA_CONTINGENCIA,
        "name": "e-Factura Contingencia",
        "description": "Factura electrónica emitida en régimen de contingencia",
        "requires_receptor_rut": True,
        "allows_credit_fiscal": True,
        "credit_note_type": CFEType.NOTA_CREDITO_E_FACTURA_CONTINGENCIA,
        "debit_note_type": CFEType.NOTA_DEBITO_E_FACTURA_CONTINGENCIA,
    },
    CFEType.NOTA_CREDITO_E_FACTURA_CONTINGENCIA: {
        "code": CFEType.NOTA_CREDITO_E_FACTURA_CONTINGENCIA,
        "name": "Nota de Crédito e-Factura Contingencia",
        "description": "Ajuste/devolución sobre e-Factura en contingencia",
        "requires_receptor_rut": True,
        "allows_credit_fiscal": True,
        "credit_note_type": None,
        "debit_note_type": None,
    },
    CFEType.NOTA_DEBITO_E_FACTURA_CONTINGENCIA: {
        "code": CFEType.NOTA_DEBITO_E_FACTURA_CONTINGENCIA,
        "name": "Nota de Débito e-Factura Contingencia",
        "description": "Cargo adicional sobre e-Factura en contingencia",
        "requires_receptor_rut": True,
        "allows_credit_fiscal": True,
        "credit_note_type": None,
        "debit_note_type": None,
    },
}

CFE_TYPE_CODES: Set[str] = set(CFE_TYPE_INFO.keys())
CREDIT_NOTE_TYPES: Set[str] = {
    CFEType.NOTA_CREDITO_E_FACTURA,
    CFEType.NOTA_CREDITO_E_TICKET,
    CFEType.NOTA_CREDITO_E_TICKET_CONTINGENCIA,
    CFEType.NOTA_CREDITO_E_FACTURA_CONTINGENCIA,
}
DEBIT_NOTE_TYPES: Set[str] = {
    CFEType.NOTA_DEBITO_E_FACTURA,
    CFEType.NOTA_DEBITO_E_TICKET,
    CFEType.NOTA_DEBITO_E_TICKET_CONTINGENCIA,
    CFEType.NOTA_DEBITO_E_FACTURA_CONTINGENCIA,
}
CONTINGENCY_TYPE_MAP: Dict[str, str] = {
    CFEType.E_TICKET: CFEType.E_TICKET_CONTINGENCIA,
    CFEType.NOTA_CREDITO_E_TICKET: CFEType.NOTA_CREDITO_E_TICKET_CONTINGENCIA,
    CFEType.NOTA_DEBITO_E_TICKET: CFEType.NOTA_DEBITO_E_TICKET_CONTINGENCIA,
    CFEType.E_FACTURA: CFEType.E_FACTURA_CONTINGENCIA,
    CFEType.NOTA_CREDITO_E_FACTURA: CFEType.NOTA_CREDITO_E_FACTURA_CONTINGENCIA,
    CFEType.NOTA_DEBITO_E_FACTURA: CFEType.NOTA_DEBITO_E_FACTURA_CONTINGENCIA,
}
CONTINGENCY_TYPES: Set[str] = set(CONTINGENCY_TYPE_MAP.values())

def is_credit_note(document_type: str) -> bool:
    return document_type in CREDIT_NOTE_TYPES

def is_debit_note(document_type: str) -> bool:
    return document_type in DEBIT_NOTE_TYPES

def is_note(document_type: str) -> bool:
    return is_credit_note(document_type) or is_debit_note(document_type)

def is_contingency_type(document_type: str) -> bool:
    return document_type in CONTINGENCY_TYPES


def to_contingency_type(document_type: str) -> str:
    return CONTINGENCY_TYPE_MAP.get(document_type, document_type)


def resolve_document_type(document_type: str, *, is_contingency: bool = False) -> str:
    if is_contingency and not is_contingency_type(document_type):
        return to_contingency_type(document_type)
    return document_type


def get_parent_type(document_type: str) -> Optional[str]:
    parents = {
        CFEType.NOTA_CREDITO_E_FACTURA: CFEType.E_FACTURA,
        CFEType.NOTA_DEBITO_E_FACTURA: CFEType.E_FACTURA,
        CFEType.NOTA_CREDITO_E_TICKET: CFEType.E_TICKET,
        CFEType.NOTA_DEBITO_E_TICKET: CFEType.E_TICKET,
        CFEType.NOTA_CREDITO_E_FACTURA_CONTINGENCIA: CFEType.E_FACTURA_CONTINGENCIA,
        CFEType.NOTA_DEBITO_E_FACTURA_CONTINGENCIA: CFEType.E_FACTURA_CONTINGENCIA,
        CFEType.NOTA_CREDITO_E_TICKET_CONTINGENCIA: CFEType.E_TICKET_CONTINGENCIA,
        CFEType.NOTA_DEBITO_E_TICKET_CONTINGENCIA: CFEType.E_TICKET_CONTINGENCIA,
    }
    return parents.get(document_type)
