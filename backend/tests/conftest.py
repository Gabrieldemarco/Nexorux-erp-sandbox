import os
import sys
import uuid

import pytest

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from app.models.company import Company
from app.models.tenant import Tenant
from app.models.user import User
from app.core.security import get_password_hash


class FakeScaler:
    def __init__(self, values):
        self._values = values

    def all(self):
        return self._values


class FakeResult:
    def __init__(self, scalar=None, scalars=None, rowcount=None):
        self._scalar = scalar
        self._scalars = scalars or []
        self.rowcount = rowcount if rowcount is not None else len(self._scalars)

    def scalar_one_or_none(self):
        return self._scalar

    def scalar(self):
        if self._scalar is not None and not self._scalars:
            return self._scalar
        if self._scalars and self._scalar is None:
            return len(self._scalars)
        return self._scalar

    def scalars(self):
        return FakeScaler(self._scalars)


class FakeSession:
    def __init__(self, users=None, companies=None, tenants=None):
        self._store = {}
        self.added = []
        self.committed = False

        if tenants:
            self._store.setdefault("tenant", []).extend(tenants)
        if companies:
            self._store.setdefault("company", []).extend(companies)
        if users:
            self._store.setdefault("user", []).extend(users)

    def _ensure_id(self, obj):
        if getattr(obj, "id", None) is None:
            try:
                obj.id = uuid.uuid4()
            except Exception:
                pass

    def add(self, obj):
        self._ensure_id(obj)
        self.added.append(obj)
        table_name = getattr(obj, "__tablename__", None)
        if table_name:
            self._store.setdefault(table_name, []).append(obj)

    async def commit(self):
        self.committed = True

    async def rollback(self):
        return None

    async def flush(self):
        return None

    async def refresh(self, obj):
        return obj

    async def delete(self, obj):
        table_name = getattr(obj, "__tablename__", None)
        if table_name and table_name in self._store:
            try:
                self._store[table_name].remove(obj)
            except ValueError:
                pass

    async def execute(self, stmt, *args, **kwargs):
        from sqlalchemy.sql.dml import Delete
        from sqlalchemy.sql.elements import BinaryExpression, BooleanClauseList, UnaryExpression

        def _value(expr_right):
            return getattr(expr_right, "value", expr_right)

        def _resolve_column_name(left):
            name = getattr(left, "name", None)
            if name in ("lower", "upper"):
                clauses = getattr(left, "clauses", None)
                try:
                    first = clauses[0] if clauses is not None else None
                except Exception:
                    first = None
                if first is not None:
                    return getattr(first, "name", None)
                elem = getattr(left, "clause_expr", None) or getattr(left, "element", None)
                return getattr(elem, "name", None)
            return name

        def _match_record(record, left, right_value, operator=None):
            column_name = _resolve_column_name(left)
            op_name = getattr(operator, "__name__", "") if operator else ""

            if column_name == "password_reset_token_expires_at":
                left_val = getattr(record, "password_reset_token_expires_at", None)
                if op_name in ("gt", ">"):
                    return left_val is not None and left_val > right_value
                if op_name in ("lt", "<"):
                    return left_val is not None and left_val < right_value
                if right_value is None and op_name in ("ne", "is_not", "isnot", "is_distinct_from"):
                    return left_val is not None
                return left_val == right_value

            if column_name == "password_reset_token_hash":
                return getattr(record, "password_reset_token_hash", None) == right_value

            if column_name == "email":
                return (record.email or "").lower() == str(right_value or "").lower()
            if column_name == "username":
                return record.username == right_value
            if column_name == "id":
                return record.id == right_value or (
                    isinstance(right_value, str) and str(record.id) == right_value
                )
            if column_name == "tenant_id":
                return record.tenant_id == right_value or (
                    isinstance(right_value, str) and str(record.tenant_id) == right_value
                )
            if column_name == "company_id":
                return record.company_id == right_value or (
                    isinstance(right_value, str) and str(record.company_id) == right_value
                )
            if column_name == "customer_id":
                return getattr(record, "customer_id", None) == right_value or (
                    isinstance(right_value, str) and str(getattr(record, "customer_id", None) or "") == right_value
                )
            if column_name == "invoice_id":
                return getattr(record, "invoice_id", None) == right_value or (
                    isinstance(right_value, str) and str(getattr(record, "invoice_id", None) or "") == right_value
                )
            if column_name == "product_id":
                return getattr(record, "product_id", None) == right_value or (
                    isinstance(right_value, str) and str(getattr(record, "product_id", None) or "") == right_value
                )
            if column_name == "branch_id":
                return getattr(record, "branch_id", None) == right_value or (
                    isinstance(right_value, str) and str(getattr(record, "branch_id", None) or "") == right_value
                )
            if column_name == "warehouse_id":
                return getattr(record, "warehouse_id", None) == right_value or (
                    isinstance(right_value, str) and str(getattr(record, "warehouse_id", None) or "") == right_value
                )
            if column_name == "reference_id":
                return getattr(record, "reference_id", None) == right_value or (
                    isinstance(right_value, str) and str(getattr(record, "reference_id", None) or "") == right_value
                )
            if column_name == "reference_type":
                return getattr(record, "reference_type", None) == right_value
            if column_name == "sku":
                return getattr(record, "sku", None) == right_value
            if column_name == "is_active":
                return bool(getattr(record, "is_active", None)) == bool(right_value)
            if column_name == "fiscal_document_id":
                return getattr(record, "fiscal_document_id", None) == right_value or (
                    isinstance(right_value, str) and str(getattr(record, "fiscal_document_id", None) or "") == right_value
                )
            if column_name == "user_id":
                return getattr(record, "user_id", None) == right_value or (
                    isinstance(right_value, str) and str(getattr(record, "user_id", None) or "") == right_value
                )
            if column_name == "role_id":
                return getattr(record, "role_id", None) == right_value or (
                    isinstance(right_value, str) and str(getattr(record, "role_id", None) or "") == right_value
                )
            if column_name == "permission_id":
                return getattr(record, "permission_id", None) == right_value or (
                    isinstance(right_value, str) and str(getattr(record, "permission_id", None) or "") == right_value
                )
            return False

        def _evaluate(record, clause):
            if clause is None:
                return True
            if isinstance(clause, BooleanClauseList):
                results = [_evaluate(record, sub) for sub in clause.clauses]
                is_or = getattr(clause.operator, '__name__', '') == 'or_'
                if is_or:
                    return any(results)
                return all(results)
            if isinstance(clause, UnaryExpression):
                # IS NOT NULL / NOT
                element = getattr(clause, "element", None)
                column_name = _resolve_column_name(element) if element is not None else None
                if column_name == "password_reset_token_expires_at":
                    return getattr(record, "password_reset_token_expires_at", None) is not None
                return True
            if isinstance(clause, BinaryExpression):
                right_value = _value(clause.right)
                return _match_record(record, clause.left, right_value, operator=clause.operator)
            if hasattr(clause, "clauses"):
                return all(_evaluate(record, sub) for sub in getattr(clause, "clauses"))
            return True

        if isinstance(stmt, Delete):
            table = getattr(stmt, "table", None)
            table_name = getattr(table, "name", None) if table is not None else None
            records = list(self._store.get(table_name, []))
            whereclause = getattr(stmt, "_whereclause", None)
            kept = []
            deleted = 0
            for record in records:
                if whereclause is None or _evaluate(record, whereclause):
                    deleted += 1
                else:
                    kept.append(record)
            if table_name:
                self._store[table_name] = kept
            return FakeResult(scalars=[], rowcount=deleted)

        table_name = None
        if hasattr(stmt, "column_descriptions") and stmt.column_descriptions:
            first_desc = stmt.column_descriptions[0]
            model = first_desc.get("entity") or first_desc.get("type") or first_desc.get("expr")
            if hasattr(model, "__tablename__"):
                table_name = model.__tablename__
            elif hasattr(model, "__name__"):
                table_name = model.__name__.lower()

        if not table_name and hasattr(stmt, "_raw_columns") and stmt._raw_columns:
            first_col = stmt._raw_columns[0]
            if hasattr(first_col, "table") and first_col.table is not None:
                table_name = first_col.table.name

        records = self._store.get(table_name, [])
        whereclause = getattr(stmt, "_whereclause", None)

        if whereclause is None:
            result = records
        else:
            result = [record for record in records if _evaluate(record, whereclause)]

        offset = getattr(stmt, "_offset", None) or 0
        limit = getattr(stmt, "_limit", None)
        if isinstance(limit, int):
            result = result[offset:offset + limit]
        elif isinstance(offset, int) and offset:
            result = result[offset:]

        return FakeResult(scalar=result[0] if result else None, scalars=result)


@pytest.fixture
def fake_tenant():
    tenant = Tenant(name="Test Tenant", status="active", settings={})
    tenant.id = uuid.uuid4()
    return tenant


@pytest.fixture
def fake_company(fake_tenant):
    company = Company(
        tenant_id=fake_tenant.id,
        legal_name="Test Company",
        rut="12345678-9",
        fiscal_address="Test Address",
        phone="+59812345678",
        email="test@example.com",
        website="https://example.com",
    )
    company.id = uuid.uuid4()
    return company


@pytest.fixture
def fake_user(fake_tenant, fake_company):
    user = User(
        email="existing@example.com",
        username="existing_user",
        full_name="Existing User",
        password_hash=get_password_hash("secret123"),
        is_active=True,
        tenant_id=fake_tenant.id,
        company_id=fake_company.id,
    )
    user.id = uuid.uuid4()
    user.roles = []
    user.permission_codes = ["*"]
    return user


@pytest.fixture
def fake_db(fake_user, fake_tenant, fake_company):
    return FakeSession(users=[fake_user], tenants=[fake_tenant], companies=[fake_company])
