"""Catalog tests — catalogs drive UI labels and stock rules."""

from app.core.catalog import INVOICE_STATUSES, build_catalog, credit_note_type_for
from app.services.inventory import STOCK_AFFECTING_STATUSES


def test_catalog_has_spanish_invoice_statuses():
    catalog = build_catalog()
    values = {row["value"]: row["label"] for row in catalog["invoice_statuses"]}
    assert values["draft"] == "Borrador"
    assert values["paid"] == "Pagada"
    assert values["cancelled"] == "Anulada"
    assert catalog["currency"] == "UYU"
    assert catalog["defaults"]["pos_document_type"] == "101"


def test_credit_note_mapping_from_cfe_catalog():
    assert credit_note_type_for("101") == "102"
    assert credit_note_type_for("111") == "112"
    assert credit_note_type_for("102") is None


def test_stock_statuses_come_from_catalog():
    expected = {row["value"] for row in INVOICE_STATUSES if row["affects_stock"]}
    assert STOCK_AFFECTING_STATUSES == expected
    assert "draft" not in STOCK_AFFECTING_STATUSES
    assert "paid" in STOCK_AFFECTING_STATUSES
    assert catalog_receivable()


def catalog_receivable():
    catalog = build_catalog()
    issued = next(r for r in catalog["invoice_statuses"] if r["value"] == "issued")
    draft = next(r for r in catalog["invoice_statuses"] if r["value"] == "draft")
    assert issued["affects_receivable"] is True
    assert draft["affects_receivable"] is False
    completed = next(r for r in catalog["payment_statuses"] if r["value"] == "completed")
    assert completed["counts_as_paid"] is True
    return True
