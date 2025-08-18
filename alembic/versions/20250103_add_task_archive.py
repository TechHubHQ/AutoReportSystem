"""Add task archive fields

Revision ID: 20250103_add_task_archive_fields
Revises: 20241224_add_job_tracking
Create Date: 2025-01-03 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20250103_add_task_archive_fields'
down_revision: Union[str, None] = '20241224_add_job_tracking'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add archive functionality fields to tasks table"""
    # Add archive fields to tasks table
    op.add_column('tasks', sa.Column('is_archived', sa.Boolean(),
                  nullable=False, server_default='false'))
    op.add_column('tasks', sa.Column(
        'archived_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('tasks', sa.Column(
        'archived_by', sa.Integer(), nullable=True))

    # Add foreign key constraint for archived_by
    op.create_foreign_key(
        'fk_tasks_archived_by_users',
        'tasks', 'users',
        ['archived_by'], ['id']
    )

    # Create index for better performance on archive queries
    op.create_index('idx_tasks_is_archived', 'tasks', ['is_archived'])


def downgrade() -> None:
    """Remove archive functionality fields from tasks table"""
    # Drop index
    op.drop_index('idx_tasks_is_archived', table_name='tasks')

    # Drop foreign key constraint
    op.drop_constraint('fk_tasks_archived_by_users',
                       'tasks', type_='foreignkey')

    # Drop columns
    op.drop_column('tasks', 'archived_by')
    op.drop_column('tasks', 'archived_at')
    op.drop_column('tasks', 'is_archived')
