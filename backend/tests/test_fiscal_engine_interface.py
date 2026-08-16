"""
Pruebas unitarias para la interfaz IFiscalEngine.

Estas pruebas validan que cualquier implementación de IFiscalEngine
cumpla con el contrato establecido, garantizando el desacoplamiento.
"""

import pytest
from unittest.mock import Mock, AsyncMock
from datetime import date, datetime
from decimal import Decimal

from app.services.fiscal.engines.base import (
    IFiscalEngine,
    FiscalEngineError,
    ValidationError,
    DocumentNotFoundError,
    TransmissionError
)
from app.services.fiscal.models import (
    FiscalDocumentData,
    FiscalDocumentResponse,
    FiscalEngineCapabilities,
    FiscalCompany,
    FiscalCustomer,
    FiscalDocumentItem
)


class MockFiscalEngine(IFiscalEngine):
    """Motor fiscal mock para pruebas."""
    
    def __init__(self):
        self.validate_called = False
        self.issue_called = False
        self.send_called = False
        self.query_called = False
        self.cancel_called = False
        self.health_check_called = False
    
    @property
    def engine_info(self) -> FiscalEngineCapabilities:
        return FiscalEngineCapabilities(
            engine_id="mock_engine",
            engine_name="Mock Fiscal Engine",
            country="XX",
            fiscal_authority="Mock Authority",
            version="1.0",
            supports_electronic_invoice=True,
            supports_credit_note=True,
            supports_debit_note=True,
            supports_contingency=False,
            supports_cancellation=False,
            supports_query_status=True,
            supported_document_types=["invoice", "credit_note", "debit_note"]
        )
    
    async def validate_document(self, document_data: dict) -> FiscalDocumentResponse:
        self.validate_called = True
        return FiscalDocumentResponse(
            success=True,
            engine_used="mock_engine",
            operation="validate"
        )
    
    async def issue_document(self, document_data: dict) -> FiscalDocumentResponse:
        self.issue_called = True
        return FiscalDocumentResponse(
            success=True,
            document_type=document_data.get("document_type"),
            series=document_data.get("series"),
            number=document_data.get("number"),
            generated_xml="<mock>xml</mock>",
            signed_xml="<mock>signed_xml</mock>",
            status="ready_to_send",
            engine_used="mock_engine",
            operation="issue"
        )
    
    async def send_document(self, document_data: dict) -> FiscalDocumentResponse:
        self.send_called = True
        return FiscalDocumentResponse(
            success=True,
            status="accepted",
            engine_response={"status": "accepted"},
            engine_used="mock_engine",
            operation="send"
        )
    
    async def query_status(self, document_data: dict) -> FiscalDocumentResponse:
        self.query_called = True
        return FiscalDocumentResponse(
            success=True,
            engine_response={"status": "accepted"},
            engine_used="mock_engine",
            operation="query"
        )
    
    async def cancel_document(self, document_data: dict) -> FiscalDocumentResponse:
        self.cancel_called = True
        raise FiscalEngineError("Cancellation not implemented")
    
    async def health_check(self) -> dict:
        self.health_check_called = True
        return {
            "healthy": True,
            "engine_id": "mock_engine",
            "message": "Mock engine is healthy"
        }


class TestIFiscalEngine:
    """Pruebas para la interfaz IFiscalEngine."""
    
    @pytest.fixture
    def mock_engine(self):
        """Fixture que proporciona un motor fiscal mock."""
        return MockFiscalEngine()
    
    @pytest.fixture
    def sample_document_data(self):
        """Fixture que proporciona datos de documento fiscal de ejemplo."""
        return {
            "document_type": "invoice",
            "series": "A",
            "number": "001",
            "issue_date": date.today(),
            "company": {
                "rut": "123456789012",
                "legal_name": "Test Company"
            },
            "items": [
                {
                    "description": "Test Item",
                    "quantity": Decimal("1"),
                    "unit_price": Decimal("100")
                }
            ],
            "currency": "UYU",
            "subtotal": Decimal("100"),
            "tax_total": Decimal("22"),
            "total": Decimal("122")
        }
    
    def test_engine_info_returns_correct_capabilities(self, mock_engine):
        """Test que engine_info retorna capacidades correctas."""
        info = mock_engine.engine_info
        
        assert info.engine_id == "mock_engine"
        assert info.engine_name == "Mock Fiscal Engine"
        assert info.country == "XX"
        assert info.fiscal_authority == "Mock Authority"
        assert info.supports_electronic_invoice is True
        assert info.supports_credit_note is True
        assert info.supports_query_status is True
    
    @pytest.mark.asyncio
    async def test_validate_document_success(self, mock_engine, sample_document_data):
        """Test que validate_document funciona correctamente."""
        response = await mock_engine.validate_document(sample_document_data)
        
        assert response.success is True
        assert response.engine_used == "mock_engine"
        assert response.operation == "validate"
        assert mock_engine.validate_called is True
    
    @pytest.mark.asyncio
    async def test_issue_document_success(self, mock_engine, sample_document_data):
        """Test que issue_document genera documento correctamente."""
        response = await mock_engine.issue_document(sample_document_data)
        
        assert response.success is True
        assert response.document_type == "invoice"
        assert response.series == "A"
        assert response.number == "001"
        assert response.generated_xml == "<mock>xml</mock>"
        assert response.signed_xml == "<mock>signed_xml</mock>"
        assert response.status == "ready_to_send"
        assert mock_engine.issue_called is True
    
    @pytest.mark.asyncio
    async def test_send_document_success(self, mock_engine):
        """Test que send_document envía documento correctamente."""
        document_data = {
            "signed_xml": "<mock>signed_xml</mock>",
            "document_type": "invoice",
            "series": "A",
            "number": "001"
        }
        
        response = await mock_engine.send_document(document_data)
        
        assert response.success is True
        assert response.status == "accepted"
        assert response.engine_response == {"status": "accepted"}
        assert mock_engine.send_called is True
    
    @pytest.mark.asyncio
    async def test_query_status_success(self, mock_engine):
        """Test que query_status consulta estado correctamente."""
        document_data = {
            "rut": "123456789012",
            "cfe_type": "111",
            "cfe_number": "A001",
            "issue_date": "2026-08-15"
        }
        
        response = await mock_engine.query_status(document_data)
        
        assert response.success is True
        assert response.engine_response == {"status": "accepted"}
        assert mock_engine.query_called is True
    
    @pytest.mark.asyncio
    async def test_cancel_document_not_implemented(self, mock_engine):
        """Test que cancel_document lanza error cuando no está implementado."""
        with pytest.raises(FiscalEngineError):
            await mock_engine.cancel_document({})
        
        assert mock_engine.cancel_called is True
    
    @pytest.mark.asyncio
    async def test_health_check_success(self, mock_engine):
        """Test que health_check retorna estado correcto."""
        health = await mock_engine.health_check()
        
        assert health["healthy"] is True
        assert health["engine_id"] == "mock_engine"
        assert health["message"] == "Mock engine is healthy"
        assert mock_engine.health_check_called is True
    
    def test_get_supported_document_types(self, mock_engine):
        """Test que get_supported_document_types retorna tipos correctos."""
        types = mock_engine.get_supported_document_types()
        
        assert "invoice" in types
        assert "credit_note" in types
        assert "debit_note" in types
        assert len(types) == 3
    
    def test_supports_document_type(self, mock_engine):
        """Test que supports_document_type valida correctamente."""
        assert mock_engine.supports_document_type("invoice") is True
        assert mock_engine.supports_document_type("credit_note") is True
        assert mock_engine.supports_document_type("unknown") is False
    
    def test_supports_operation(self, mock_engine):
        """Test que supports_operation valida capacidades correctamente."""
        assert mock_engine.supports_operation("issue") is True
        assert mock_engine.supports_operation("send") is True
        assert mock_engine.supports_operation("query") is True
        assert mock_engine.supports_operation("cancel") is False
        assert mock_engine.supports_operation("contingency") is False


class TestFiscalDocumentData:
    """Pruebas para el modelo FiscalDocumentData."""
    
    def test_fiscal_document_data_validation(self):
        """Test que FiscalDocumentData valida correctamente."""
        company = FiscalCompany(
            rut="123456789012",
            legal_name="Test Company"
        )
        item = FiscalDocumentItem(
            description="Test Item",
            quantity=Decimal("1"),
            unit_price=Decimal("100")
        )
        
        doc_data = FiscalDocumentData(
            document_type="invoice",
            series="A",
            number="001",
            issue_date=date.today(),
            company=company,
            items=[item],
            currency="UYU",
            subtotal=Decimal("100"),
            tax_total=Decimal("22"),
            total=Decimal("122")
        )
        
        assert doc_data.document_type == "invoice"
        assert doc_data.series == "A"
        assert doc_data.number == "001"
        assert len(doc_data.items) == 1
        assert doc_data.total == Decimal("122")
    
    def test_fiscal_document_data_with_customer(self):
        """Test que FiscalDocumentData acepta cliente opcional."""
        company = FiscalCompany(rut="123456789012", legal_name="Test Company")
        customer = FiscalCustomer(rut="987654321012", legal_name="Test Customer")
        item = FiscalDocumentItem(
            description="Test Item",
            quantity=Decimal("1"),
            unit_price=Decimal("100")
        )
        
        doc_data = FiscalDocumentData(
            document_type="invoice",
            series="A",
            number="001",
            issue_date=date.today(),
            company=company,
            customer=customer,
            items=[item],
            currency="UYU",
            subtotal=Decimal("100"),
            tax_total=Decimal("22"),
            total=Decimal("122")
        )
        
        assert doc_data.customer is not None
        assert doc_data.customer.legal_name == "Test Customer"
    
    def test_fiscal_document_data_validation_errors(self):
        """Test que FiscalDocumentData lanza errores de validación."""
        company = FiscalCompany(rut="123456789012", legal_name="Test Company")
        
        # Falta required field
        with pytest.raises(Exception):  # Pydantic validation error
            FiscalDocumentData(
                document_type="invoice",
                # series faltante
                number="001",
                issue_date=date.today(),
                company=company,
                items=[],  # items vacíos
                currency="UYU",
                subtotal=Decimal("100"),
                tax_total=Decimal("22"),
                total=Decimal("122")
            )


class TestFiscalEngineCapabilities:
    """Pruebas para el modelo FiscalEngineCapabilities."""
    
    def test_engine_capabilities_structure(self):
        """Test que FiscalEngineCapabilities tiene estructura correcta."""
        capabilities = FiscalEngineCapabilities(
            engine_id="test_engine",
            engine_name="Test Engine",
            country="UY",
            fiscal_authority="Test Authority",
            version="1.0",
            supports_electronic_invoice=True,
            supports_credit_note=True,
            supports_debit_note=True,
            supports_contingency=False,
            supports_cancellation=False,
            supports_query_status=True,
            supported_document_types=["invoice", "credit_note"]
        )
        
        assert capabilities.engine_id == "test_engine"
        assert capabilities.supports_electronic_invoice is True
        assert capabilities.supports_contingency is False
        assert len(capabilities.supported_document_types) == 2
    
    def test_engine_capabilities_default_values(self):
        """Test que FiscalEngineCapabilities tiene defaults correctos."""
        capabilities = FiscalEngineCapabilities(
            engine_id="test_engine",
            engine_name="Test Engine",
            country="UY",
            fiscal_authority="Test Authority",
            version="1.0"
        )
        
        # Verificar defaults
        assert capabilities.supports_electronic_invoice is False
        assert capabilities.supports_credit_note is False
        assert capabilities.supports_query_status is False
        assert capabilities.supported_document_types == []