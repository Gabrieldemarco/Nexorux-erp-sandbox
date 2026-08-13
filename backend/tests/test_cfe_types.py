"""Unit tests for CFE type helpers."""

import pytest

from app.services.fiscal.cfe_types import (
    CFEType,
    CFE_TYPE_INFO,
    get_parent_type,
    is_contingency_type,
    is_credit_note,
    is_debit_note,
    is_note,
    resolve_document_type,
    to_contingency_type,
)


@pytest.mark.parametrize(
    "document_type,expected_parent",
    [
        (CFEType.NOTA_CREDITO_E_FACTURA, CFEType.E_FACTURA),
        (CFEType.NOTA_DEBITO_E_FACTURA, CFEType.E_FACTURA),
        (CFEType.NOTA_CREDITO_E_TICKET, CFEType.E_TICKET),
        (CFEType.NOTA_DEBITO_E_TICKET, CFEType.E_TICKET),
        (CFEType.NOTA_CREDITO_E_FACTURA_CONTINGENCIA, CFEType.E_FACTURA_CONTINGENCIA),
        (CFEType.NOTA_DEBITO_E_FACTURA_CONTINGENCIA, CFEType.E_FACTURA_CONTINGENCIA),
        (CFEType.NOTA_CREDITO_E_TICKET_CONTINGENCIA, CFEType.E_TICKET_CONTINGENCIA),
        (CFEType.NOTA_DEBITO_E_TICKET_CONTINGENCIA, CFEType.E_TICKET_CONTINGENCIA),
    ],
)
def test_get_parent_type_for_notes(document_type, expected_parent):
    assert get_parent_type(document_type) == expected_parent


def test_contingency_type_mapping():
    assert to_contingency_type(CFEType.E_FACTURA) == CFEType.E_FACTURA_CONTINGENCIA
    assert to_contingency_type(CFEType.E_TICKET) == CFEType.E_TICKET_CONTINGENCIA
    assert is_contingency_type(CFEType.E_FACTURA_CONTINGENCIA)


def test_resolve_document_type_applies_contingency_flag():
    assert resolve_document_type(CFEType.E_FACTURA, is_contingency=True) == CFEType.E_FACTURA_CONTINGENCIA
    assert resolve_document_type(CFEType.E_FACTURA_CONTINGENCIA, is_contingency=True) == CFEType.E_FACTURA_CONTINGENCIA


@pytest.mark.parametrize("cfe_type", list(CFE_TYPE_INFO.keys()))
def test_all_cfe_types_have_metadata(cfe_type):
    info = CFE_TYPE_INFO[cfe_type]
    assert info["code"] == cfe_type
    assert info["name"]
    assert "requires_receptor_rut" in info


def test_note_classification():
    assert is_note(CFEType.NOTA_CREDITO_E_FACTURA)
    assert is_credit_note(CFEType.NOTA_CREDITO_E_TICKET_CONTINGENCIA)
    assert is_debit_note(CFEType.NOTA_DEBITO_E_FACTURA_CONTINGENCIA)
    assert not is_note(CFEType.E_FACTURA)
