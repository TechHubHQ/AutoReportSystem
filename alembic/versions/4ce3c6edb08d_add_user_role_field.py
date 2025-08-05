"""add user role field

Revision ID: 4ce3c6edb08d
Revises: add_user_role_field
Create Date: 2025-08-05 21:49:07.979509

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4ce3c6edb08d'
down_revision: Union[str, Sequence[str], None] = 'add_user_sessions'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add userrole column to users table
    op.add_column('users', sa.Column('userrole', sa.String(), nullable=False, server_default='Software Engineer'))


def downgrade() -> None:
    """Downgrade schema."""
    # Remove userrole column from users table
    op.drop_column('users', 'userrole')
