"""force row level security on tenant tables

Revision ID: f8a2b4c6d0e1
Revises: e4f7a9c1b2d3
Create Date: 2026-08-12 20:40:00.000000
"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "f8a2b4c6d0e1"
down_revision: Union[str, None] = "e4f7a9c1b2d3"
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
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY;")


def downgrade() -> None:
    for table in TABLES:
        op.execute(f"ALTER TABLE {table} NO FORCE ROW LEVEL SECURITY;")
