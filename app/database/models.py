from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func, Text, Boolean, Date, UniqueConstraint
from sqlalchemy.pool import NullPool
from app.config.config import settings


DATABASEURL = settings.db_url
# Use NullPool to avoid sharing async connections across multiple event loops/threads.
# This prevents "another operation is in progress" errors when the app uses asyncio in
# different contexts (e.g., Streamlit UI and background scheduler thread).
engine = create_async_engine(DATABASEURL, poolclass=NullPool)
Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)
    userrole = Column(String, default="Software Engineer", nullable=False)

    # One-to-many: User → Tasks
    tasks = relationship("Task", foreign_keys="Task.created_by", back_populates="creator",
                         cascade="all, delete-orphan")

    # One-to-many: User → EmailTemplates
    templates = relationship(
        "EmailTemplate", back_populates="creator", cascade="all, delete-orphan")

    # One-to-many: User → UserSessions
    sessions = relationship(
        lambda: UserSession, back_populates="user", cascade="all, delete-orphan")


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True, nullable=False)
    description = Column(String, nullable=True)
    # todo, inprogress, completed, pending
    status = Column(String, default="todo", nullable=False)
    # low, medium, high, urgent
    priority = Column(String, default="medium", nullable=False)
    # accomplishments, in progress
    category = Column(String, default="in progress", nullable=False)
    due_date = Column(DateTime(timezone=True), nullable=True)
    # Archive functionality
    is_archived = Column(Boolean, default=False, nullable=False)
    archived_at = Column(DateTime(timezone=True), nullable=True)
    archived_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True),
                        server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True),
                        server_default=func.now(), onupdate=func.now(), nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Many-to-one: Task → User
    creator = relationship("User", foreign_keys=[created_by], back_populates="tasks")
    
    # Many-to-one: Task → User (who archived it)
    archiver = relationship("User", foreign_keys=[archived_by], backref="archived_tasks")

    # One-to-many: Task → TaskStatusHistory
    status_history = relationship("TaskStatusHistory", back_populates="task",
                                  cascade="all, delete-orphan")

    # One-to-many: Task → TaskNotes
    notes = relationship("TaskNote", back_populates="task",
                         cascade="all, delete-orphan")


class TaskStatusHistory(Base):
    __tablename__ = "task_status_history"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    # Previous status (null for initial creation)
    old_status = Column(String, nullable=True)
    new_status = Column(String, nullable=False)  # New status
    old_category = Column(String, nullable=True)  # Previous category
    new_category = Column(String, nullable=False)  # New category
    changed_at = Column(DateTime(timezone=True),
                        server_default=func.now(), nullable=False)
    changed_by = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Many-to-one: TaskStatusHistory → Task
    task = relationship("Task", back_populates="status_history")

    # Many-to-one: TaskStatusHistory → User
    user = relationship("User", backref="task_status_changes")


class TaskNote(Base):
    __tablename__ = "task_notes"
    __table_args__ = (UniqueConstraint(
        'task_id', 'note_date', name='unique_task_note_per_date'),)

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    # Date for this specific note entry
    note_date = Column(Date, nullable=False)
    # Clear explanation of the issue
    issue_description = Column(Text, nullable=False)
    # Detailed progress analysis
    analysis_content = Column(Text, nullable=False)
    # Resolution information (can be null until resolved)
    resolution_notes = Column(Text, nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True),
                        server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True),
                        server_default=func.now(), onupdate=func.now(), nullable=False)

    # Many-to-one: TaskNote → Task
    task = relationship("Task", back_populates="notes")

    # Many-to-one: TaskNote → User
    creator = relationship("User", backref="task_notes")


class SMTPConf(Base):
    __tablename__ = "smtp_conf"

    id = Column(Integer, primary_key=True, index=True)
    smtp_host = Column(String, nullable=False, default="smtp.gmail.com")
    smtp_port = Column(Integer, nullable=False, default=587)
    smtp_username = Column(String, nullable=False)
    smtp_password = Column(String, nullable=False)
    sender_email = Column(String, ForeignKey("users.email"), nullable=False)
    is_active = Column(String, default="True", nullable=False)

    # Many-to-one: SMTPConf → User
    user = relationship("User", backref="smtp_confs",
                        primaryjoin="SMTPConf.sender_email==User.email")


class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)
    function_name = Column(String, nullable=False)
    module_path = Column(String, nullable=False)
    # weekly, monthly, daily, custom
    schedule_type = Column(String, nullable=False)
    code = Column(Text, nullable=True)  # Python code for the job
    schedule_config = Column(Text, nullable=True)  # JSON config for scheduling
    is_active = Column(Boolean, default=True, nullable=False)
    # User-created vs auto-discovered
    is_custom = Column(Boolean, default=False, nullable=False)
    last_run = Column(DateTime(timezone=True), nullable=True)
    next_run = Column(DateTime(timezone=True), nullable=True)
    # Execution statistics
    total_runs = Column(Integer, default=0, nullable=False)
    successful_runs = Column(Integer, default=0, nullable=False)
    failed_runs = Column(Integer, default=0, nullable=False)
    # Average duration in seconds
    average_duration = Column(Integer, nullable=True)
    last_success = Column(DateTime(timezone=True), nullable=True)
    last_failure = Column(DateTime(timezone=True), nullable=True)
    last_error_message = Column(Text, nullable=True)
    # Job status: active, paused, disabled, error
    status = Column(String, default="active", nullable=False)
    created_at = Column(DateTime(timezone=True),
                        server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(
    ), onupdate=func.now(), nullable=False)

    # One-to-many: Job → JobExecutions
    executions = relationship("JobExecution", back_populates="job",
                              cascade="all, delete-orphan", order_by="JobExecution.started_at.desc()")


class EmailTemplate(Base):
    __tablename__ = "email_templates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    subject = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String, default="General", nullable=False)
    html_content = Column(Text, nullable=False)
    file_path = Column(String, nullable=True)  # Path to template file
    is_active = Column(Boolean, default=True, nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True),
                        server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(
    ), onupdate=func.now(), nullable=False)

    # Many-to-one: EmailTemplate → User
    creator = relationship("User", back_populates="templates")


class JobExecution(Base):
    __tablename__ = "job_executions"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False)
    # Unique execution identifier
    execution_id = Column(String, nullable=False, index=True)
    scheduled_time = Column(DateTime(timezone=True), nullable=False)
    started_at = Column(DateTime(timezone=True), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    duration = Column(Integer, nullable=True)  # Duration in seconds
    # success, failure, timeout, cancelled
    status = Column(String, nullable=False)
    result_data = Column(Text, nullable=True)  # JSON result data
    error_message = Column(Text, nullable=True)
    error_traceback = Column(Text, nullable=True)
    # Execution context information
    trigger_type = Column(String, nullable=True)  # manual, scheduled, retry
    triggered_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    retry_count = Column(Integer, default=0, nullable=False)
    parent_execution_id = Column(String, nullable=True)  # For retry tracking
    # System information during execution
    cpu_usage_start = Column(Integer, nullable=True)
    cpu_usage_end = Column(Integer, nullable=True)
    memory_usage_start = Column(Integer, nullable=True)
    memory_usage_end = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True),
                        server_default=func.now(), nullable=False)

    # Many-to-one: JobExecution → Job
    job = relationship("Job", back_populates="executions")

    # Many-to-one: JobExecution → User (who triggered it)
    triggered_by_user = relationship(
        "User", backref="triggered_job_executions")


class JobExecutionLog(Base):
    __tablename__ = "job_execution_logs"

    id = Column(Integer, primary_key=True, index=True)
    execution_id = Column(String, ForeignKey(
        "job_executions.execution_id"), nullable=False)
    log_level = Column(String, nullable=False)  # INFO, WARNING, ERROR, DEBUG
    message = Column(Text, nullable=False)
    timestamp = Column(DateTime(timezone=True),
                       server_default=func.now(), nullable=False)
    source = Column(String, nullable=True)  # Source module/function

    # Many-to-one: JobExecutionLog → JobExecution
    execution = relationship("JobExecution", backref="logs")


class UserSession(Base):
    __tablename__ = "user_sessions"

    session_token = Column(String, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    user_data = Column(Text, nullable=False)  # JSON string of user data
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True),
                        server_default=func.now(), nullable=False)
    last_accessed = Column(DateTime(timezone=True),
                           server_default=func.now(), nullable=False)

    # Many-to-one: UserSession → User
    user = relationship("User", back_populates="sessions")