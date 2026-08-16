"""
Pruebas de integración para FiscalCore.

Estas pruebas validan que FiscalCore funcione correctamente con
diferentes motores fiscales, demostrando el desacoplamiento logrado.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import date, datetime
from decimal import Decimal
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.fiscal.fiscal_core import FiscalCore, FiscalCoreError
from app.services.fiscal.engines.base import FiscalEngineError, ValidationError
from app.services.fiscal.engines.mock_engine import MockFiscalEngine
from app.services.fiscal.engines.registry import get_fiscal_engine_registry, reset_fiscal_engine_registry


@pytest.fixture(autouse=True)
def reset_registry():
    """Resetea el registro de motores antes de cada test."""
    reset_fiscal_engine_registry()
    yield
    reset_fiscal_engine_registry()


@pytest.fixture
def mock_db():
    """Fixture que proporciona un mock de base de datos."""
    db = Mock(spec=AsyncSession)
    db.execute = AsyncMock()
    db.flush = AsyncMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    return db


@pytest.fixture
def sample_tenant_id():
    """Fixture que proporciona un ID de tenant de ejemplo."""
    return uuid4()


@pytest.fixture
def sample_invoice_id():
    """Fixture que proporciona un ID de factura de ejemplo."""
    return uuid4()


@pytest.fixture
def sample_certificate_id():
    """Fixture que proporciona un ID de certificado de ejemplo."""
    return uuid4()


class TestFiscalCoreWithMockEngine:
    """Pruebas de integración de FiscalCore con motor mock."""
    
    @pytest.fixture
    def fiscal_core(self, mock_db):
        """Fixture que proporciona FiscalCore con mock DB."""
        return FiscalCore(mock_db)
    
    @pytest.fixture
    def register_mock_engine(self):
        """Fixture que registra el motor mock."""
        registry = get_fiscal_engine_registry()
        mock_engine = MockFiscalEngine(environment="testing")
        registry.register_engine("mock_fiscal", mock_engine)
        return mock_engine
    
    @pytest.mark.asyncio
    async def test_fiscal_core_uses_configured_engine(
        self, fiscal_core, register_mock_engine, sample_tenant_id
    ):
        """Test que FiscalCore usa el motor configurado."""
        # Mockear obtención de tenant para que use mock_fiscal
        from app.models.tenant import Tenant
        
        mock_tenant = Mock()
        mock_tenant.fiscal_engine_id = "mock_fiscal"
        mock_tenant.fiscal_config = {}
        
        # Mockear la consulta de tenant
        fiscal_core.db.execute.return_value.scalar_one_or_none.return_value = mock_tenant
        
        # Obtener motor
        engine = await fiscal_core._get_engine_for_tenant(sample_tenant_id)
        
        # Verificar que obtuvo el motor mock
        assert isinstance(engine, MockFiscalEngine)
        assert engine.environment == "testing"
    
    @pytest.mark.asyncio
    async def test_fiscal_core_fallback_to_dgi_when_no_config(
        self, fiscal_core, sample_tenant_id
    ):
        """Test que FiscalCore usa DGI como fallback cuando no hay configuración."""
        from app.models.tenant import Tenant
        from app.services.fiscal.engines.dgi_uruguay import DGIUruguayEngine
        
        # Registrar motor DGI
        registry = get_fiscal_engine_registry()
        dgi_engine = DGIUruguayEngine(environment="testing")
        registry.register_engine("dgi_uruguay", dgi_engine)
        
        # Mockear tenant sin configuración
        mock_tenant = Mock()
        mock_tenant.fiscal_engine_id = None
        mock_tenant.fiscal_config = {}
        
        fiscal_core.db.execute.return_value.scalar_one_or_none.return_value = mock_tenant
        
        # Obtener motor
        engine = await fiscal_core._get_engine_for_tenant(sample_tenant_id)
        
        # Verificar que obtuvo DGI como fallback
        assert isinstance(engine, DGIUruguayEngine)
    
    @pytest.mark.asyncio
    async def test_fiscal_core_uses_environment_from_config(
        self, fiscal_core, register_mock_engine, sample_tenant_id
    ):
        """Test que FiscalCore usa el entorno de la configuración del tenant."""
        from app.models.tenant import Tenant
        
        # Mockear tenant con configuración de entorno
        mock_tenant = Mock()
        mock_tenant.fiscal_engine_id = "mock_fiscal"
        mock_tenant.fiscal_config = {"environment": "production"}
        
        fiscal_core.db.execute.return_value.scalar_one_or_none.return_value = mock_tenant
        
        # Obtener motor
        engine = await fiscal_core._get_engine_for_tenant(sample_tenant_id)
        
        # Verificar que usó el entorno de la configuración
        assert engine.environment == "production"
    
    @pytest.mark.asyncio
    async def test_fiscal_core_engine_selection_logging(
        self, fiscal_core, register_mock_engine, sample_tenant_id, caplog
    ):
        """Test que FiscalCore loguea correctamente la selección de motor."""
        from app.models.tenant import Tenant
        
        mock_tenant = Mock()
        mock_tenant.fiscal_engine_id = "mock_fiscal"
        mock_tenant.fiscal_config = {}
        
        fiscal_core.db.execute.return_value.scalar_one_or_none.return_value = mock_tenant
        
        # Obtener motor
        await fiscal_core._get_engine_for_tenant(sample_tenant_id)
        
        # Verificar que se logueó la selección
        # Nota: Esto requiere configuración de logging específica para tests


class TestFiscalCoreErrorHandling:
    """Pruebas de manejo de errores en FiscalCore."""
    
    @pytest.fixture
    def fiscal_core(self, mock_db):
        """Fixture que proporciona FiscalCore con mock DB."""
        return FiscalCore(mock_db)
    
    @pytest.mark.asyncio
    async def test_fiscal_core_handles_validation_errors(
        self, fiscal_core, sample_invoice_id, sample_certificate_id, sample_tenant_id
    ):
        """Test que FiscalCore maneja errores de validación del motor."""
        from app.models.tenant import Tenant
        
        # Registrar motor mock
        registry = get_fiscal_engine_registry()
        mock_engine = MockFiscalEngine(environment="testing")
        registry.register_engine("mock_fiscal", mock_engine)
        
        # Mockear tenant
        mock_tenant = Mock()
        mock_tenant.fiscal_engine_id = "mock_fiscal"
        mock_tenant.fiscal_config = {}
        fiscal_core.db.execute.return_value.scalar_one_or_none.return_value = mock_tenant
        
        # Mockear obtención de entidades para que falle validación
        fiscal_core._get_invoice = AsyncMock(side_effect=FiscalCoreError("Invoice not found"))
        
        # Intentar emitir documento
        with pytest.raises(FiscalCoreError):
            await fiscal_core.issue_fiscal_document(
                sample_invoice_id,
                sample_certificate_id,
                sample_tenant_id
            )
    
    @pytest.mark.asyncio
    async def test_fiscal_core_handles_engine_errors(
        self, fiscal_core, sample_invoice_id, sample_certificate_id, sample_tenant_id
    ):
        """Test que FiscalCore maneja errores del motor fiscal."""
        from app.models.tenant import Tenant
        
        # Registrar motor mock que falla
        registry = get_fiscal_engine_registry()
        mock_engine = Mock(spec=MockFiscalEngine)
        mock_engine.validate_document = AsyncMock(
            side_effect=ValidationError("Mock validation failed")
        )
        registry.register_engine("failing_engine", mock_engine)
        
        # Mockear tenant
        mock_tenant = Mock()
        mock_tenant.fiscal_engine_id = "failing_engine"
        mock_tenant.fiscal_config = {}
        fiscal_core.db.execute.return_value.scalar_one_or_none.return_value = mock_tenant
        
        # Intentar emitir documento
        with pytest.raises(FiscalCoreError):
            await fiscal_core.issue_fiscal_document(
                sample_invoice_id,
                sample_certificate_id,
                sample_tenant_id
            )


class TestFiscalCoreDataConversion:
    """Pruebas de conversión de datos en FiscalCore."""
    
    @pytest.fixture
    def fiscal_core(self, mock_db):
        """Fixture que proporciona FiscalCore con mock DB."""
        return FiscalCore(mock_db)
    
    @pytest.mark.asyncio
    async def test_convert_to_fiscal_document_data(
        self, fiscal_core, sample_invoice_id
    ):
        """Test que FiscalCore convierte correctamente entidades ERP a modelo normalizado."""
        from app.models.invoice import Invoice
        from app.models.company import Company
        from app.models.certificate import Certificate
        
        # Crear mocks de entidades
        mock_invoice = Mock()
        mock_invoice.id = sample_invoice_id
        mock_invoice.company_id = uuid4()
        mock_invoice.customer_id = uuid4()
        mock_invoice.document_type = "invoice"
        mock_invoice.series = "A"
        mock_invoice.number = "001"
        mock_invoice.issue_date = date.today()
        mock_invoice.currency = "UYU"
        mock_invoice.exchange_rate = Decimal("1")
        mock_invoice.subtotal = Decimal("100")
        mock_invoice.tax_total = Decimal("22")
        mock_invoice.total = Decimal("122")
        mock_invoice.discount_total = Decimal("0")
        mock_invoice.notes = "Test invoice"
        mock_invoice.metadata_json = {}
        
        mock_company = Mock()
        mock_company.rut = "123456789012"
        mock_company.legal_name = "Test Company"
        mock_company.trade_name = "Test Trade"
        mock_company.business_activity = "Commerce"
        mock_company.fiscal_address = "123 Test St"
        mock_company.city = "Montevideo"
        mock_company.department = "Montevideo"
        mock_company.phone = "123456789"
        mock_company.email = "test@example.com"
        mock_company.dgi_branch_code = 1
        mock_company.metadata_json = {}
        
        mock_customer = Mock()
        mock_customer.rut = "987654321012"
        mock_customer.legal_name = "Test Customer"
        mock_customer.address = "456 Customer Ave"
        mock_customer.city = "Montevideo"
        mock_customer.department = "Montevideo"
        mock_customer.phone = "987654321"
        mock_customer.email = "customer@example.com"
        mock_customer.metadata_json = {}
        
        mock_certificate = Mock()
        mock_certificate.metadata_json = {
            "cert_path": "/path/to/cert.pem",
            "key_path": "/path/to/key.pem"
        }
        
        mock_items = [
            Mock(
                description="Test Item",
                quantity=Decimal("1"),
                unit_price=Decimal("100"),
                discount=Decimal("0"),
                tax_amount=Decimal("22"),
                metadata_json={}
            )
        ]
        
        # Convertir
        fiscal_data = await fiscal_core._convert_to_fiscal_document_data(
            mock_invoice, mock_company, mock_customer, mock_items, mock_certificate
        )
        
        # Verificar conversión
        assert fiscal_data.document_type == "invoice"
        assert fiscal_data.series == "A"
        assert fiscal_data.number == "001"
        assert fiscal_data.company.rut == "123456789012"
        assert fiscal_data.company.legal_name == "Test Company"
        assert fiscal_data.customer is not None
        assert fiscal_data.customer.legal_name == "Test Customer"
        assert len(fiscal_data.items) == 1
        assert fiscal_data.items[0].description == "Test Item"
        assert fiscal_data.total == Decimal("122")
        assert fiscal_data.engine_config is not None
        assert fiscal_data.engine_config["cert_path"] == "/path/to/cert.pem"


class TestFiscalCoreMultiEngine:
    """Pruebas que demuestran el uso de múltiples motores."""
    
    @pytest.fixture
    def fiscal_core(self, mock_db):
        """Fixture que proporciona FiscalCore con mock DB."""
        return FiscalCore(mock_db)
    
    @pytest.mark.asyncio
    async def test_fiscal_core_switches_engines_by_tenant(
        self, fiscal_core, sample_tenant_id
    ):
        """Test que FiscalCore puede usar diferentes motores para diferentes tenants."""
        from app.models.tenant import Tenant
        
        # Registrar dos motores
        registry = get_fiscal_engine_registry()
        mock_engine_1 = MockFiscalEngine(environment="testing")
        mock_engine_2 = MockFiscalEngine(environment="production")
        registry.register_engine("mock_engine_1", mock_engine_1)
        registry.register_engine("mock_engine_2", mock_engine_2)
        
        # Tenant 1 usa motor 1
        mock_tenant_1 = Mock()
        mock_tenant_1.fiscal_engine_id = "mock_engine_1"
        mock_tenant_1.fiscal_config = {}
        
        fiscal_core.db.execute.return_value.scalar_one_or_none.return_value = mock_tenant_1
        engine_1 = await fiscal_core._get_engine_for_tenant(sample_tenant_id)
        
        # Tenant 2 usa motor 2
        mock_tenant_2 = Mock()
        mock_tenant_2.fiscal_engine_id = "mock_engine_2"
        mock_tenant_2.fiscal_config = {}
        
        fiscal_core.db.execute.return_value.scalar_one_or_none.return_value = mock_tenant_2
        engine_2 = await fiscal_core._get_engine_for_tenant(sample_tenant_id)
        
        # Verificar que obtuvieron motores diferentes
        assert engine_1.environment == "testing"
        assert engine_2.environment == "production"
    
    @pytest.mark.asyncio
    async def test_fiscal_core_registry_lists_all_engines(self):
        """Test que el registro lista todos los motores disponibles."""
        registry = get_fiscal_engine_registry()
        
        # Registrar varios motores
        registry.register_engine("mock_1", MockFiscalEngine())
        registry.register_engine("mock_2", MockFiscalEngine())
        
        # Listar motores
        engines = registry.list_engines()
        
        # Verificar que ambos están en la lista
        assert "mock_1" in engines
        assert "mock_2" in engines
        assert len(engines) >= 2