"""Unit tests for CFE XML builder and XSD validator."""

import uuid
from datetime import date, datetime, timedelta
from types import SimpleNamespace

import pytest
from lxml import etree

from app.services.fiscal.cfe_types import CFEType, get_parent_type, is_note
from app.services.fiscal.signer import sign_xml
from app.services.fiscal.xml_builder import build_cfe_xml, CFE_NAMESPACE
from app.services.fiscal.xsd_validator import (
    DEFAULT_XSD_PATH,
    validate_cfe_xml,
    validate_cfe_xml_or_raise,
    CFEValidationError,
)

DEFAULT_CAE = {
    "cae_id": 90000000001,
    "d_nro": 1,
    "h_nro": 9999999,
    "fec_venc": date(2026, 12, 31),
}


def _sign_test_xml(xml_bytes: bytes) -> bytes:
    from cryptography import x509
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.x509.oid import NameOID

    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    subject = issuer = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "Test CFE")])
    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.utcnow())
        .not_valid_after(datetime.utcnow() + timedelta(days=1))
        .sign(key, hashes.SHA256())
    )
    cert_data = cert.public_bytes(serialization.Encoding.PEM)
    return sign_xml(xml_bytes, key, cert, cert_data)


def _make_invoice(**overrides):
    defaults = dict(
        id=uuid.uuid4(),
        document_type=CFEType.E_FACTURA,
        series="A",
        number="00000001",
        issue_date=datetime(2024, 1, 15, 10, 0, 0),
        currency="UYU",
        exchange_rate=1.0,
        notes="Nota de prueba",
        metadata_json={},
    )
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def _make_company():
    return SimpleNamespace(
        rut="123456789012",
        legal_name="Empresa Demo SA",
        trade_name="Demo",
        email="demo@example.com",
        phone="+59812345678",
        fiscal_address="Av. Demo 123",
        locality="Montevideo",
        department="Montevideo",
        dgi_branch_code=1,
        metadata_json={},
    )


def _make_customer():
    return SimpleNamespace(
        rut="987654321098",
        legal_name="Cliente Demo SA",
        email="cliente@example.com",
        address="Calle Cliente 456",
    )


def _make_item(**overrides):
    defaults = dict(
        product_id=uuid.uuid4(),
        quantity=2,
        unit_price=100.0,
        discount=0.0,
        tax_amount=44.0,
        total=244.0,
        description="Producto demo",
    )
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


@pytest.fixture
def sample_cfe_xml():
    return build_cfe_xml(
        invoice=_make_invoice(),
        company=_make_company(),
        customer=_make_customer(),
        items=[_make_item()],
        document_type=CFEType.E_FACTURA,
        cfe_number="A00000001",
        issue_date=date(2024, 1, 15),
        currency="UYU",
        notes="Nota de prueba",
        cae_data=DEFAULT_CAE,
    )


def test_build_cfe_xml_produces_valid_structure(sample_cfe_xml):
    root = etree.fromstring(sample_cfe_xml)
    assert etree.QName(root).localname == "CFE"
    assert etree.QName(root).namespace == CFE_NAMESPACE
    assert root.get("version") == "1.0"

    e_fact = root.find(f"{{{CFE_NAMESPACE}}}eFact")
    assert e_fact is not None

    tipo_cfe = e_fact.find(f".//{{{CFE_NAMESPACE}}}TipoCFE")
    assert tipo_cfe is not None
    assert tipo_cfe.text == "111"


def test_build_cfe_xml_requires_customer_rut_for_efactura():
    with pytest.raises(ValueError, match="Customer RUT"):
        build_cfe_xml(
            invoice=_make_invoice(),
            company=_make_company(),
            customer=SimpleNamespace(legal_name="Sin RUT"),
            items=[_make_item()],
            document_type=CFEType.E_FACTURA,
            cfe_number="A00000001",
            issue_date=date(2024, 1, 15),
            cae_data=DEFAULT_CAE,
        )


def test_build_cfe_xml_allows_eticket_without_rut():
    xml = build_cfe_xml(
        invoice=_make_invoice(document_type=CFEType.E_TICKET, series="A", number="00000002"),
        company=_make_company(),
        customer=SimpleNamespace(legal_name="Consumidor Final"),
        items=[_make_item()],
        document_type=CFEType.E_TICKET,
        cfe_number="A00000002",
        issue_date=date(2024, 1, 15),
        cae_data=DEFAULT_CAE,
    )
    errors = validate_cfe_xml(xml, validate_xsd=False)
    assert errors == []


def test_structural_validation_passes(sample_cfe_xml):
    errors = validate_cfe_xml(sample_cfe_xml, validate_xsd=False)
    assert errors == []


def test_structural_validation_fails_on_invalid_xml():
    errors = validate_cfe_xml(b"<not-xml", validate_xsd=False)
    assert any("mal formado" in e.lower() or "XML" in e for e in errors)


def test_structural_validation_fails_on_wrong_root(sample_cfe_xml):
    root = etree.fromstring(sample_cfe_xml)
    root.tag = "Wrong"
    errors = validate_cfe_xml(etree.tostring(root), validate_xsd=False)
    assert any("CFE" in e for e in errors)


def test_validate_or_raise_raises(sample_cfe_xml):
    validate_cfe_xml_or_raise(sample_cfe_xml, validate_xsd=False)


def test_validate_or_raise_on_bad_xml():
    with pytest.raises(CFEValidationError):
        validate_cfe_xml_or_raise(b"<broken", validate_xsd=False)


@pytest.mark.skipif(not DEFAULT_XSD_PATH.exists(), reason="Official XSD not in evidence/")
def test_official_xsd_present():
    assert DEFAULT_XSD_PATH.name == "CFEDGI.xsd"


@pytest.mark.skipif(not DEFAULT_XSD_PATH.exists(), reason="Official XSD not in evidence/")
def test_builder_xml_passes_official_xsd(sample_cfe_xml):
    signed_xml = _sign_test_xml(sample_cfe_xml)
    errors = validate_cfe_xml(signed_xml, validate_xsd=True)
    assert errors == []


@pytest.mark.parametrize(
    "document_type,body_tag,requires_rut",
    [
        (CFEType.E_FACTURA, "eFact", True),
        (CFEType.E_TICKET, "eTck", False),
        (CFEType.NOTA_CREDITO_E_FACTURA, "eFact", True),
        (CFEType.NOTA_DEBITO_E_TICKET, "eTck", False),
        (CFEType.E_FACTURA_CONTINGENCIA, "eFact", True),
        (CFEType.E_TICKET_CONTINGENCIA, "eTck", False),
        (CFEType.NOTA_CREDITO_E_FACTURA_CONTINGENCIA, "eFact", True),
        (CFEType.NOTA_DEBITO_E_TICKET_CONTINGENCIA, "eTck", False),
    ],
)
def test_build_all_primary_cfe_types(document_type, body_tag, requires_rut):
    customer = _make_customer() if requires_rut else SimpleNamespace(legal_name="Consumidor Final")
    reference_document = None
    if is_note(document_type):
        reference_document = {
            "document_type": get_parent_type(document_type),
            "series": "A",
            "number": "00000001",
            "issue_date": date(2024, 1, 10),
            "reason": "Ajuste",
        }

    xml = build_cfe_xml(
        invoice=_make_invoice(document_type=document_type),
        company=_make_company(),
        customer=customer,
        items=[_make_item()],
        document_type=document_type,
        cfe_number="A00000099",
        issue_date=date(2024, 1, 15),
        cae_data=DEFAULT_CAE,
        reference_document=reference_document,
    )

    root = etree.fromstring(xml)
    body = root.find(f"{{{CFE_NAMESPACE}}}{body_tag}")
    assert body is not None

    tipo_cfe = body.find(f".//{{{CFE_NAMESPACE}}}TipoCFE")
    assert tipo_cfe is not None
    assert tipo_cfe.text == str(getattr(document_type, "value", document_type))

    errors = validate_cfe_xml(xml, validate_xsd=False)
    assert errors == []

    signed_xml = _sign_test_xml(xml)
    xsd_errors = validate_cfe_xml(signed_xml, validate_xsd=True)
    assert xsd_errors == []
