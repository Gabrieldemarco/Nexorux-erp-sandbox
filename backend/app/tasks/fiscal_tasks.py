import asyncio
import logging
import uuid
from datetime import datetime
from typing import Optional

from app.core.celery_app import celery_app
from app.core.config import settings
from app.services.fiscal.engine import FiscalEngine, FiscalEngineError, FiscalDocumentNotFoundError
from app.models.fiscal_document import FiscalDocument
from app.services.fiscal.state_machine import FiscalState
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

logger = logging.getLogger(__name__)

_async_engine = None
_async_session_factory = None


def _get_async_session() -> AsyncSession:
    global _async_engine, _async_session_factory
    if _async_engine is None:
        _async_engine = create_async_engine(settings.DATABASE_URL, future=True)
        _async_session_factory = sessionmaker(
            _async_engine, class_=AsyncSession, expire_on_commit=False
        )
    return _async_session_factory()


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def send_cfe_async(self, fiscal_document_id: str, tenant_id: str, environment: Optional[str] = None, certificate_id: Optional[str] = None):
    """Celery task to send a CFE document to DGI asynchronously."""
    try:
        asyncio.run(_send_cfe_impl(fiscal_document_id, tenant_id, environment, certificate_id))
    except Exception as exc:
        logger.error("send_cfe_async_failed", fiscal_document_id=fiscal_document_id, error=str(exc))
        try:
            self.retry(exc=exc)
        except Exception:
            asyncio.run(_mark_failed(fiscal_document_id, tenant_id, str(exc)))


async def _send_cfe_impl(fiscal_document_id: str, tenant_id: str, environment: Optional[str], certificate_id: Optional[str]):
    async with _get_async_session() as db:
        try:
            fiscal_doc = await _get_fiscal_document(db, fiscal_document_id, tenant_id)
            if fiscal_doc.state in (FiscalState.SENT.value, FiscalState.ACCEPTED.value):
                logger.info("send_cfe_skipped_already_sent", fiscal_document_id=fiscal_document_id)
                return

            engine = FiscalEngine(db)
            response = await engine.send_cfe(
                fiscal_document_id=fiscal_doc.id,
                tenant_id=fiscal_doc.tenant_id,
                environment=environment,
                certificate_id=uuid.UUID(certificate_id) if certificate_id else None,
            )
            await db.commit()
            logger.info("send_cfe_async_success", fiscal_document_id=fiscal_document_id, response=response)
            return response
        except (FiscalEngineError, FiscalDocumentNotFoundError) as exc:
            await db.rollback()
            await _mark_failed(fiscal_document_id, tenant_id, str(exc))
            raise


async def _get_fiscal_document(db: AsyncSession, fiscal_document_id: str, tenant_id: str) -> FiscalDocument:
    stmt = select(FiscalDocument).where(
        FiscalDocument.id == uuid.UUID(fiscal_document_id),
        FiscalDocument.tenant_id == uuid.UUID(tenant_id),
    )
    result = await db.execute(stmt)
    doc = result.scalar_one_or_none()
    if not doc:
        raise FiscalDocumentNotFoundError(f"Fiscal document {fiscal_document_id} not found")
    return doc


async def _mark_failed(fiscal_document_id: str, tenant_id: str, error_message: str):
    async with _get_async_session() as db:
        try:
            fiscal_doc = await _get_fiscal_document(db, fiscal_document_id, tenant_id)
            fiscal_doc.state = FiscalState.REJECTED.value
            fiscal_doc.response_at = datetime.utcnow()
            await db.commit()
            logger.info("send_cfe_marked_failed", fiscal_document_id=fiscal_document_id, error=error_message)
        except Exception:
            await db.rollback()
            raise
