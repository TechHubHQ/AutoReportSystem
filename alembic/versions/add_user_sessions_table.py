"""Add user_sessions table for persistent session management

Revision ID: add_user_sessions
Revises: add_template_fields
Create Date: 2024-01-01 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = 'add_user_sessions'
down_revision = 'add_job_fields'
branch_labels = None
depends_on = None


def upgrade():
    """Add user_sessions table"""
    # Create user_sessions table
    op.execute(text("""
        CREATE TABLE IF NOT EXISTS user_sessions (
            session_token TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL,
            user_data TEXT NOT NULL,
            expires_at TIMESTAMP NOT NULL,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            last_accessed TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        )
    """))
    
    # Create index for faster lookups
    op.execute(text("""
        CREATE INDEX IF NOT EXISTS idx_sessions_expires 
        ON user_sessions(expires_at)
    """))
    
    op.execute(text("""
        CREATE INDEX IF NOT EXISTS idx_sessions_user_id 
        ON user_sessions(user_id)
    """))


def downgrade():
    """Remove user_sessions table"""
    op.execute(text("DROP INDEX IF EXISTS idx_sessions_expires"))
    op.execute(text("DROP INDEX IF EXISTS idx_sessions_user_id"))
    op.execute(text("DROP TABLE IF EXISTS user_sessions"))