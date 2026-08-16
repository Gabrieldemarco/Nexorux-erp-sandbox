"""
Motor fiscal mock para demostrar la extensibilidad de la arquitectura.

Este motor es un ejemplo de cómo implementar IFiscalEngine para un
proveedor fiscal ficticio, demostrando que agregar nuevos motores
es simple y no requiere modificar el ERP.
"""

import structlog
from typing import Dict, Any
from datetime import date

from app.services.fiscal.engines.base import (
    IFiscalEngine,
    FiscalEngineError,
    ValidationError
)
from app.services.fiscal.models import (
    FiscalDocumentResponse,
    FiscalEngineCapabilities
)

logger = structlog.get_logger(__name__)


class MockFiscalEngine(IFiscalEngine):
    """
    Motor fiscal mock para propósitos de demostración y testing.
    
    Este motor simula un proveedor fiscal ficticio llamado "MockFiscal Authority"
    que emite documentos en formato JSON en lugar de XML.
    
    Propósito:
    - Demostrar cómo implementar IFiscalEngine
    - Facilitar testing sin depender de servicios reales
    - Servir como template para implementaciones reales
    """
    
    def __init__(self, environment: str = "testing"):
        """
        Inicializa el motor mock.
        
        Args:
            environment: Entorno (testing, development, production)
        """
        self.environment = environment
        self._issued_documents = {}  # Almacenamiento en memoria para demo
        logger.info("mock_fiscal_engine_initialized", environment=environment)
    
    @property
    def engine_info(self) -> FiscalEngineCapabilities:
        """Retorna información sobre las capacidades del motor mock."""
        return FiscalEngineCapabilities(
            engine_id="mock_fiscal",
            engine_name="Mock Fiscal Authority",
            country="XX",  # País ficticio
            fiscal_authority="MockFiscal Authority",
            version="1.0",
            supports_electronic_invoice=True,
            supports_credit_note=True,
            supports_debit_note=True,
            supports_contingency=True,
            supports_cancellation=True,  # El mock sí soporta cancelación
            supports_query_status=True,
            supported_document_types=[
                "invoice",
                "credit_note", 
                "debit_note",
                "contingency_invoice"
            ]
        )
    
    async def validate_document(self, document_data: Dict[str, Any]) -> FiscalDocumentResponse:
        """
        Valida un documento según reglas del mock.
        
        Reglas de validación mock:
        - Debe tener company con rut
        - Debe tener al menos un item
        - El total debe ser positivo
        """
        logger.info("mock_validate_document", document_type=document_data.get("document_type"))
        
        validation_errors = []
        
        # Validaciones básicas
        company = document_data.get("company", {})
        if not company.get("rut"):
            validation_errors.append("Company RUT is required")
        
        items = document_data.get("items", [])
        if not items or len(items) == 0:
            validation_errors.append("At least one item is required")
        
        total = document_data.get("total", 0)
        if total <= 0:
            validation_errors.append("Total must be greater than 0")
        
        is_valid = len(validation_errors) == 0
        
        return FiscalDocumentResponse(
            success=is_valid,
            validation_errors=validation_errors if not is_valid else None,
            status="valid" if is_valid else "invalid",
            engine_used="mock_fiscal",
            operation="validate"
        )
    
    async def issue_document(self, document_data: Dict[str, Any]) -> FiscalDocumentResponse:
        """
        Emite un documento fiscal en formato JSON (simulado).
        
        A diferencia de DGI que usa XML, este motor usa JSON para demostrar
        que diferentes proveedores pueden tener diferentes formatos.
        """
        logger.info("mock_issue_document", document_type=document_data.get("document_type"))
        
        # Validar primero
        validation = await self.validate_document(document_data)
        if not validation.success:
            raise ValidationError(
                f"Document validation failed: {validation.validation_errors}",
                validation_errors=validation.validation_errors
            )
        
        # Generar documento JSON (simulado)
        document_type = document_data.get("document_type")
        series = document_data.get("series")
        number = document_data.get("number")
        
        mock_document = {
            "document_type": document_type,
            "series": series,
            "number": number,
            "issue_date": str(document_data.get("issue_date")),
            "company": document_data.get("company"),
            "customer": document_data.get("customer"),
            "items": document_data.get("items"),
            "totals": {
                "subtotal": document_data.get("subtotal"),
                "tax_total": document_data.get("tax_total"),
                "total": document_data.get("total")
            },
            "currency": document_data.get("currency"),
            "mock_authority": {
                "authorization_code": f"MOCK-{series}{number}",
                "authorized_at": "2026-08-15T22:00:00Z",
                "environment": self.environment
            }
        }
        
        import json
        generated_json = json.dumps(mock_document, indent=2)
        
        # Guardar en almacenamiento en memoria
        doc_key = f"{series}{number}"
        self._issued_documents[doc_key] = mock_document
        
        logger.info("mock_issue_document_success", document_key=doc_key)
        
        return FiscalDocumentResponse(
            success=True,
            document_type=document_type,
            series=series,
            number=number,
            generated_xml=generated_json,  # Usamos el mismo campo pero con JSON
            signed_xml=generated_json,     # Simulado
            status="authorized",            # El mock autoriza inmediatamente
            engine_used="mock_fiscal",
            operation="issue"
        )
    
    async def send_document(self, document_data: Dict[str, Any]) -> FiscalDocumentResponse:
        """
        Envía un documento a la autoridad mock.
        
        En este caso, el mock ya autoriza durante la emisión, así que
        el envío es una operación trivial que confirma la autorización.
        """
        logger.info("mock_send_document")
        
        series = document_data.get("series")
        number = document_data.get("number")
        doc_key = f"{series}{number}"
        
        # Verificar que el documento fue emitido
        if doc_key not in self._issued_documents:
            raise ValidationError(f"Document {doc_key} not found in issued documents")
        
        mock_doc = self._issued_documents[doc_key]
        
        logger.info("mock_send_document_success", document_key=doc_key)
        
        return FiscalDocumentResponse(
            success=True,
            status="confirmed",
            engine_response={
                "status": "confirmed",
                "authorization_code": mock_doc["mock_authority"]["authorization_code"],
                "confirmed_at": "2026-08-15T22:05:00Z"
            },
            engine_used="mock_fiscal",
            operation="send"
        )
    
    async def query_status(self, document_data: Dict[str, Any]) -> FiscalDocumentResponse:
        """
        Consulta el estado de un documento en la autoridad mock.
        """
        logger.info("mock_query_status")
        
        series = document_data.get("series")
        number = document_data.get("number")
        doc_key = f"{series}{number}"
        
        if doc_key in self._issued_documents:
            mock_doc = self._issued_documents[doc_key]
            status = "authorized"
        else:
            status = "not_found"
            mock_doc = None
        
        logger.info("mock_query_status_success", document_key=doc_key, status=status)
        
        return FiscalDocumentResponse(
            success=True,
            engine_response={
                "status": status,
                "document": mock_doc,
                "queried_at": "2026-08-15T22:10:00Z"
            },
            engine_used="mock_fiscal",
            operation="query"
        )
    
    async def cancel_document(self, document_data: Dict[str, Any]) -> FiscalDocumentResponse:
        """
        Cancela un documento en la autoridad mock.
        
        A diferencia de DGI que no soporta cancelación directa,
        este motor mock sí implementa cancelación.
        """
        logger.info("mock_cancel_document")
        
        series = document_data.get("series")
        number = document_data.get("number")
        doc_key = f"{series}{number}"
        
        if doc_key not in self._issued_documents:
            raise ValidationError(f"Document {doc_key} not found for cancellation")
        
        # Marcar como cancelado
        self._issued_documents[doc_key]["mock_authority"]["status"] = "cancelled"
        self._issued_documents[doc_key]["mock_authority"]["cancelled_at"] = "2026-08-15T22:15:00Z"
        
        logger.info("mock_cancel_document_success", document_key=doc_key)
        
        return FiscalDocumentResponse(
            success=True,
            status="cancelled",
            engine_response={
                "status": "cancelled",
                "cancelled_at": "2026-08-15T22:15:00Z",
                "cancellation_reason": document_data.get("reason", "User requested")
            },
            engine_used="mock_fiscal",
            operation="cancel"
        )
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Verifica la salud del servicio mock.
        
        Siempre retorna healthy ya que es un servicio simulado.
        """
        logger.info("mock_health_check")
        
        return {
            "healthy": True,
            "environment": self.environment,
            "endpoint": "mock://fiscal.authority/api",
            "engine_id": "mock_fiscal",
            "message": "Mock fiscal service is running",
            "issued_documents_count": len(self._issued_documents)
        }
    
    def get_issued_documents(self) -> Dict[str, Any]:
        """
        Método adicional para testing: retorna todos los documentos emitidos.
        
        Returns:
            Dict con todos los documentos emitidos en memoria
        """
        return self._issued_documents
    
    def clear_issued_documents(self) -> None:
        """
        Método adicional para testing: limpia los documentos emitidos.
        """
        self._issued_documents.clear()
        logger.info("mock_issued_documents_cleared")