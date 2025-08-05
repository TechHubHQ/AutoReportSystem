"""add user role field

Revision ID: add_user_role_field
Revises: add_user_sessions_table
Create Date: 2024-01-01 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_user_role_field'
down_revision = 'add_user_sessions'
branch_labels = None
depends_on = None


def upgrade():
    # Add userrole column to users table
    op.add_column('users', sa.Column('userrole', sa.String(), nullable=False, server_default='Software Engineer'))


def downgrade():
    # Remove userrole column from users table
    op.drop_column('users', 'userrole')