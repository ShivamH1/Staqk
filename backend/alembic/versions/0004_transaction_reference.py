"""add reference column to transactions for webhook idempotency

Revision ID: 0004
Revises: 0003
Create Date: 2026-06-28

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("transactions", sa.Column("reference", sa.String(), nullable=True))
    op.create_unique_constraint("uq_transactions_reference", "transactions", ["reference"])


def downgrade() -> None:
    op.drop_constraint("uq_transactions_reference", "transactions", type_="unique")
    op.drop_column("transactions", "reference")
