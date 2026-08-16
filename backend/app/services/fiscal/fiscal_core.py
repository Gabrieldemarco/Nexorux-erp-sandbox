"""
Fiscal Core - Servicio central de operaciones fiscales.

Este componente actúa como intermediario entre el ERP y los motores fiscales,
proporcionando una interfaz unificada y agnóstica al proveedor fiscal.
"""

import structlog
import uuid
from typing import Dict, Any, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.services.fiscal.models import (
    FiscalDocumentData, 
    FiscalDocumentResponse,
    FiscalCompany,
    FiscalCustomer,
    FiscalDocumentItem,
    ReferenceDocument
)
from app.services.fiscal.engines.base import (
    IFiscalEngine, 
    FiscalEngineError, 
    ValidationError
)
from app.services.fiscal.engines.registry import get_fiscal_engine_registry
from app.models.invoice import Invoice
from app.models.invoice_item import InvoiceItem
from app.models.company import Company
from app.models.customer import Customer
from app.models.certificate import Certificate
from app.models.fiscal_document import FiscalDocument as FiscalDocumentModel
from app.models.fiscal_response import FiscalResponse
from app.models.tenant import Tenant
from app.services.fiscal.state_machine import FiscalStateMachine, FiscalState

logger = structlog.get_logger(__name__)


class FiscalCoreError(Exception):
    """Excepción base para errores del Fiscal Core."""
    pass


class FiscalCore:
    """
    Servicio central de operaciones fiscales.
    
    Responsabilidades:
    - Selección del motor fiscal adecuado según configuración
    - Conversión entre modelos ERP y modelos fiscales normalizados
    - Orquestación de operaciones fiscales (emisión, envío, consulta)
    - Persistencia de documentos y respuestas fiscales
    - Manejo de errores y reintentos
    """
    
    def __init__(self, db: AsyncSession):
        """
        Inicializa el Fiscal Core.
        
        Args:
            db: Sesión de base de datos SQLAlchemy
        """
        self.db = db
        self.registry = get_fiscal_engine_registry()
        self.state_machine = FiscalStateMachine()
        logger.info("fiscal_core_initialized")
    
    async def issue_fiscal_document(
        self,
        invoice_id: uuid.UUID,
        certificate_id: uuid.UUID,
        tenant_id: uuid.UUID,
        request_id: Optional[str] = None
    ) -> FiscalDocumentModel:
        """
        Emite un documento fiscal usando el motor configurado.
        
        Flujo:
        1. Obtener datos de la factura y entidades relacionadas
        2. Convertir a formato normalizado FiscalDocumentData
        3. Obtener motor fiscal configurado para el tenant
        4. Validar documento con el motor
        5. Emitir documento con el motor
        6. Guardar resultado en base de datos
        
        Args:
            invoice_id: ID de la factura en el ERP
            certificate_id: ID del certificado a usar
            tenant_id: ID del tenant
            request_id: ID opcional para tracking
            
        Returns:
            FiscalDocumentModel con el documento emitido
            
        Raises:
            FiscalCoreError: Si hay error en el proceso
        """
        logger.info(
            "fiscal_core_issue_started",
            invoice_id=str(invoice_id),
            certificate_id=str(certificate_id),
            tenant_id=str(tenant_id)
        )
        
        try:
            # 1. Obtener datos de la factura
            invoice = await self._get_invoice(invoice_id, tenant_id)
            certificate = await self._get_certificate(certificate_id, tenant_id)
            company = await self._get_company(invoice.company_id, tenant_id)
            customer = await self._get_customer(invoice.customer_id, tenant_id) if invoice.customer_id else None
            
            # Obtener items de la factura
            items = await self._get_invoice_items(invoice_id, tenant_id)
            
            # 2. Convertir a formato normalizado
            fiscal_data = await self._convert_to_fiscal_document_data(
                invoice, company, customer, items, certificate
            )
            
            # 3. Obtener motor fiscal configurado
            engine = await self._get_engine_for_tenant(tenant_id)
            
            # 4. Validar documento
            validation_result = await engine.validate_document(fiscal_data.model_dump())
            if not validation_result.success:
                raise FiscalCoreError(
                    f"Document validation failed: {validation_result.validation_errors}"
                )
            
            # 5. Emitir documento
            issue_result = await engine.issue_document(fiscal_data.model_dump())
            
            if not issue_result.success:
                raise FiscalCoreError(f"Document issuance failed: {issue_result.error_message}")
            
            # 6. Guardar en base de datos
            fiscal_doc = await self._save_issued_fiscal_document(
                fiscal_data, issue_result, tenant_id, request_id
            )
            
            logger.info(
                "fiscal_core_issue_success",
                fiscal_document_id=str(fiscal_doc.id),
                engine_used=issue_result.engine_used
            )
            
            return fiscal_doc
            
        except FiscalEngineError as e:
            logger.error("fiscal_core_issue_engine_error", error=str(e))
            raise FiscalCoreError(f"Fiscal engine error: {e}")
        except Exception as e:
            logger.error("fiscal_core_issue_failed", error=str(e))
            raise FiscalCoreError(f"Failed to issue fiscal document: {e}")
    
    async def send_fiscal_document(
        self,
        fiscal_document_id: uuid.UUID,
        tenant_id: uuid.UUID,
        environment: Optional[str] = None,
        certificate_id: Optional[uuid.UUID] = None
    ) -> Dict[str, Any]:
        """
        Envía un documento fiscal a la autoridad fiscal.
        
        Args:
            fiscal_document_id: ID del documento fiscal
            tenant_id: ID del tenant
            environment: Entorno fiscal (opcional, usa configuración por defecto)
            certificate_id: ID del certificado (opcional, para autenticación)
            
        Returns:
            Dict con respuesta de la autoridad fiscal
            
        Raises:
            FiscalCoreError: Si hay error en el proceso
        """
        logger.info(
            "fiscal_core_send_started",
            fiscal_document_id=str(fiscal_document_id),
            tenant_id=str(tenant_id)
        )
        
        try:
            # 1. Obtener documento fiscal
            fiscal_doc = await self._get_fiscal_document(fiscal_document_id, tenant_id)
            
            # 2. Verificar estado
            if self.state_machine.is_terminal(fiscal_doc.state):
                raise FiscalCoreError(
                    f"Cannot send fiscal document in terminal state: {fiscal_doc.state}"
                )
            
            # 3. Transición de estado
            self.state_machine.transition(fiscal_doc.state, FiscalState.PENDING_SEND.value)
            fiscal_doc.state = FiscalState.PENDING_SEND.value
            await self.db.flush()
            
            # 4. Obtener motor fiscal
            engine = await self._get_engine_for_tenant(tenant_id, environment)
            
            # 5. Preparar datos para envío
            send_data = {
                "signed_xml": fiscal_doc.raw_payload.get("signed_xml"),
                "document_type": fiscal_doc.document_type,
                "series": fiscal_doc.series,
                "number": fiscal_doc.number,
                "fiscal_document_id": str(fiscal_doc.id)
            }
            
            # Agregar configuración de certificado si se proporciona
            if certificate_id:
                certificate = await self._get_certificate(certificate_id, tenant_id)
                cert_path = certificate.metadata_json.get("cert_path")
                if cert_path:
                    send_data["engine_config"] = {"cert_path": cert_path}
            
            # 6. Enviar documento
            send_result = await engine.send_document(send_data)
            
            # 7. Actualizar estado según respuesta
            fiscal_doc.state = FiscalState.SENT.value
            fiscal_doc.sent_at = datetime.utcnow()
            fiscal_doc.response_at = datetime.utcnow()
            
            if send_result.success:
                fiscal_doc.state = FiscalState.ACCEPTED.value
            else:
                fiscal_doc.state = FiscalState.REJECTED.value
            
            # 8. Guardar respuesta
            await self._save_fiscal_response(
                fiscal_document_id,
                tenant_id,
                send_result,
                request_id=str(uuid.uuid4())
            )
            
            await self.db.flush()
            
            logger.info(
                "fiscal_core_send_success",
                fiscal_document_id=str(fiscal_document_id),
                status=fiscal_doc.state
            )
            
            return send_result.engine_response or {}
            
        except FiscalEngineError as e:
            logger.error("fiscal_core_send_engine_error", error=str(e))
            # Marcar como rechazado en caso de error
            fiscal_doc.state = FiscalState.REJECTED.value
            fiscal_doc.response_at = datetime.utcnow()
            await self.db.flush()
            raise FiscalCoreError(f"Fiscal engine error: {e}")
        except Exception as e:
            logger.error("fiscal_core_send_failed", error=str(e))
            raise FiscalCoreError(f"Failed to send fiscal document: {e}")
    
    async def query_fiscal_document_status(
        self,
        fiscal_document_id: uuid.UUID,
        tenant_id: uuid.UUID,
        environment: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Consulta el estado de un documento fiscal en la autoridad.
        
        Args:
            fiscal_document_id: ID del documento fiscal
            tenant_id: ID del tenant
            environment: Entorno fiscal (opcional)
            
        Returns:
            Dict con estado del documento
            
        Raises:
            FiscalCoreError: Si hay error en el proceso
        """
        logger.info(
            "fiscal_core_query_status_started",
            fiscal_document_id=str(fiscal_document_id)
        )
        
        try:
            # Obtener documento y compañía
            fiscal_doc = await self._get_fiscal_document(fiscal_document_id, tenant_id)
            company = await self._get_company(fiscal_doc.company_id, tenant_id)
            
            # Obtener motor fiscal
            engine = await self._get_engine_for_tenant(tenant_id, environment)
            
            # Preparar datos para consulta
            query_data = {
                "rut": company.rut,
                "cfe_type": fiscal_doc.document_type,
                "cfe_number": f"{fiscal_doc.series}{fiscal_doc.number}",
                "issue_date": fiscal_doc.issued_at.strftime("%Y-%m-%d") if fiscal_doc.issued_at else ""
            }
            
            # Consultar estado
            query_result = await engine.query_status(query_data)
            
            logger.info(
                "fiscal_core_query_status_success",
                fiscal_document_id=str(fiscal_document_id)
            )
            
            return query_result.engine_response or {}
            
        except FiscalEngineError as e:
            logger.error("fiscal_core_query_engine_error", error=str(e))
            raise FiscalCoreError(f"Fiscal engine error: {e}")
        except Exception as e:
            logger.error("fiscal_core_query_status_failed", error=str(e))
            raise FiscalCoreError(f"Failed to query fiscal document status: {e}")
    
    async def retry_fiscal_document(
        self,
        fiscal_document_id: uuid.UUID,
        tenant_id: uuid.UUID
    ) -> FiscalDocumentModel:
        """
        Reintenta el envío de un documento fiscal rechazado.
        
        Args:
            fiscal_document_id: ID del documento fiscal
            tenant_id: ID del tenant
            
        Returns:
            FiscalDocumentModel actualizado
            
        Raises:
            FiscalCoreError: Si hay error en el proceso
        """
        logger.info(
            "fiscal_core_retry_started",
            fiscal_document_id=str(fiscal_document_id)
        )
        
        try:
            fiscal_doc = await self._get_fiscal_document(fiscal_document_id, tenant_id)
            
            if fiscal_doc.state != FiscalState.REJECTED.value:
                raise FiscalCoreError(
                    f"Cannot retry fiscal document in state: {fiscal_doc.state}"
                )
            
            # Transición de estado
            self.state_machine.transition(
                FiscalState.REJECTED.value, 
                FiscalState.PENDING_SEND.value, 
                reason="retry"
            )
            fiscal_doc.state = FiscalState.PENDING_SEND.value
            await self.db.flush()
            
            logger.info(
                "fiscal_core_retry_success",
                fiscal_document_id=str(fiscal_document_id)
            )
            
            return fiscal_doc
            
        except Exception as e:
            logger.error("fiscal_core_retry_failed", error=str(e))
            raise FiscalCoreError(f"Failed to retry fiscal document: {e}")
    
    # Métodos auxiliares
    
    async def _get_engine_for_tenant(
        self, 
        tenant_id: uuid.UUID, 
        environment: Optional[str] = None
    ) -> IFiscalEngine:
        """
        Obtiene el motor fiscal configurado para el tenant.
        
        Lee la configuración del tenant para determinar qué motor fiscal usar.
        Si no hay configuración específica, usa DGI Uruguay por defecto.
        
        Args:
            tenant_id: ID del tenant
            environment: Entorno fiscal (opcional)
            
        Returns:
            Instancia de IFiscalEngine
        """
        # Obtener configuración del tenant
        stmt = select(Tenant).where(Tenant.id == tenant_id)
        result = await self.db.execute(stmt)
        tenant = result.scalar_one_or_none()
        
        if tenant:
            # Usar motor configurado en el tenant
            engine_id = tenant.fiscal_engine_id or "dgi_uruguay"
            fiscal_config = tenant.fiscal_config or {}
        else:
            # Fallback a DGI Uruguay
            engine_id = "dgi_uruguay"
            fiscal_config = {}
        
        # Obtener motor del registro
        engine = self.registry.get_engine(engine_id)
        
        # Si el motor soporta configuración de entorno, aplicarla
        if hasattr(engine, 'environment'):
            # Usar entorno del parámetro o de la configuración del tenant
            final_environment = environment or fiscal_config.get('environment', 'testing')
            engine.environment = final_environment
        
        logger.info(
            "fiscal_engine_selected",
            tenant_id=str(tenant_id),
            engine_id=engine_id,
            environment=getattr(engine, 'environment', None)
        )
        
        return engine
    
    async def _convert_to_fiscal_document_data(
        self,
        invoice: Invoice,
        company: Company,
        customer: Optional[Customer],
        items: list,
        certificate: Certificate
    ) -> FiscalDocumentData:
        """
        Convierte entidades del ERP a FiscalDocumentData normalizado.
        
        Args:
            invoice: Factura del ERP
            company: Compañía del ERP
            customer: Cliente del ERP (opcional)
            items: Items de factura
            certificate: Certificado fiscal
            
        Returns:
            FiscalDocumentData normalizado
        """
        # Convertir compañía
        fiscal_company = FiscalCompany(
            rut=company.rut,
            legal_name=company.legal_name,
            trade_name=getattr(company, 'trade_name', None),
            business_activity=getattr(company, 'business_activity', None),
            address=getattr(company, 'fiscal_address', None) or getattr(company, 'address', None),
            city=getattr(company, 'city', None),
            department=getattr(company, 'department', None),
            email=getattr(company, 'email', None),
            phone=getattr(company, 'phone', None),
            fiscal_address=getattr(company, 'fiscal_address', None),
            branch_code=getattr(company, 'dgi_branch_code', None),
            metadata=getattr(company, 'metadata_json', None)
        )
        
        # Convertir cliente si existe
        fiscal_customer = None
        if customer:
            fiscal_customer = FiscalCustomer(
                rut=getattr(customer, 'rut', None),
                legal_name=getattr(customer, 'legal_name', None),
                address=getattr(customer, 'address', None),
                city=getattr(customer, 'city', None),
                department=getattr(customer, 'department', None),
                email=getattr(customer, 'email', None),
                phone=getattr(customer, 'phone', None),
                metadata=getattr(customer, 'metadata_json', None)
            )
        
        # Convertir items
        fiscal_items = []
        for item in items:
            fiscal_items.append(FiscalDocumentItem(
                description=getattr(item, 'description', '') or f'Item {item.id}',
                quantity=Decimal(str(item.quantity)),
                unit_price=Decimal(str(item.unit_price)),
                discount=Decimal(str(getattr(item, 'discount', 0) or 0)),
                tax_amount=Decimal(str(getattr(item, 'tax_amount', 0) or 0)),
                tax_rate=None,  # Se puede calcular si es necesario
                metadata=getattr(item, 'metadata_json', None)
            ))
        
        # Convertir documento de referencia si existe
        reference_document = None
        invoice_metadata = getattr(invoice, 'metadata_json', None) or {}
        if isinstance(invoice_metadata, dict) and invoice_metadata.get('reference_document'):
            ref_data = invoice_metadata['reference_document']
            reference_document = ReferenceDocument(**ref_data)
        
        # Configuración del motor (certificado)
        engine_config = {
            'cert_path': certificate.metadata_json.get('cert_path') if certificate.metadata_json else None,
            'key_path': certificate.metadata_json.get('key_path') if certificate.metadata_json else None,
            'is_contingency': invoice_metadata.get('is_contingency', False)
        }
        
        # Crear documento fiscal normalizado
        return FiscalDocumentData(
            document_type=invoice.document_type,
            series=invoice.series,
            number=invoice.number,
            issue_date=invoice.issue_date.date() if invoice.issue_date else datetime.utcnow().date(),
            company=fiscal_company,
            customer=fiscal_customer,
            items=fiscal_items,
            currency=invoice.currency,
            exchange_rate=Decimal(str(invoice.exchange_rate)),
            subtotal=Decimal(str(invoice.subtotal)),
            tax_total=Decimal(str(invoice.tax_total)),
            discount_total=Decimal(str(invoice.discount_total)),
            total=Decimal(str(invoice.total)),
            payment_method=1,  # Por defecto
            notes=invoice.notes,
            reference_document=reference_document,
            engine_config=engine_config,
            metadata=invoice_metadata,
            invoice_id=str(invoice.id),
            tenant_id=str(invoice.tenant_id),
            company_id=str(invoice.company_id)
        )
    
    async def _save_issued_fiscal_document(
        self,
        fiscal_data: FiscalDocumentData,
        issue_result: FiscalDocumentResponse,
        tenant_id: uuid.UUID,
        request_id: Optional[str]
    ) -> FiscalDocumentModel:
        """
        Guarda un documento fiscal emitido en la base de datos.
        
        Args:
            fiscal_data: Datos del documento fiscal
            issue_result: Resultado de la emisión
            tenant_id: ID del tenant
            request_id: ID de request para tracking
            
        Returns:
            FiscalDocumentModel guardado
        """
        fiscal_doc = FiscalDocumentModel(
            tenant_id=tenant_id,
            company_id=uuid.UUID(fiscal_data.company_id) if fiscal_data.company_id else None,
            invoice_id=uuid.UUID(fiscal_data.invoice_id) if fiscal_data.invoice_id else None,
            document_type=issue_result.document_type or fiscal_data.document_type,
            series=fiscal_data.series,
            number=fiscal_data.number,
            state=FiscalState.PENDING_SIGN.value,
            issued_at=datetime.utcnow(),
            raw_payload={
                "cfe_xml": issue_result.generated_xml,
                "signed_xml": issue_result.signed_xml,
            }
        )
        
        self.db.add(fiscal_doc)
        await self.db.flush()
        
        # Actualizar estado a firmado
        self.state_machine.transition(FiscalState.DRAFT.value, FiscalState.PENDING_SIGN.value)
        fiscal_doc.state = FiscalState.PENDING_SIGN.value
        fiscal_doc.signed_at = datetime.utcnow()
        await self.db.flush()
        
        # Crear respuesta de emisión
        await self._save_fiscal_response(
            fiscal_doc.id,
            tenant_id,
            issue_result,
            request_id or str(uuid.uuid4())
        )
        
        await self.db.flush()
        return fiscal_doc
    
    async def _save_fiscal_response(
        self,
        fiscal_document_id: uuid.UUID,
        tenant_id: uuid.UUID,
        result: FiscalDocumentResponse,
        request_id: str
    ) -> FiscalResponse:
        """
        Guarda una respuesta fiscal en la base de datos.
        
        Args:
            fiscal_document_id: ID del documento fiscal
            tenant_id: ID del tenant
            result: Resultado de la operación fiscal
            request_id: ID del request
            
        Returns:
            FiscalResponse guardada
        """
        fiscal_doc = await self._get_fiscal_document(fiscal_document_id, tenant_id)
        
        response = FiscalResponse(
            tenant_id=tenant_id,
            company_id=fiscal_doc.company_id,
            fiscal_document_id=fiscal_document_id,
            request_id=request_id,
            status_code="success" if result.success else "error",
            status_message=result.error_message if not result.success else "Operation completed",
            raw_response=result.engine_response or {}
        )
        
        self.db.add(response)
        await self.db.flush()
        return response
    
    # Métodos de acceso a datos (reutilizan lógica existente)
    
    async def _get_invoice(self, invoice_id: uuid.UUID, tenant_id: uuid.UUID) -> Invoice:
        stmt = select(Invoice).where(
            Invoice.id == invoice_id,
            Invoice.tenant_id == tenant_id,
        )
        result = await self.db.execute(stmt)
        invoice = result.scalar_one_or_none()
        if not invoice:
            raise FiscalCoreError(f"Invoice {invoice_id} not found")
        return invoice
    
    async def _get_certificate(self, certificate_id: uuid.UUID, tenant_id: uuid.UUID) -> Certificate:
        stmt = select(Certificate).where(
            Certificate.id == certificate_id,
            Certificate.tenant_id == tenant_id,
            Certificate.is_active == True,
        )
        result = await self.db.execute(stmt)
        cert = result.scalar_one_or_none()
        if not cert:
            raise FiscalCoreError(f"Active certificate {certificate_id} not found")
        return cert
    
    async def _get_company(self, company_id: uuid.UUID, tenant_id: uuid.UUID) -> Company:
        stmt = select(Company).where(
            Company.id == company_id,
            Company.tenant_id == tenant_id,
        )
        result = await self.db.execute(stmt)
        company = result.scalar_one_or_none()
        if not company:
            raise FiscalCoreError(f"Company {company_id} not found")
        return company
    
    async def _get_customer(self, customer_id: uuid.UUID, tenant_id: uuid.UUID) -> Customer:
        stmt = select(Customer).where(
            Customer.id == customer_id,
            Customer.tenant_id == tenant_id,
        )
        result = await self.db.execute(stmt)
        customer = result.scalar_one_or_none()
        if not customer:
            raise FiscalCoreError(f"Customer {customer_id} not found")
        return customer
    
    async def _get_fiscal_document(self, fiscal_document_id: uuid.UUID, tenant_id: uuid.UUID) -> FiscalDocumentModel:
        stmt = select(FiscalDocumentModel).where(
            FiscalDocumentModel.id == fiscal_document_id,
            FiscalDocumentModel.tenant_id == tenant_id,
        )
        result = await self.db.execute(stmt)
        doc = result.scalar_one_or_none()
        if not doc:
            raise FiscalCoreError(f"Fiscal document {fiscal_document_id} not found")
        return doc
    
    async def _get_invoice_items(self, invoice_id: uuid.UUID, tenant_id: uuid.UUID) -> list:
        stmt = select(InvoiceItem).where(
            InvoiceItem.invoice_id == invoice_id,
            InvoiceItem.tenant_id == tenant_id,
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()