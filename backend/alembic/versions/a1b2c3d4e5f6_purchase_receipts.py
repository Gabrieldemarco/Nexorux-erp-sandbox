"""purchase receipts + RLS

Revision ID: a1b2c3d4e5f6
Revises: f8a2b4c6d0e1
Create Date: 2026-08-12 21:20:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "f8a2b4c6d0e1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

RLS_TABLES = ("purchase_receipt", "purchase_receipt_item")


def upgrade() -> None:
    op.create_table(
        "purchase_receipt",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenant.id", ondelete="CASCADE"), nullable=False),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("company.id", ondelete="CASCADE"), nullable=False),
        sa.Column("supplier_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("supplier.id", ondelete="SET NULL"), nullable=True),
        sa.Column("warehouse_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("warehouse.id", ondelete="SET NULL"), nullable=True),
        sa.Column("number", sa.String(length=50), nullable=False),
        sa.Column("receipt_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="received"),
    )
    op.create_index("ix_purchase_receipt_tenant_id", "purchase_receipt", ["tenant_id"])
    op.create_index("ix_purchase_receipt_company_id", "purchase_receipt", ["company_id"])
    op.create_index("ix_purchase_receipt_supplier_id", "purchase_receipt", ["supplier_id"])
    op.create_index("ix_purchase_receipt_warehouse_id", "purchase_receipt", ["warehouse_id"])

    op.create_table(
        "purchase_receipt_item",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenant.id", ondelete="CASCADE"), nullable=False),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("company.id", ondelete="CASCADE"), nullable=False),
        sa.Column(
            "receipt_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("purchase_receipt.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("product.id", ondelete="SET NULL"), nullable=True),
        sa.Column("quantity", sa.Numeric(18, 6), nullable=False, server_default="0"),
        sa.Column("unit_cost", sa.Numeric(18, 6), nullable=False, server_default="0"),
        sa.Column("description", sa.String(length=500), nullable=True),
    )
    op.create_index("ix_purchase_receipt_item_tenant_id", "purchase_receipt_item", ["tenant_id"])
    op.create_index("ix_purchase_receipt_item_company_id", "purchase_receipt_item", ["company_id"])
    op.create_index("ix_purchase_receipt_item_receipt_id", "purchase_receipt_item", ["receipt_id"])
    op.create_index("ix_purchase_receipt_item_product_id", "purchase_receipt_item", ["product_id"])

    for table in RLS_TABLES:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY;")
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY;")
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
    for table in RLS_TABLES:
        op.execute(f"DROP POLICY IF EXISTS {table}_tenant_isolation ON {table};")
        op.execute(f"ALTER TABLE {table} NO FORCE ROW LEVEL SECURITY;")
        op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY;")

    op.drop_table("purchase_receipt_item")
    op.drop_table("purchase_receipt")
