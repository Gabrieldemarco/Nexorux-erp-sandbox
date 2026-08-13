import uuid
import pytest
from fastapi import HTTPException

from app.api.v1.endpoints.fiscal_documents import (
    create_fiscal_document,
    list_fiscal_documents,
    get_fiscal_document,
    update_fiscal_document,
    delete_fiscal_document,
    issue_fiscal_document,
    send_fiscal_document,
    query_fiscal_document_status,
    retry_fiscal_document,
)
from app.schemas.fiscal_document import (
    FiscalDocumentCreate,
    FiscalDocumentUpdate,
    FiscalDocumentIssueRequest,
    FiscalDocumentSendRequest,
    FiscalDocumentRetryRequest,
)
from app.services.fiscal.engine import FiscalEngine, FiscalEngineError, FiscalDocumentNotFoundError


class FakeFiscalEngine:
    def __init__(self, fiscal_doc=None, response=None, raise_on_issue=None, raise_on_send=None, raise_on_query=None, raise_on_retry=None):
        self.fiscal_doc = fiscal_doc
        self.response = response or {}
        self.raise_on_issue = raise_on_issue
        self.raise_on_send = raise_on_send
        self.raise_on_query = raise_on_query
        self.raise_on_retry = raise_on_retry
        self.issue_calls = []
        self.send_calls = []
        self.query_calls = []
        self.retry_calls = []

    async def issue_cfe(self, invoice_id, certificate_id, tenant_id, request_id=None):
        self.issue_calls.append({
            "invoice_id": invoice_id,
            "certificate_id": certificate_id,
            "tenant_id": tenant_id,
            "request_id": request_id,
        })
        if self.raise_on_issue:
            raise self.raise_on_issue
        return self.fiscal_doc

    async def send_cfe(self, fiscal_document_id, tenant_id, environment=None, certificate_id=None):
        self.send_calls.append({
            "fiscal_document_id": fiscal_document_id,
            "tenant_id": tenant_id,
            "environment": environment,
            "certificate_id": certificate_id,
        })
        if self.raise_on_send:
            raise self.raise_on_send
        return self.response

    async def query_status(self, fiscal_document_id, tenant_id, environment=None):
        self.query_calls.append({
            "fiscal_document_id": fiscal_document_id,
            "tenant_id": tenant_id,
            "environment": environment,
        })
        if self.raise_on_query:
            raise self.raise_on_query
        return self.response

    async def retry_cfe(self, fiscal_document_id, tenant_id):
        self.retry_calls.append({
            "fiscal_document_id": fiscal_document_id,
            "tenant_id": tenant_id,
        })
        if self.raise_on_retry:
            raise self.raise_on_retry
        return self.fiscal_doc


@pytest.mark.asyncio
async def test_fiscal_document_crud(fake_db, fake_user, fake_tenant, fake_company):
    from datetime import datetime, timezone

    from app.models.invoice import Invoice

    invoice = Invoice(
        tenant_id=fake_tenant.id,
        company_id=fake_company.id,
        document_type="111",
        series="A",
        number="0001-00000001",
        status="draft",
        issue_date=datetime.now(timezone.utc),
        due_date=datetime.now(timezone.utc),
        subtotal=100,
        tax_total=22,
        discount_total=0,
        total=122,
        currency="UYU",
        exchange_rate=1,
    )
    fake_db.add(invoice)
    await fake_db.commit()

    doc_data = FiscalDocumentCreate(
        tenant_id=fake_tenant.id,
        company_id=fake_company.id,
        invoice_id=invoice.id,
        document_type="111",
        series="A",
        number="0001-00000001",
        state="draft",
    )
    doc = await create_fiscal_document(doc_data, fake_db, fake_user)
    assert doc is not None
    assert doc.document_type == "111"

    docs = await list_fiscal_documents(db=fake_db, current_user=fake_user)
    assert len(docs) == 1

    found = await get_fiscal_document(str(doc.id), fake_db, fake_user)
    assert found.id == doc.id

    update_data = FiscalDocumentUpdate(state="pending_sign")
    updated = await update_fiscal_document(str(doc.id), update_data, fake_db, fake_user)
    assert updated.state == "pending_sign"

    await delete_fiscal_document(str(doc.id), fake_db, fake_user)
    docs = await list_fiscal_documents(db=fake_db, current_user=fake_user)
    assert len(docs) == 0


@pytest.mark.asyncio
async def test_issue_fiscal_document_success(fake_db, fake_user, fake_tenant, fake_company):
    from app.models.fiscal_document import FiscalDocument
    doc = FiscalDocument(
        tenant_id=fake_tenant.id,
        company_id=fake_company.id,
        invoice_id=str(uuid.uuid4()),
        document_type="111",
        series="A",
        number="0001-00000001",
        state="draft",
    )
    doc.id = uuid.uuid4()
    fake_db._store.setdefault("fiscal_document", []).append(doc)

    fake_engine = FakeFiscalEngine(fiscal_doc=doc)

    original_init = FiscalEngine.__init__
    def fake_init(self, db):
        self.db = db
        self.state_machine = None
        self.issue_cfe = fake_engine.issue_cfe
        self.send_cfe = fake_engine.send_cfe
        self.query_status = fake_engine.query_status
        self.retry_cfe = fake_engine.retry_cfe

    FiscalEngine.__init__ = fake_init
    try:
        payload = FiscalDocumentIssueRequest(certificate_id=uuid.uuid4())
        result = await issue_fiscal_document(str(doc.id), payload, fake_db, fake_user)
        assert result.id == doc.id
        assert len(fake_engine.issue_calls) == 1
        assert fake_engine.issue_calls[0]["tenant_id"] == fake_user.tenant_id
    finally:
        FiscalEngine.__init__ = original_init


@pytest.mark.asyncio
async def test_issue_fiscal_document_not_found(fake_db, fake_user, fake_tenant, fake_company):
    fake_engine = FakeFiscalEngine(raise_on_issue=FiscalDocumentNotFoundError("not found"))

    original_init = FiscalEngine.__init__
    def fake_init(self, db):
        self.db = db
        self.state_machine = None
        self.issue_cfe = fake_engine.issue_cfe

    FiscalEngine.__init__ = fake_init
    try:
        payload = FiscalDocumentIssueRequest(certificate_id=uuid.uuid4())
        with pytest.raises(HTTPException) as excinfo:
            await issue_fiscal_document(str(uuid.uuid4()), payload, fake_db, fake_user)
        assert excinfo.value.status_code == 404
    finally:
        FiscalEngine.__init__ = original_init


@pytest.mark.asyncio
async def test_send_fiscal_document_success(fake_db, fake_user, fake_tenant, fake_company):
    from app.models.fiscal_document import FiscalDocument
    doc = FiscalDocument(
        tenant_id=fake_tenant.id,
        company_id=fake_company.id,
        invoice_id=str(uuid.uuid4()),
        document_type="111",
        series="A",
        number="0001-00000001",
        state="pending_send",
    )
    doc.id = uuid.uuid4()

    fake_db._store.setdefault("fiscal_document", []).append(doc)

    class FakeTask:
        id = "fake-task-id"

    import app.api.v1.endpoints.fiscal_documents as fiscal_endpoints
    original_delay = fiscal_endpoints.send_cfe_async.delay
    fiscal_endpoints.send_cfe_async.delay = lambda *args, **kwargs: FakeTask()
    try:
        payload = FiscalDocumentSendRequest(environment="testing")
        result = await send_fiscal_document(str(doc.id), payload, fake_db, fake_user)
        assert result.task_id == "fake-task-id"
        assert result.status == "queued"
        assert result.fiscal_document_id == doc.id
    finally:
        fiscal_endpoints.send_cfe_async.delay = original_delay


@pytest.mark.asyncio
async def test_query_fiscal_document_status_success(fake_db, fake_user, fake_tenant, fake_company):
    fake_engine = FakeFiscalEngine(response={"status_code": "aceptado", "status_message": "OK"})

    original_init = FiscalEngine.__init__
    def fake_init(self, db):
        self.db = db
        self.state_machine = None
        self.query_status = fake_engine.query_status

    FiscalEngine.__init__ = fake_init
    try:
        result = await query_fiscal_document_status(str(uuid.uuid4()), db=fake_db, current_user=fake_user)
        assert result["status_code"] == "aceptado"
        assert len(fake_engine.query_calls) == 1
    finally:
        FiscalEngine.__init__ = original_init


@pytest.mark.asyncio
async def test_retry_fiscal_document_success(fake_db, fake_user, fake_tenant, fake_company):
    from app.models.fiscal_document import FiscalDocument
    doc = FiscalDocument(
        tenant_id=fake_tenant.id,
        company_id=fake_company.id,
        invoice_id=str(uuid.uuid4()),
        document_type="111",
        series="A",
        number="0001-00000001",
        state="rejected",
    )
    doc.id = uuid.uuid4()

    fake_engine = FakeFiscalEngine(fiscal_doc=doc)

    original_init = FiscalEngine.__init__
    def fake_init(self, db):
        self.db = db
        self.state_machine = None
        self.retry_cfe = fake_engine.retry_cfe

    FiscalEngine.__init__ = fake_init
    try:
        payload = FiscalDocumentRetryRequest()
        result = await retry_fiscal_document(str(doc.id), payload, fake_db, fake_user)
        assert result.id == doc.id
        assert len(fake_engine.retry_calls) == 1
    finally:
        FiscalEngine.__init__ = original_init
