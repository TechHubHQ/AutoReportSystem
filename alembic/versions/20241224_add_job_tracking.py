"""Add job tracking tables (fixed)

Revision ID: 20241224_add_job_tracking_fixed
Revises: add_task_notes
Create Date: 2024-12-24 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20241224_add_job_tracking_fixed'
down_revision = 'add_task_notes'
branch_labels = None
depends_on = None


def upgrade():
    # Enhance existing jobs table with tracking columns
    op.add_column('jobs', sa.Column('total_runs', sa.Integer(),
                  nullable=False, server_default=sa.text('0')))
    op.add_column('jobs', sa.Column('successful_runs', sa.Integer(),
                  nullable=False, server_default=sa.text('0')))
    op.add_column('jobs', sa.Column('failed_runs', sa.Integer(),
                  nullable=False, server_default=sa.text('0')))
    op.add_column('jobs', sa.Column(
        'average_duration', sa.Integer(), nullable=True))
    op.add_column('jobs', sa.Column('last_success',
                  sa.DateTime(timezone=True), nullable=True))
    op.add_column('jobs', sa.Column('last_failure',
                  sa.DateTime(timezone=True), nullable=True))
    op.add_column('jobs', sa.Column(
        'last_error_message', sa.Text(), nullable=True))
    op.add_column('jobs', sa.Column('status', sa.String(),
                  nullable=False, server_default=sa.text("'active'")))

    # Create job_executions table
    op.create_table('job_executions',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('job_id', sa.Integer(), nullable=False),
                    sa.Column('execution_id', sa.String(), nullable=False),
                    sa.Column('scheduled_time', sa.DateTime(
                        timezone=True), nullable=False),
                    sa.Column('started_at', sa.DateTime(
                        timezone=True), nullable=False),
                    sa.Column('completed_at', sa.DateTime(
                        timezone=True), nullable=True),
                    sa.Column('duration', sa.Integer(), nullable=True),
                    sa.Column('status', sa.String(), nullable=False),
                    sa.Column('result_data', sa.Text(), nullable=True),
                    sa.Column('error_message', sa.Text(), nullable=True),
                    sa.Column('error_traceback', sa.Text(), nullable=True),
                    sa.Column('trigger_type', sa.String(), nullable=True),
                    sa.Column('triggered_by', sa.Integer(), nullable=True),
                    sa.Column('retry_count', sa.Integer(), nullable=False,
                              server_default=sa.text('0')),
                    sa.Column('parent_execution_id',
                              sa.String(), nullable=True),
                    sa.Column('cpu_usage_start', sa.Integer(), nullable=True),
                    sa.Column('cpu_usage_end', sa.Integer(), nullable=True),
                    sa.Column('memory_usage_start',
                              sa.Integer(), nullable=True),
                    sa.Column('memory_usage_end', sa.Integer(), nullable=True),
                    sa.Column('created_at', sa.DateTime(timezone=True),
                              server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
                    sa.ForeignKeyConstraint(['job_id'], ['jobs.id'], ),
                    sa.ForeignKeyConstraint(['triggered_by'], ['users.id'], ),
                    sa.PrimaryKeyConstraint('id'),
                    sa.UniqueConstraint(
                        'execution_id', name='uq_job_executions_execution_id')
                    )
    op.create_index(op.f('ix_job_executions_id'),
                    'job_executions', ['id'], unique=False)
    op.create_index(op.f('ix_job_executions_execution_id'),
                    'job_executions', ['execution_id'], unique=False)

    # Create job_execution_logs table
    op.create_table('job_execution_logs',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('execution_id', sa.String(), nullable=False),
                    sa.Column('log_level', sa.String(), nullable=False),
                    sa.Column('message', sa.Text(), nullable=False),
                    sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.text(
                        '(CURRENT_TIMESTAMP)'), nullable=False),
                    sa.Column('source', sa.String(), nullable=True),
                    sa.ForeignKeyConstraint(
                        ['execution_id'], ['job_executions.execution_id'], ),
                    sa.PrimaryKeyConstraint('id')
                    )
    op.create_index(op.f('ix_job_execution_logs_id'),
                    'job_execution_logs', ['id'], unique=False)


def downgrade():
    # Drop new tables
    op.drop_index(op.f('ix_job_execution_logs_id'),
                  table_name='job_execution_logs')
    op.drop_table('job_execution_logs')
    op.drop_index(op.f('ix_job_executions_execution_id'),
                  table_name='job_executions')
    op.drop_index(op.f('ix_job_executions_id'), table_name='job_executions')
    op.drop_table('job_executions')

    # Remove columns from jobs table
    op.drop_column('jobs', 'status')
    op.drop_column('jobs', 'last_error_message')
    op.drop_column('jobs', 'last_failure')
    op.drop_column('jobs', 'last_success')
    op.drop_column('jobs', 'average_duration')
    op.drop_column('jobs', 'failed_runs')
    op.drop_column('jobs', 'successful_runs')
    op.drop_column('jobs', 'total_runs')
