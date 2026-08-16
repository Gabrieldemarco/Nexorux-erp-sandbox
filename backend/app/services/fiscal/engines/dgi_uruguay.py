"""
Motor fiscal para DGI Uruguay.

Este motor implementa la interfaz IFiscalEngine para la integración con
los servicios web de la Dirección General Impositiva de Uruguay.
"""

import structlog
from typing import Dict, Any, Optional
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

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
    FiscalDocumentItem,
    ReferenceDocument
)
from app.services.fiscal.dgi_client import DGIClient, DGIError
from app.services.fiscal.xml_builder import build_cfe_xml
from app.services.fiscal.signer import sign_xml, load_certificate, load_private_key, CertificateError, SigningError
from app.services.fiscal.cfe_types import (
    CFEType, 
    CFE_TYPE_INFO, 
    resolve_document_type, 
    is_note, 
    get_parent_type
)
from app.services.fiscal.xsd_validator import validate_cfe_xml_or_raise, CFEValidationError, DEFAULT_XSD_PATH
from app.core.config import settings

logger = structlog.get_logger(__name__)


class DGIUruguayEngine(IFiscalEngine):
    """
    Implementación del motor fiscal para DGI Uruguay.
    
    Este motor encapsula toda la lógica específica de Uruguay:
    - Generación de XML CFE según especificación DGI
    - Firma digital con certificados X.509
    - Comunicación SOAP con servicios DGI
    - Validación según XSD DGI
    - Manejo de contingencia
    """
    
    def __init__(self, environment: str = "testing"):
        """
        Inicializa el motor DGI Uruguay.
        
        Args:
            environment: Entorno DGI (testing, homologacion, produccion)
        """
        self.environment = environment
        self._client = None
        logger.info("dgi_uruguay_engine_initialized", environment=environment)
    
    @property
    def engine_info(self) -> FiscalEngineCapabilities:
        """Retorna información sobre las capacidades del motor DGI Uruguay."""
        return FiscalEngineCapabilities(
            engine_id="dgi_uruguay",
            engine_name="DGI Uruguay Engine",
            country="UY",
            fiscal_authority="Dirección General Impositiva",
            version="1.0",
            supports_electronic_invoice=True,
            supports_credit_note=True,
            supports_debit_note=True,
            supports_contingency=True,
            supports_cancellation=False,  # No implementado aún
            supports_query_status=True,
            supported_document_types=[
                "111",  # e-Factura
                "101",  # e-Ticket
                "112",  # Nota de Crédito e-Factura
                "113",  # Nota de Débito e-Factura
                "102",  # Nota de Crédito e-Ticket
                "103",  # Nota de Débito e-Ticket
                "201",  # e-Ticket Contingencia
                "202",  # Nota de Crédito e-Ticket Contingencia
                "203",  # Nota de Débito e-Ticket Contingencia
                "211",  # e-Factura Contingencia
                "212",  # Nota de Crédito e-Factura Contingencia
                "213",  # Nota de Débito e-Factura Contingencia
            ]
        )
    
    async def validate_document(self, document_data: Dict[str, Any]) -> FiscalDocumentResponse:
        """
        Valida un documento según reglas DGI Uruguay.
        
        Args:
            document_data: Datos del documento en formato normalizado
            
        Returns:
            FiscalDocumentResponse con resultado de validación
        """
        logger.info("dgi_validate_document_started", document_type=document_data.get("document_type"))
        
        validation_errors = []
        
        try:
            # Convertir a modelo normalizado para validaciones Pydantic
            fiscal_doc = FiscalDocumentData(**document_data)
        except Exception as e:
            validation_errors.append(f"Invalid document structure: {str(e)}")
            return FiscalDocumentResponse(
                success=False,
                validation_errors=validation_errors,
                engine_used="dgi_uruguay",
                operation="validate"
            )
        
        # Validaciones específicas DGI
        if not fiscal_doc.company.rut:
            validation_errors.append("Company RUT is required for DGI documents")
        
        if not fiscal_doc.items:
            validation_errors.append("At least one item is required")
        
        # Validar tipo de documento
        document_type = fiscal_doc.document_type
        if document_type not in self.get_supported_document_types():
            validation_errors.append(f"Unsupported document type for DGI: {document_type}")
        
        # Validar RUT de cliente si corresponde
        cfe_info = CFE_TYPE_INFO.get(document_type)
        if cfe_info and cfe_info.get("requires_receptor_rut"):
            if not fiscal_doc.customer or not fiscal_doc.customer.rut:
                validation_errors.append(f"Customer RUT is required for document type {document_type}")
        
        # Validar documento de referencia para notas
        if is_note(document_type) and not fiscal_doc.reference_document:
            validation_errors.append("Reference document is required for credit/debit notes")
        
        # Validar moneda y tipo de cambio
        if fiscal_doc.currency != "UYU" and fiscal_doc.exchange_rate <= 0:
            validation_errors.append("Exchange rate must be greater than 0 for foreign currency")
        
        is_valid = len(validation_errors) == 0
        
        logger.info(
            "dgi_validate_document_completed",
            valid=is_valid,
            errors_count=len(validation_errors)
        )
        
        return FiscalDocumentResponse(
            success=is_valid,
            validation_errors=validation_errors if not is_valid else None,
            status="valid" if is_valid else "invalid",
            engine_used="dgi_uruguay",
            operation="validate"
        )
    
    async def issue_document(self, document_data: Dict[str, Any]) -> FiscalDocumentResponse:
        """
        Emite un documento CFE para DGI Uruguay.
        
        Proceso:
        1. Convertir documento normalizado a formato CFE
        2. Generar XML según especificación DGI
        3. Validar XML estructuralmente
        4. Firmar XML con certificado X.509
        5. Validar XML firmado con XSD
        6. Retornar documento listo para envío
        
        Args:
            document_data: Datos del documento incluyendo certificado
            
        Returns:
            FiscalDocumentResponse con XML generado y firmado
        """
        logger.info("dgi_issue_document_started", document_type=document_data.get("document_type"))
        
        try:
            # Validar primero
            validation = await self.validate_document(document_data)
            if not validation.success:
                raise ValidationError(
                    f"Document validation failed: {validation.validation_errors}",
                    validation_errors=validation.validation_errors
                )
            
            fiscal_doc = FiscalDocumentData(**document_data)
            
            # Obtener configuración de certificado
            engine_config = fiscal_doc.engine_config or {}
            cert_path = engine_config.get("cert_path")
            key_path = engine_config.get("key_path")
            
            if not cert_path or not key_path:
                raise ValidationError("Certificate configuration missing: cert_path and key_path required")
            
            if not Path(cert_path).exists():
                raise ValidationError(f"Certificate file not found: {cert_path}")
            if not Path(key_path).exists():
                raise ValidationError(f"Private key file not found: {key_path}")
            
            # Determinar tipo CFE (considerando contingencia)
            is_contingency = engine_config.get("is_contingency", False)
            cfe_type = resolve_document_type(fiscal_doc.document_type, is_contingency=is_contingency)
            
            # Construir objetos para XML builder
            company_data = fiscal_doc.company.model_dump()
            customer_data = fiscal_doc.customer.model_dump() if fiscal_doc.customer else None
            items_data = [item.model_dump() for item in fiscal_doc.items]
            reference_data = fiscal_doc.reference_document.model_dump() if fiscal_doc.reference_document else None
            
            # Generar XML CFE
            xml_bytes = build_cfe_xml(
                invoice=self._create_invoice_proxy(fiscal_doc),
                company=self._create_company_proxy(company_data),
                customer=self._create_customer_proxy(customer_data) if customer_data else None,
                items=self._create_items_proxy(items_data),
                document_type=cfe_type,
                cfe_number=f"{fiscal_doc.series}{fiscal_doc.number}",
                issue_date=fiscal_doc.issue_date,
                currency=fiscal_doc.currency,
                exchange_rate=fiscal_doc.exchange_rate,
                notes=fiscal_doc.notes,
                reference_document=reference_data,
            )
            
            # Validar XML estructuralmente
            xsd_path = Path(settings.CFE_XSD_PATH) if settings.CFE_XSD_PATH else None
            try:
                validate_cfe_xml_or_raise(
                    xml_bytes,
                    xsd_path=xsd_path,
                    require_xsd=settings.CFE_XSD_VALIDATION_REQUIRED,
                    validate_xsd=False,
                )
            except CFEValidationError as e:
                raise ValidationError(f"CFE XML structural validation failed: {'; '.join(e.errors)}")
            
            # Cargar certificado y clave privada
            cert, cert_data = load_certificate(cert_path)
            private_key = load_private_key(key_path)
            
            # Firmar XML
            try:
                signed_xml = sign_xml(xml_bytes, private_key, cert, cert_data)
            except (CertificateError, SigningError) as e:
                raise ValidationError(f"Failed to sign CFE XML: {e}")
            
            # Validar XML firmado con XSD
            if settings.CFE_XSD_VALIDATION_REQUIRED or (xsd_path and xsd_path.exists()) or DEFAULT_XSD_PATH.exists():
                try:
                    validate_cfe_xml_or_raise(
                        signed_xml,
                        xsd_path=xsd_path,
                        require_xsd=settings.CFE_XSD_VALIDATION_REQUIRED,
                        validate_xsd=True,
                    )
                except CFEValidationError as e:
                    raise ValidationError(f"CFE XML XSD validation failed: {'; '.join(e.errors)}")
            
            logger.info("dgi_issue_document_success", document_type=cfe_type)
            
            return FiscalDocumentResponse(
                success=True,
                document_type=cfe_type,
                series=fiscal_doc.series,
                number=fiscal_doc.number,
                generated_xml=xml_bytes.decode("utf-8", errors="replace"),
                signed_xml=signed_xml.decode("utf-8", errors="replace"),
                status="ready_to_send",
                engine_used="dgi_uruguay",
                operation="issue"
            )
            
        except ValidationError:
            raise
        except Exception as e:
            logger.error("dgi_issue_document_failed", error=str(e))
            raise FiscalEngineError(f"Failed to issue CFE document: {e}")
    
    async def send_document(self, document_data: Dict[str, Any]) -> FiscalDocumentResponse:
        """
        Envía un documento CFE a DGI Uruguay.
        
        Args:
            document_data: Datos del documento incluyendo XML firmado
            
        Returns:
            FiscalDocumentResponse con respuesta de DGI
        """
        logger.info("dgi_send_document_started")
        
        try:
            signed_xml = document_data.get("signed_xml")
            if not signed_xml:
                raise ValidationError("signed_xml is required for sending")
            
            if isinstance(signed_xml, str):
                signed_xml_bytes = signed_xml.encode("utf-8")
            else:
                signed_xml_bytes = signed_xml
            
            # Obtener configuración de certificado para autenticación
            engine_config = document_data.get("engine_config", {})
            cert_path = engine_config.get("cert_path")
            
            cert_data = None
            if cert_path and Path(cert_path).exists():
                _, cert_data = load_certificate(cert_path)
            
            # Enviar a DGI
            async with DGIClient(environment=self.environment, certificate_data=cert_data) as client:
                try:
                    response = await client.send_cfe_envelope(signed_xml_bytes)
                except DGIError as e:
                    logger.error("dgi_send_failed", error=str(e))
                    raise TransmissionError(f"DGI send failed: {e}")
            
            # Procesar respuesta
            status_code = response.get("status_code", "unknown")
            status_message = response.get("status_message", "")
            
            is_accepted = status_code.lower() in ("aceptado", "ok", "0", "success")
            is_rejected = status_code.lower() in ("rechazado", "error", "1")
            
            final_status = "accepted" if is_accepted else "rejected" if is_rejected else "pending"
            
            logger.info(
                "dgi_send_document_completed",
                status=final_status,
                dgi_status=status_code
            )
            
            return FiscalDocumentResponse(
                success=is_accepted,
                status=final_status,
                engine_response=response,
                engine_used="dgi_uruguay",
                operation="send"
            )
            
        except TransmissionError:
            raise
        except Exception as e:
            logger.error("dgi_send_document_failed", error=str(e))
            raise FiscalEngineError(f"Failed to send CFE document: {e}")
    
    async def query_status(self, document_data: Dict[str, Any]) -> FiscalDocumentResponse:
        """
        Consulta el estado de un CFE en DGI Uruguay.
        
        Args:
            document_data: Datos para identificar el CFE (rut, tipo, número, fecha)
            
        Returns:
            FiscalDocumentResponse con estado del CFE
        """
        logger.info("dgi_query_status_started")
        
        try:
            rut = document_data.get("rut")
            cfe_type = document_data.get("cfe_type")
            cfe_number = document_data.get("cfe_number")
            issue_date = document_data.get("issue_date")
            
            if not all([rut, cfe_type, cfe_number, issue_date]):
                raise ValidationError("Missing required fields for DGI query: rut, cfe_type, cfe_number, issue_date")
            
            # Formatear fecha
            if isinstance(issue_date, datetime):
                issue_date_str = issue_date.strftime("%Y-%m-%d")
            elif isinstance(issue_date, date):
                issue_date_str = issue_date.strftime("%Y-%m-%d")
            else:
                issue_date_str = str(issue_date)
            
            async with DGIClient(environment=self.environment) as client:
                try:
                    response = await client.query_cfe_status(
                        rut=rut,
                        cfe_type=cfe_type,
                        cfe_number=cfe_number,
                        issue_date=issue_date_str
                    )
                except DGIError as e:
                    logger.error("dgi_query_failed", error=str(e))
                    raise TransmissionError(f"DGI query failed: {e}")
            
            logger.info("dgi_query_status_success", response=response)
            
            return FiscalDocumentResponse(
                success=True,
                engine_response=response,
                engine_used="dgi_uruguay",
                operation="query"
            )
            
        except (ValidationError, TransmissionError):
            raise
        except Exception as e:
            logger.error("dgi_query_status_failed", error=str(e))
            raise FiscalEngineError(f"Failed to query CFE status: {e}")
    
    async def cancel_document(self, document_data: Dict[str, Any]) -> FiscalDocumentResponse:
        """
        Cancela un documento CFE en DGI Uruguay.
        
        NOTA: Esta funcionalidad no está implementada actualmente en DGI Uruguay.
        Para cancelar un CFE se debe emitir una nota de crédito.
        
        Args:
            document_data: Datos del documento a cancelar
            
        Returns:
            FiscalDocumentResponse con resultado
            
        Raises:
            FiscalEngineError: Siempre, ya que no está implementado
        """
        logger.warning("dgi_cancel_document_not_implemented")
        raise FiscalEngineError(
            "Cancellation not implemented for DGI Uruguay. "
            "To cancel a CFE, issue a credit note instead."
        )
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Verifica la conectividad con los servicios DGI.
        
        Returns:
            Dict con información de salud del servicio
        """
        logger.info("dgi_health_check_started", environment=self.environment)
        
        try:
            async with DGIClient(environment=self.environment) as client:
                # Intentar obtener cliente HTTP
                http_client = await client._get_client()
                
                return {
                    "healthy": True,
                    "environment": self.environment,
                    "endpoint": client.url,
                    "engine_id": "dgi_uruguay",
                    "message": "DGI service is reachable"
                }
                
        except Exception as e:
            logger.error("dgi_health_check_failed", error=str(e))
            return {
                "healthy": False,
                "environment": self.environment,
                "engine_id": "dgi_uruguay",
                "error": str(e)
            }
    
    # Métodos auxiliares para compatibilidad con código existente
    
    def _create_invoice_proxy(self, fiscal_doc: FiscalDocumentData):
        """Crea un objeto proxy compatible con Invoice para xml_builder."""
        class InvoiceProxy:
            def __init__(self, doc: FiscalDocumentData):
                self.id = doc.invoice_id
                self.series = doc.series
                self.number = doc.number
                self.issue_date = doc.issue_date
                self.currency = doc.currency
                self.exchange_rate = doc.exchange_rate
                self.notes = doc.notes
                self.metadata_json = doc.metadata or {}
                if doc.engine_config:
                    self.metadata_json.update(doc.engine_config)
        
        return InvoiceProxy(fiscal_doc)
    
    def _create_company_proxy(self, company_data: Dict):
        """Crea un objeto proxy compatible con Company para xml_builder."""
        class CompanyProxy:
            def __init__(self, data: Dict):
                self.rut = data.get("rut")
                self.legal_name = data.get("legal_name")
                self.trade_name = data.get("trade_name")
                self.business_activity = data.get("business_activity")
                self.fiscal_address = data.get("fiscal_address") or data.get("address")
                self.city = data.get("city")
                self.department = data.get("department")
                self.phone = data.get("phone")
                self.email = data.get("email")
                self.dgi_branch_code = data.get("branch_code")
                self.metadata_json = data.get("metadata", {})
        
        return CompanyProxy(company_data)
    
    def _create_customer_proxy(self, customer_data: Dict):
        """Crea un objeto proxy compatible con Customer para xml_builder."""
        class CustomerProxy:
            def __init__(self, data: Dict):
                self.rut = data.get("rut")
                self.legal_name = data.get("legal_name")
                self.address = data.get("address")
                self.city = data.get("city")
                self.department = data.get("department")
                self.phone = data.get("phone")
                self.email = data.get("email")
        
        return CustomerProxy(customer_data)
    
    def _create_items_proxy(self, items_data: list):
        """Crea objetos proxy compatibles con InvoiceItem para xml_builder."""
        class ItemProxy:
            def __init__(self, data: Dict):
                self.description = data.get("description")
                self.quantity = Decimal(str(data.get("quantity", 0)))
                self.unit_price = Decimal(str(data.get("unit_price", 0)))
                self.discount = Decimal(str(data.get("discount", 0)))
                self.tax_amount = Decimal(str(data.get("tax_amount", 0)))
        
        return [ItemProxy(item) for item in items_data]