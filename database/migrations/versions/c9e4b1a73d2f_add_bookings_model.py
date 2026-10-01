"""add_bookings_model

Revision ID: c9e4b1a73d2f
Revises: f73d91b8a2e4
Create Date: 2026-09-29 05:50:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd8a3f2b1c4e5'
down_revision: Union[str, None] = 'f73d91b8a2e4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'bookings',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('student_id', sa.String(length=36), nullable=False),
        sa.Column('tutor_id', sa.String(length=36), nullable=False),
        sa.Column('learning_need_id', sa.String(length=36), nullable=False),
        sa.Column('scheduled_date', sa.String(length=50), nullable=False),
        sa.Column('start_time', sa.String(length=50), nullable=False),
        sa.Column('duration_minutes', sa.Integer(), nullable=False, server_default='60'),
        sa.Column('hourly_rate', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('total_amount', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('student_message', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='PENDING'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['learning_need_id'], ['learning_needs.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['student_id'], ['student_profiles.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['tutor_id'], ['tutor_profiles.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_bookings_student_id'), 'bookings', ['student_id'], unique=False)
    op.create_index(op.f('ix_bookings_tutor_id'), 'bookings', ['tutor_id'], unique=False)
    op.create_index(op.f('ix_bookings_learning_need_id'), 'bookings', ['learning_need_id'], unique=False)
    op.create_index(op.f('ix_bookings_status'), 'bookings', ['status'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_bookings_status'), table_name='bookings')
    op.drop_index(op.f('ix_bookings_learning_need_id'), table_name='bookings')
    op.drop_index(op.f('ix_bookings_tutor_id'), table_name='bookings')
    op.drop_index(op.f('ix_bookings_student_id'), table_name='bookings')
    op.drop_table('bookings')
