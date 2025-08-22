"""Add timeline_content field to task_notes table

Revision ID: add_timeline_content
Revises: 20250103_add_task_archive
Create Date: 2025-01-15 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_timeline_content'
down_revision = '20250103_add_task_archive_fields'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add timeline_content column to task_notes table
    op.add_column('task_notes', sa.Column(
        'timeline_content', sa.Text(), nullable=True))

    # Migrate existing data: copy analysis_content to timeline_content for existing records
    # This ensures backward compatibility
    op.execute("""
        UPDATE task_notes 
        SET timeline_content = analysis_content 
        WHERE timeline_content IS NULL
    """)


def downgrade() -> None:
    # Remove the timeline_content column
    op.drop_column('task_notes', 'timeline_content')
