"""Tax configuration schema must not bind SQLAlchemy MetaData via alias 'metadata'."""

import uuid
from datetime import datetime, timezone
from decimal import Decimal

from app.models.tax_configuration import TaxConfiguration
from app.schemas.tax_configuration import TaxConfigurationCreate, TaxConfigurationResponse


def test_tax_configuration_response_from_orm():
    row = TaxConfiguration(
        tenant_id=uuid.uuid4(),
        company_id=uuid.uuid4(),
        tax_code="IVA",
        description="IVA 22%",
        rate=Decimal("22.00"),
        effective_from=datetime.now(timezone.utc),
        metadata_json={"source": "test"},
    )
    row.id = uuid.uuid4()
    row.created_at = datetime.now(timezone.utc)
    row.updated_at = datetime.now(timezone.utc)

    parsed = TaxConfigurationResponse.model_validate(row)
    assert parsed.tax_code == "IVA"
    assert parsed.metadata == {"source": "test"}


def test_tax_configuration_create_allows_missing_effective_from():
    payload = TaxConfigurationCreate.model_validate(
        {
            "tax_code": "ivab",
            "rate": 10,
            "tenant_id": str(uuid.uuid4()),
            "company_id": str(uuid.uuid4()),
        }
    )
    assert payload.effective_from is None
    assert payload.tax_code == "ivab"
