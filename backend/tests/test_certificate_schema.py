"""Certificate schema must not bind SQLAlchemy MetaData via alias 'metadata'."""

import uuid
from datetime import datetime, timezone

from app.models.certificate import Certificate
from app.schemas.certificate import CertificateCreate, CertificateResponse


def test_certificate_response_from_orm_ignores_sqlalchemy_metadata():
    cert = Certificate(
        tenant_id=uuid.uuid4(),
        company_id=uuid.uuid4(),
        name="Firma DGI",
        thumbprint="ABC123",
        usage="signing",
        is_active=True,
        metadata_json={"cert_path": "/certs/dgi.pem", "key_path": "/certs/dgi.key"},
    )
    cert.id = uuid.uuid4()
    cert.created_at = datetime.now(timezone.utc)
    cert.updated_at = datetime.now(timezone.utc)

    # SQLAlchemy exposes class/instance .metadata as MetaData — must not be used as JSON.
    assert cert.metadata_json["cert_path"] == "/certs/dgi.pem"
    assert not isinstance(cert.metadata_json, type(Certificate.metadata))

    parsed = CertificateResponse.model_validate(cert)
    assert parsed.name == "Firma DGI"
    assert parsed.metadata == {"cert_path": "/certs/dgi.pem", "key_path": "/certs/dgi.key"}


def test_certificate_create_accepts_metadata_key():
    payload = CertificateCreate.model_validate(
        {
            "name": "Firma",
            "thumbprint": "TP1",
            "tenant_id": str(uuid.uuid4()),
            "company_id": str(uuid.uuid4()),
            "metadata": {"cert_path": "a.pem"},
        }
    )
    assert payload.metadata == {"cert_path": "a.pem"}
