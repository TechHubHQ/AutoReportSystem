from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func
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

    # One-to-many: User → Tasks
    tasks = relationship("Task", back_populates="creator",
                         cascade="all, delete-orphan")


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True, nullable=False)
    description = Column(String, nullable=True)
    status = Column(String, default="todo", nullable=False)  # todo, inprogress, completed, pending
    priority = Column(String, default="medium", nullable=False)  # low, medium, high, urgent
    category = Column(String, default="in progress", nullable=False)  # accomplishments, in progress
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
