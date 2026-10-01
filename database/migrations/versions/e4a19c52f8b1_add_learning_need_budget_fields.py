"""add_learning_need_budget_fields

Revision ID: e4a19c52f8b1
Revises: b7123ef69a10
Create Date: 2026-09-29 01:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e4a19c52f8b1'
down_revision: Union[str, None] = 'b7123ef69a10'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('learning_needs', sa.Column('budget_min', sa.Numeric(precision=10, scale=2), nullable=True))
    op.add_column('learning_needs', sa.Column('budget_max', sa.Numeric(precision=10, scale=2), nullable=True))


def downgrade() -> None:
    op.drop_column('learning_needs', 'budget_max')
    op.drop_column('learning_needs', 'budget_min')
