"""add_verification_reviews_table

Revision ID: f73d91b8a2e4
Revises: e4a19c52f8b1
Create Date: 2026-09-29 01:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f73d91b8a2e4'
down_revision: Union[str, None] = 'e4a19c52f8b1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'verification_reviews',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('verification_record_id', sa.String(length=36), nullable=False),
        sa.Column('reviewer_id', sa.String(length=36), nullable=False),
        sa.Column('decision', sa.String(length=50), nullable=False),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['reviewer_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['verification_record_id'], ['verification_records.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_verification_reviews_verification_record_id'), 'verification_reviews', ['verification_record_id'], unique=False)
    op.create_index(op.f('ix_verification_reviews_reviewer_id'), 'verification_reviews', ['reviewer_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_verification_reviews_reviewer_id'), table_name='verification_reviews')
    op.drop_index(op.f('ix_verification_reviews_verification_record_id'), table_name='verification_reviews')
    op.drop_table('verification_reviews')
