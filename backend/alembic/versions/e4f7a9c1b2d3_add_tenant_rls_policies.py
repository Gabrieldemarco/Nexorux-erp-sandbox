"""add tenant rls policies

Revision ID: e4f7a9c1b2d3
Revises: d7a1c2b3f4e5
Create Date: 2026-08-12 11:10:00.000000
"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "e4f7a9c1b2d3"
down_revision: Union[str, None] = "d7a1c2b3f4e5"
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
]


def upgrade() -> None:
    for table in TABLES:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY;")
        op.execute(
            f"""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1
                    FROM pg_policies
                    WHERE schemaname = 'public'
                      AND tablename = '{table}'
                      AND policyname = '{table}_tenant_isolation'
                ) THEN
                    CREATE POLICY {table}_tenant_isolation
                    ON {table}
                    USING (
                        tenant_id = current_setting('app.current_tenant_id', true)::uuid
                    )
                    WITH CHECK (
                        tenant_id = current_setting('app.current_tenant_id', true)::uuid
                    );
                END IF;
            END$$;
            """
        )


def downgrade() -> None:
    for table in TABLES:
        op.execute(f"DROP POLICY IF EXISTS {table}_tenant_isolation ON {table};")
        op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY;")
