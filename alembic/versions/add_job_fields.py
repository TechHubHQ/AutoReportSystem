"""Add job fields for code and custom jobs

Revision ID: add_job_fields
Revises: add_job_model
Create Date: 2024-01-01 00:00:01.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = 'add_job_fields'
down_revision = 'add_job_model'
branch_labels = None
depends_on = None


def upgrade():
    # Add new columns to jobs table
    op.add_column('jobs', sa.Column('code', sa.Text(), nullable=True))
    op.add_column('jobs', sa.Column('schedule_config', sa.Text(), nullable=True))
    op.add_column('jobs', sa.Column('is_custom', sa.Boolean(), nullable=False, server_default='0'))


def downgrade():
    op.drop_column('jobs', 'is_custom')
    op.drop_column('jobs', 'schedule_config')
    op.drop_column('jobs', 'code')