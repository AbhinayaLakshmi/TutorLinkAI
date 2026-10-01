"""add_sessions_model

Revision ID: a1d2e3f4b5c6
Revises: c9e4b1a73d2f
Create Date: 2026-10-01 09:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1d2e3f4b5c6'
down_revision: Union[str, None] = 'd8a3f2b1c4e5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'sessions',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('booking_id', sa.String(length=36), nullable=False),
        sa.Column('student_id', sa.String(length=36), nullable=False),
        sa.Column('tutor_id', sa.String(length=36), nullable=False),
        sa.Column('learning_need_id', sa.String(length=36), nullable=False),
        sa.Column('scheduled_date', sa.String(length=50), nullable=False),
        sa.Column('start_time', sa.String(length=50), nullable=False),
        sa.Column('duration_minutes', sa.Integer(), nullable=False, server_default='60'),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='SCHEDULED'),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('ended_at', sa.DateTime(), nullable=True),
        sa.Column('actual_duration_minutes', sa.Integer(), nullable=True),
        sa.Column('completion_note', sa.Text(), nullable=True),
        sa.Column('cancellation_reason', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['booking_id'], ['bookings.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['learning_need_id'], ['learning_needs.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['student_id'], ['student_profiles.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['tutor_id'], ['tutor_profiles.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('booking_id')
    )
    op.create_index(op.f('ix_sessions_booking_id'), 'sessions', ['booking_id'], unique=True)
    op.create_index(op.f('ix_sessions_student_id'), 'sessions', ['student_id'], unique=False)
    op.create_index(op.f('ix_sessions_tutor_id'), 'sessions', ['tutor_id'], unique=False)
    op.create_index(op.f('ix_sessions_learning_need_id'), 'sessions', ['learning_need_id'], unique=False)
    op.create_index(op.f('ix_sessions_status'), 'sessions', ['status'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_sessions_status'), table_name='sessions')
    op.drop_index(op.f('ix_sessions_learning_need_id'), table_name='sessions')
    op.drop_index(op.f('ix_sessions_tutor_id'), table_name='sessions')
    op.drop_index(op.f('ix_sessions_student_id'), table_name='sessions')
    op.drop_index(op.f('ix_sessions_booking_id'), table_name='sessions')
    op.drop_table('sessions')
