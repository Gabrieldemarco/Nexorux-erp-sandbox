"""fix rls empty tenant guc cast

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-08-13 01:05:00.000000

When app.current_tenant_id is unset, current_setting(..., true) returns ''
and ''::uuid raises, surfacing as HTTP 500 on inserts/selects.
Use NULLIF so missing GUC denies access instead of erroring.
"""

from typing import Sequence, Union

from alembic import op

revision: str = "b2c3d4e5f6a7"
down_revision: Union[str, None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TABLES = [
    "product",
    "customer",
    "supplier",
    "branch",
    "warehouse",
    "invoice",
    "invoice_item",
    "payment",
    "stock_movement",
    "fiscal_document",
    "fiscal_response",
    "certificate",
    "tax_configuration",
    "price_list",
    "audit_log",
    "purchase_receipt",
    "purchase_receipt_item",
]

TENANT_PRED = (
    "NULLIF(current_setting('app.current_tenant_id', true), '') IS NOT NULL "
    "AND tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid"
)


def upgrade() -> None:
    for table in TABLES:
        op.execute(f"DROP POLICY IF EXISTS {table}_tenant_isolation ON {table};")
        op.execute(
            f"""
            CREATE POLICY {table}_tenant_isolation
            ON {table}
            USING ({TENANT_PRED})
            WITH CHECK ({TENANT_PRED});
            """
        )


def downgrade() -> None:
    old = "tenant_id = current_setting('app.current_tenant_id', true)::uuid"
    for table in TABLES:
        op.execute(f"DROP POLICY IF EXISTS {table}_tenant_isolation ON {table};")
        op.execute(
            f"""
            CREATE POLICY {table}_tenant_isolation
            ON {table}
            USING ({old})
            WITH CHECK ({old});
            """
        )
