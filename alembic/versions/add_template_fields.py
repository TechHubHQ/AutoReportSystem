"""Add description, category, and file_path to email_templates

Revision ID: add_template_fields
Revises: 8c8b218a72b0
Create Date: 2024-01-15 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_template_fields'
down_revision = '8c8b218a72b0'
branch_labels = None
depends_on = None

def upgrade():
    # Add new columns to email_templates table
    op.add_column('email_templates', sa.Column('description', sa.Text(), nullable=True))
    op.add_column('email_templates', sa.Column('category', sa.String(), nullable=False, server_default='General'))
    op.add_column('email_templates', sa.Column('file_path', sa.String(), nullable=True))

def downgrade():
    # Remove the added columns
    op.drop_column('email_templates', 'file_path')
    op.drop_column('email_templates', 'category')
    op.drop_column('email_templates', 'description')