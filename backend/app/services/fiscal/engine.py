import structlog
import uuid
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Optional, Dict, Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.invoice import Invoice
from app.models.invoice_item import InvoiceItem
from app.models.company import Company
from app.models.customer import Customer
from app.models.certificate import Certificate
from app.models.fiscal_document import FiscalDocument
from app.models.fiscal_response import FiscalResponse
from app.services.fiscal.cfe_types import CFEType, CFE_TYPE_INFO, is_note, resolve_document_type, get_parent_type
from app.services.fiscal.xml_builder import build_cfe_xml
from app.services.fiscal.xsd_validator import validate_cfe_xml_or_raise, CFEValidationError, DEFAULT_XSD_PATH
from app.services.fiscal.signer import load_certificate, load_private_key, sign_xml, CertificateError, SigningError
from app.services.fiscal.dgi_client import DGIClient, DGIError
from app.services.fiscal.state_machine import FiscalStateMachine, FiscalState, StateTransitionError
from app.core.config import settings

logger = structlog.get_logger(__name__)


class FiscalEngineError(Exception):
    """Base exception for fiscal engine errors."""

class FiscalDocumentNotFoundError(FiscalEngineError):
    """Raised when a fiscal document is not found."""


class FiscalEngine:
    """Main fiscal engine orchestrating CFE generation, signing, sending, and state updates."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.state_machine = FiscalStateMachine()

    async def issue_cfe(
        self,
        invoice_id: uuid.UUID,
        certificate_id: uuid.UUID,
        tenant_id: uuid.UUID,
        request_id: Optional[str] = None,
    ) -> FiscalDocument:
        logger.info(
            "issue_cfe_started",
            invoice_id=str(invoice_id),
            certificate_id=str(certificate_id),
            tenant_id=str(tenant_id),
        )

        invoice = await self._get_invoice(invoice_id, tenant_id)
        certificate = await self._get_certificate(certificate_id, tenant_id)
        company = await self._get_company(invoice.company_id, tenant_id)
        customer = await self._get_customer(invoice.customer_id, tenant_id) if invoice.customer_id else None

        cert_path = certificate.metadata_json.get("cert_path") if certificate.metadata_json else None
        key_path = certificate.metadata_json.get("key_path") if certificate.metadata_json else None
        if not cert_path or not key_path:
            raise FiscalEngineError("Certificate metadata must include cert_path and key_path")
        if certificate.expires_at and certificate.expires_at < datetime.utcnow():
            raise FiscalEngineError("Certificate is expired")
        if not Path(cert_path).exists():
            raise FiscalEngineError(f"Certificate file not found: {cert_path}")
        if not Path(key_path).exists():
            raise FiscalEngineError(f"Private key file not found: {key_path}")

        stmt = (
            select(InvoiceItem)
            .where(InvoiceItem.invoice_id == invoice_id)
            .where(InvoiceItem.tenant_id == tenant_id)
        )
        result = await self.db.execute(stmt)
        items = result.scalars().all()

        document_type = resolve_document_type(
            invoice.document_type,
            is_contingency=bool((getattr(invoice, "metadata_json", None) or {}).get("is_contingency")),
        )
        cfe_number = f"{invoice.series}{invoice.number}"
        issue_date = invoice.issue_date.date() if invoice.issue_date else date.today()

        reference_document = await self._resolve_reference_document(
            invoice=invoice,
            document_type=document_type,
            tenant_id=tenant_id,
            fallback_issue_date=issue_date,
        )

        try:
            xml_bytes = build_cfe_xml(
                invoice=invoice,
                company=company,
                customer=customer,
                items=items,
                document_type=document_type,
                cfe_number=cfe_number,
                issue_date=issue_date,
                currency=invoice.currency,
                exchange_rate=Decimal(str(invoice.exchange_rate)),
                notes=invoice.notes,
                reference_document=reference_document,
            )
        except Exception as e:
            logger.error("cfe_xml_build_failed", error=str(e))
            raise FiscalEngineError(f"Failed to build CFE XML: {e}")

        xsd_path = Path(settings.CFE_XSD_PATH) if settings.CFE_XSD_PATH else None

        try:
            validate_cfe_xml_or_raise(
                xml_bytes,
                xsd_path=xsd_path,
                require_xsd=settings.CFE_XSD_VALIDATION_REQUIRED,
                validate_xsd=False,
            )
        except CFEValidationError as e:
            logger.error("cfe_structural_validation_failed", errors=e.errors)
            raise FiscalEngineError(f"CFE XML validation failed: {'; '.join(e.errors)}")

        cert, cert_data = load_certificate(cert_path)
        private_key = load_private_key(key_path)

        try:
            signed_xml = sign_xml(xml_bytes, private_key, cert, cert_data)
        except (CertificateError, SigningError) as e:
            logger.error("cfe_signing_failed", error=str(e))
            raise FiscalEngineError(f"Failed to sign CFE XML: {e}")

        if settings.CFE_XSD_VALIDATION_REQUIRED or (xsd_path and xsd_path.exists()) or DEFAULT_XSD_PATH.exists():
            try:
                validate_cfe_xml_or_raise(
                    signed_xml,
                    xsd_path=xsd_path,
                    require_xsd=settings.CFE_XSD_VALIDATION_REQUIRED,
                    validate_xsd=True,
                )
            except CFEValidationError as e:
                logger.error("cfe_xsd_validation_failed", errors=e.errors)
                raise FiscalEngineError(f"CFE XML validation failed: {'; '.join(e.errors)}")

        fiscal_doc = FiscalDocument(
            tenant_id=tenant_id,
            company_id=invoice.company_id,
            invoice_id=invoice_id,
            document_type=document_type,
            series=invoice.series,
            number=invoice.number,
            state=FiscalState.PENDING_SIGN.value,
            issued_at=datetime.utcnow(),
            raw_payload={
                "cfe_xml": xml_bytes.decode("utf-8", errors="replace"),
                "signed_xml": signed_xml.decode("utf-8", errors="replace"),
            },
        )
        self.db.add(fiscal_doc)
        await self.db.flush()

        self.state_machine.transition(FiscalState.DRAFT.value, FiscalState.PENDING_SIGN.value)
        fiscal_doc.state = FiscalState.PENDING_SIGN.value
        fiscal_doc.signed_at = datetime.utcnow()
        await self.db.flush()

        await self._create_response(
            fiscal_document_id=fiscal_doc.id,
            tenant_id=tenant_id,
            request_id=request_id or str(uuid.uuid4()),
            status_code="signed",
            status_message="CFE signed successfully",
            raw_response={"signed_xml_length": len(signed_xml)},
        )

        await self.db.flush()
        logger.info("cfe_issued_successfully", fiscal_document_id=str(fiscal_doc.id))
        return fiscal_doc

    async def send_cfe(
        self,
        fiscal_document_id: uuid.UUID,
        tenant_id: uuid.UUID,
        environment: Optional[str] = None,
        certificate_id: Optional[uuid.UUID] = None,
    ) -> Dict[str, Any]:
        logger.info(
            "send_cfe_started",
            fiscal_document_id=str(fiscal_document_id),
            tenant_id=str(tenant_id),
        )

        fiscal_doc = await self._get_fiscal_document(fiscal_document_id, tenant_id)

        if self.state_machine.is_terminal(fiscal_doc.state):
            raise FiscalEngineError(f"Cannot send CFE in terminal state: {fiscal_doc.state}")

        self.state_machine.transition(fiscal_doc.state, FiscalState.PENDING_SEND.value)

        cert_data = None
        if certificate_id:
            cert = await self._get_certificate(certificate_id, tenant_id)
            cert_path = cert.metadata_json.get("cert_path", "")
            _, cert_data = load_certificate(cert_path)

        cfe_env = settings.DGI_ENVIRONMENT if environment is None else environment

        async with DGIClient(environment=cfe_env, certificate_data=cert_data) as client:
            try:
                signed_xml_bytes = fiscal_doc.raw_payload.get("signed_xml", b"")
                if isinstance(signed_xml_bytes, str):
                    signed_xml_bytes = signed_xml_bytes.encode("utf-8")

                response = await client.send_cfe_envelope(signed_xml_bytes)
            except DGIError as e:
                logger.error("dgi_send_failed", error=str(e))
                fiscal_doc.state = FiscalState.REJECTED.value
                fiscal_doc.response_at = datetime.utcnow()
                await self._create_response(
                    fiscal_document_id=fiscal_document_id,
                    tenant_id=tenant_id,
                    request_id=str(uuid.uuid4()),
                    status_code="error",
                    status_message=str(e),
                    raw_response={"error": str(e)},
                )
                await self.db.flush()
                raise FiscalEngineError(f"DGI send failed: {e}")

        fiscal_doc.state = FiscalState.SENT.value
        fiscal_doc.sent_at = datetime.utcnow()
        fiscal_doc.response_at = datetime.utcnow()
        await self.db.flush()

        status_code = response.get("status_code", "unknown")
        status_message = response.get("status_message", "")

        if status_code.lower() in ("aceptado", "ok", "0", "success"):
            fiscal_doc.state = FiscalState.ACCEPTED.value
        elif status_code.lower() in ("rechazado", "error", "1"):
            fiscal_doc.state = FiscalState.REJECTED.value

        await self._create_response(
            fiscal_document_id=fiscal_document_id,
            tenant_id=tenant_id,
            request_id=response.get("response_id", str(uuid.uuid4())),
            status_code=status_code,
            status_message=status_message,
            raw_response=response,
        )

        await self.db.flush()
        logger.info(
            "cfe_sent_successfully",
            fiscal_document_id=str(fiscal_document_id),
            dgi_status=status_code,
        )
        return response

    async def query_status(
        self,
        fiscal_document_id: uuid.UUID,
        tenant_id: uuid.UUID,
        environment: Optional[str] = None,
    ) -> Dict[str, Any]:
        logger.info(
            "query_cfe_status_started",
            fiscal_document_id=str(fiscal_document_id),
            tenant_id=str(tenant_id),
        )

        fiscal_doc = await self._get_fiscal_document(fiscal_document_id, tenant_id)
        company = await self._get_company(fiscal_doc.company_id, tenant_id)

        cfe_env = settings.DGI_ENVIRONMENT if environment is None else environment
        async with DGIClient(environment=cfe_env) as client:
            try:
                response = await client.query_cfe_status(
                    rut=company.rut,
                    cfe_type=fiscal_doc.document_type,
                    cfe_number=f"{fiscal_doc.series}{fiscal_doc.number}",
                    issue_date=fiscal_doc.issued_at.strftime("%Y-%m-%d") if fiscal_doc.issued_at else "",
                )
            except DGIError as e:
                logger.error("dgi_query_failed", error=str(e))
                raise FiscalEngineError(f"DGI query failed: {e}")

        logger.info("cfe_status_queried", response=response)
        return response

    async def retry_cfe(
        self,
        fiscal_document_id: uuid.UUID,
        tenant_id: uuid.UUID,
    ) -> FiscalDocument:
        logger.info(
            "retry_cfe_started",
            fiscal_document_id=str(fiscal_document_id),
            tenant_id=str(tenant_id),
        )

        fiscal_doc = await self._get_fiscal_document(fiscal_document_id, tenant_id)

        if fiscal_doc.state != FiscalState.REJECTED.value:
            raise FiscalEngineError(f"Cannot retry CFE in state: {fiscal_doc.state}")

        self.state_machine.transition(FiscalState.REJECTED.value, FiscalState.PENDING_SEND.value, reason="retry")
        fiscal_doc.state = FiscalState.PENDING_SEND.value
        await self.db.flush()

        logger.info("cfe_retry_successful", fiscal_document_id=str(fiscal_document_id))
        return fiscal_doc

    async def _resolve_reference_document(
        self,
        invoice: Invoice,
        document_type: str,
        tenant_id: uuid.UUID,
        fallback_issue_date: date,
    ) -> Optional[Dict[str, Any]]:
        if not is_note(document_type):
            return None

        metadata = getattr(invoice, "metadata_json", None) or {}
        if isinstance(metadata, dict) and metadata.get("reference_document"):
            return metadata["reference_document"]

        parent_invoice_id = metadata.get("parent_invoice_id") if isinstance(metadata, dict) else None
        if parent_invoice_id:
            parent = await self._get_invoice(uuid.UUID(str(parent_invoice_id)), tenant_id)
            return {
                "document_type": get_parent_type(document_type),
                "series": parent.series,
                "number": parent.number,
                "cfe_number": f"{parent.series}{parent.number}",
                "issue_date": parent.issue_date.date() if parent.issue_date else fallback_issue_date,
                "reason": metadata.get("reference_reason"),
            }

        raise FiscalEngineError(
            "Credit/debit notes require reference_document or parent_invoice_id in invoice.metadata_json"
        )

    async def _get_invoice(self, invoice_id: uuid.UUID, tenant_id: uuid.UUID) -> Invoice:
        stmt = select(Invoice).where(
            Invoice.id == invoice_id,
            Invoice.tenant_id == tenant_id,
        )
        result = await self.db.execute(stmt)
        invoice = result.scalar_one_or_none()
        if not invoice:
            raise FiscalDocumentNotFoundError(f"Invoice {invoice_id} not found")
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
            raise FiscalDocumentNotFoundError(f"Active certificate {certificate_id} not found")
        return cert

    async def _get_company(self, company_id: uuid.UUID, tenant_id: uuid.UUID) -> Company:
        stmt = select(Company).where(
            Company.id == company_id,
            Company.tenant_id == tenant_id,
        )
        result = await self.db.execute(stmt)
        company = result.scalar_one_or_none()
        if not company:
            raise FiscalDocumentNotFoundError(f"Company {company_id} not found")
        return company

    async def _get_customer(self, customer_id: uuid.UUID, tenant_id: uuid.UUID) -> Customer:
        stmt = select(Customer).where(
            Customer.id == customer_id,
            Customer.tenant_id == tenant_id,
        )
        result = await self.db.execute(stmt)
        customer = result.scalar_one_or_none()
        if not customer:
            raise FiscalDocumentNotFoundError(f"Customer {customer_id} not found")
        return customer

    async def _get_fiscal_document(self, fiscal_document_id: uuid.UUID, tenant_id: uuid.UUID) -> FiscalDocument:
        stmt = select(FiscalDocument).where(
            FiscalDocument.id == fiscal_document_id,
            FiscalDocument.tenant_id == tenant_id,
        )
        result = await self.db.execute(stmt)
        doc = result.scalar_one_or_none()
        if not doc:
            raise FiscalDocumentNotFoundError(f"Fiscal document {fiscal_document_id} not found")
        return doc

    async def _create_response(
        self,
        fiscal_document_id: uuid.UUID,
        tenant_id: uuid.UUID,
        request_id: str,
        status_code: str,
        status_message: str,
        raw_response: Optional[Dict[str, Any]] = None,
    ) -> FiscalResponse:
        fiscal_doc = await self._get_fiscal_document(fiscal_document_id, tenant_id)

        response = FiscalResponse(
            tenant_id=tenant_id,
            company_id=fiscal_doc.company_id,
            fiscal_document_id=fiscal_document_id,
            request_id=request_id,
            status_code=status_code,
            status_message=status_message,
            raw_response=raw_response or {},
        )
        self.db.add(response)
        await self.db.flush()
        return response
