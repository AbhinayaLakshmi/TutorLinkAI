"""add_learning_needs_model

Revision ID: b7123ef69a10
Revises: 5c2468228789
Create Date: 2026-09-08 09:10:00.000000

"""
import uuid
from datetime import datetime
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b7123ef69a10'
down_revision: Union[str, None] = '5c2468228789'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create learning_needs table
    op.create_table(
        'learning_needs',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('student_profile_id', sa.String(length=36), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('subjects', sa.JSON(), nullable=False),
        sa.Column('topics', sa.JSON(), nullable=True),
        sa.Column('learning_goals', sa.Text(), nullable=True),
        sa.Column('preferred_tutor_characteristics', sa.Text(), nullable=True),
        sa.Column('preferred_availability', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=True, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['student_profile_id'], ['student_profiles.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_learning_needs_student_profile_id'), 'learning_needs', ['student_profile_id'], unique=False)
    op.create_index('ix_learning_needs_student_profile_id_is_active', 'learning_needs', ['student_profile_id', 'is_active'], unique=False)

    # 2. Non-destructive data migration from student_requirements to learning_needs
    bind = op.get_bind()
    student_reqs_table = sa.table(
        'student_requirements',
        sa.column('id', sa.String),
        sa.column('student_profile_id', sa.String),
        sa.column('subjects', sa.JSON),
        sa.column('topics', sa.JSON),
        sa.column('learning_goals', sa.Text),
        sa.column('preferred_tutor_characteristics', sa.Text),
        sa.column('preferred_availability', sa.Text),
    )

    learning_needs_table = sa.table(
        'learning_needs',
        sa.column('id', sa.String),
        sa.column('student_profile_id', sa.String),
        sa.column('title', sa.String),
        sa.column('subjects', sa.JSON),
        sa.column('topics', sa.JSON),
        sa.column('learning_goals', sa.Text),
        sa.column('preferred_tutor_characteristics', sa.Text),
        sa.column('preferred_availability', sa.Text),
        sa.column('is_active', sa.Boolean),
        sa.column('created_at', sa.DateTime),
        sa.column('updated_at', sa.DateTime),
    )

    rows = bind.execute(sa.select(
        student_reqs_table.c.student_profile_id,
        student_reqs_table.c.subjects,
        student_reqs_table.c.topics,
        student_reqs_table.c.learning_goals,
        student_reqs_table.c.preferred_tutor_characteristics,
        student_reqs_table.c.preferred_availability,
    )).fetchall()

    now = datetime.utcnow()
    records_to_insert = []
    for row in rows:
        subjects_val = row.subjects
        subjects_list = []
        if isinstance(subjects_val, list):
            subjects_list = subjects_val
        elif isinstance(subjects_val, str):
            try:
                import json
                parsed = json.loads(subjects_val)
                if isinstance(parsed, list):
                    subjects_list = parsed
                elif parsed:
                    subjects_list = [str(parsed)]
            except Exception:
                subjects_list = [subjects_val] if subjects_val else []
        elif subjects_val:
            subjects_list = list(subjects_val)

        first_subject = None
        if subjects_list and len(subjects_list) > 0 and subjects_list[0]:
            first_subject = str(subjects_list[0]).strip()

        title = f"{first_subject} Preparation" if first_subject else "Primary Learning Need"
        final_subjects = subjects_list if subjects_list else ["General"]

        records_to_insert.append({
            'id': str(uuid.uuid4()),
            'student_profile_id': row.student_profile_id,
            'title': title,
            'subjects': final_subjects,
            'topics': row.topics if row.topics is not None else [],
            'learning_goals': row.learning_goals,
            'preferred_tutor_characteristics': row.preferred_tutor_characteristics,
            'preferred_availability': row.preferred_availability,
            'is_active': True,
            'created_at': now,
            'updated_at': now,
        })

    if records_to_insert:
        bind.execute(learning_needs_table.insert(), records_to_insert)


def downgrade() -> None:
    op.drop_index('ix_learning_needs_student_profile_id_is_active', table_name='learning_needs')
    op.drop_index(op.f('ix_learning_needs_student_profile_id'), table_name='learning_needs')
    op.drop_table('learning_needs')
