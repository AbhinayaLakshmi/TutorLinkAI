"""add_reviews_model

Revision ID: e2f3a4b5c6d7
Revises: a1d2e3f4b5c6
Create Date: 2026-10-01 09:40:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e2f3a4b5c6d7'
down_revision: Union[str, None] = 'a1d2e3f4b5c6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'reviews',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('session_id', sa.String(length=36), nullable=False),
        sa.Column('student_id', sa.String(length=36), nullable=False),
        sa.Column('tutor_id', sa.String(length=36), nullable=False),
        sa.Column('rating', sa.Integer(), nullable=False),
        sa.Column('review_text', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.CheckConstraint('rating >= 1 AND rating <= 5', name='check_rating_range'),
        sa.ForeignKeyConstraint(['session_id'], ['sessions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['student_id'], ['student_profiles.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['tutor_id'], ['tutor_profiles.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('session_id')
    )
    op.create_index(op.f('ix_reviews_session_id'), 'reviews', ['session_id'], unique=True)
    op.create_index(op.f('ix_reviews_student_id'), 'reviews', ['student_id'], unique=False)
    op.create_index(op.f('ix_reviews_tutor_id'), 'reviews', ['tutor_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_reviews_tutor_id'), table_name='reviews')
    op.drop_index(op.f('ix_reviews_student_id'), table_name='reviews')
    op.drop_index(op.f('ix_reviews_session_id'), table_name='reviews')
    op.drop_table('reviews')
