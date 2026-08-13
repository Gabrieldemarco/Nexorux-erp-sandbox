"""add password recovery fields to user

Revision ID: d7a1c2b3f4e5
Revises: 0a8c3bfeb191
Create Date: 2026-08-12 10:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "d7a1c2b3f4e5"
down_revision: Union[str, None] = "0a8c3bfeb191"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "user",
        sa.Column("password_reset_token_hash", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "user",
        sa.Column("password_reset_token_expires_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        op.f("ix_user_password_reset_token_hash"),
        "user",
        ["password_reset_token_hash"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_user_password_reset_token_hash"), table_name="user")
    op.drop_column("user", "password_reset_token_expires_at")
    op.drop_column("user", "password_reset_token_hash")
