from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func, Text, Boolean
from app.config.config import settings


DATABASEURL = settings.db_url
engine = create_async_engine(DATABASEURL)
Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)
    userrole = Column(String, default="Software Engineer", nullable=False)

    # One-to-many: User → Tasks
    tasks = relationship("Task", back_populates="creator",
                         cascade="all, delete-orphan")

    # One-to-many: User → EmailTemplates
    templates = relationship(
        "EmailTemplate", back_populates="creator", cascade="all, delete-orphan")

    # One-to-many: User → UserSessions
    sessions = relationship(
        "UserSession", back_populates="user", cascade="all, delete-orphan")


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
    created_at = Column(DateTime(timezone=True),
                        server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True),
                        server_default=func.now(), onupdate=func.now(), nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Many-to-one: Task → User
    creator = relationship("User", back_populates="tasks")


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
    created_at = Column(DateTime(timezone=True),
                        server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(
    ), onupdate=func.now(), nullable=False)


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
