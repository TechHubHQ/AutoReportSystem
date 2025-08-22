"""Interface for managing job email configurations."""

from app.database.db_connector import get_db
from app.database.models import JobEmailConfig, User
from sqlalchemy import select
from typing import Optional, List, Dict, Any
from app.config.logging_config import get_logger

logger = get_logger(__name__)


async def create_job_email_config(
    job_id: str,
    user_id: int,
    recipient: str,
    subject: str,
    template: Optional[str] = None,
    recipient_name: Optional[str] = None,
    enabled: bool = True,
    send_empty_reports: bool = False,
    html_format: bool = True,
    retry_failed_sends: bool = True,
    max_retries: int = 3
) -> JobEmailConfig:
    """Create a new job email configuration."""
    db = None
    try:
        # Validate inputs
        if not all([job_id, user_id, recipient, subject]):
            raise ValueError("job_id, user_id, recipient, and subject are required")

        db = await get_db()

        # Check if user exists
        user_result = await db.execute(select(User).where(User.id == user_id))
        user = user_result.scalar_one_or_none()
        if not user:
            raise ValueError(f"User with ID {user_id} not found")

        # Check if config already exists for this job and user
        existing_result = await db.execute(
            select(JobEmailConfig).where(
                JobEmailConfig.job_id == job_id,
                JobEmailConfig.user_id == user_id
            )
        )
        existing_config = existing_result.scalar_one_or_none()
        if existing_config:
            raise ValueError(f"Email configuration for job '{job_id}' already exists for this user")

        # Create new configuration
        new_config = JobEmailConfig(
            job_id=job_id,
            user_id=user_id,
            enabled=enabled,
            recipient=recipient,
            subject=subject,
            template=template,
            recipient_name=recipient_name,
            send_empty_reports=send_empty_reports,
            html_format=html_format,
            retry_failed_sends=retry_failed_sends,
            max_retries=max_retries
        )
        
        db.add(new_config)
        await db.commit()
        await db.refresh(new_config)
        return new_config

    except Exception as e:
        logger.error(f"Error creating job email configuration: {e}")
        if db is not None:
            try:
                await db.rollback()
            except Exception:
                pass
        raise e
    finally:
        if db is not None:
            await db.close()


async def get_job_email_config(job_id: str, user_id: int) -> Optional[JobEmailConfig]:
    """Get email configuration for a specific job and user."""
    try:
        db = await get_db()
        
        result = await db.execute(
            select(JobEmailConfig).where(
                JobEmailConfig.job_id == job_id,
                JobEmailConfig.user_id == user_id
            )
        )
        config = result.scalar_one_or_none()
        return config

    except Exception as e:
        logger.error(f"Error getting job email configuration: {e}")
        return None
    finally:
        await db.close()


async def get_all_job_email_configs(user_id: int) -> List[JobEmailConfig]:
    """Get all email configurations for a user."""
    try:
        db = await get_db()
        
        result = await db.execute(
            select(JobEmailConfig).where(JobEmailConfig.user_id == user_id)
        )
        configs = result.scalars().all()
        return list(configs)

    except Exception as e:
        logger.error(f"Error getting all job email configurations: {e}")
        return []
    finally:
        await db.close()


async def update_job_email_config(
    job_id: str,
    user_id: int,
    **kwargs
) -> Optional[JobEmailConfig]:
    """Update an existing job email configuration."""
    db = None
    try:
        db = await get_db()
        
        # Get existing configuration
        result = await db.execute(
            select(JobEmailConfig).where(
                JobEmailConfig.job_id == job_id,
                JobEmailConfig.user_id == user_id
            )
        )
        config = result.scalar_one_or_none()
        if not config:
            raise ValueError(f"Email configuration for job '{job_id}' not found for this user")

        # Update fields
        for field, value in kwargs.items():
            if hasattr(config, field):
                setattr(config, field, value)

        await db.commit()
        await db.refresh(config)
        return config

    except Exception as e:
        logger.error(f"Error updating job email configuration: {e}")
        if db is not None:
            try:
                await db.rollback()
            except Exception:
                pass
        raise e
    finally:
        if db is not None:
            await db.close()


async def delete_job_email_config(job_id: str, user_id: int) -> bool:
    """Delete a job email configuration."""
    db = None
    try:
        db = await get_db()
        
        # Get existing configuration
        result = await db.execute(
            select(JobEmailConfig).where(
                JobEmailConfig.job_id == job_id,
                JobEmailConfig.user_id == user_id
            )
        )
        config = result.scalar_one_or_none()
        if not config:
            raise ValueError(f"Email configuration for job '{job_id}' not found for this user")

        await db.delete(config)
        await db.commit()
        return True

    except Exception as e:
        logger.error(f"Error deleting job email configuration: {e}")
        if db is not None:
            try:
                await db.rollback()
            except Exception:
                pass
        raise e
    finally:
        if db is not None:
            await db.close()


async def get_job_email_config_dict(job_id: str, user_id: int) -> Dict[str, Any]:
    """Get job email configuration as a dictionary (for backward compatibility)."""
    try:
        config = await get_job_email_config(job_id, user_id)
        if not config:
            # Return default configuration
            return {
                "enabled": True,
                "recipient": "",
                "subject": f"{job_id.replace('_', ' ').title()} Report",
                "template": f"{job_id}_template.html",
                "recipient_name": "User",
                "send_empty_reports": False,
                "html_format": True,
                "retry_failed_sends": True,
                "max_retries": 3,
            }
        
        return {
            "enabled": config.enabled,
            "recipient": config.recipient,
            "subject": config.subject,
            "template": config.template,
            "recipient_name": config.recipient_name,
            "send_empty_reports": config.send_empty_reports,
            "html_format": config.html_format,
            "retry_failed_sends": config.retry_failed_sends,
            "max_retries": config.max_retries,
        }

    except Exception as e:
        logger.error(f"Error getting job email configuration as dict: {e}")
        # Return default configuration on error
        return {
            "enabled": True,
            "recipient": "",
            "subject": f"{job_id.replace('_', ' ').title()} Report",
            "template": f"{job_id}_template.html",
            "recipient_name": "User",
            "send_empty_reports": False,
            "html_format": True,
            "retry_failed_sends": True,
            "max_retries": 3,
        }


def get_available_job_types() -> List[Dict[str, str]]:
    """Get list of available job types that can have email configurations."""
    return [
        {
            "id": "weekly_reporter",
            "name": "Weekly Reporter",
            "description": "Sends weekly progress reports every Friday (except last Friday of month)"
        },
        {
            "id": "monthly_reporter", 
            "name": "Monthly Reporter",
            "description": "Sends monthly progress reports on the last Friday of each month"
        },
        {
            "id": "task_lifecycle_manager",
            "name": "Task Lifecycle Manager",
            "description": "Manages task lifecycle and cleanup operations"
        }
    ]


def get_email_config_schema() -> Dict[str, Dict[str, Any]]:
    """Get the schema for email configuration fields."""
    return {
        "enabled": {
            "type": "boolean",
            "default": True,
            "description": "Enable or disable email functionality for this job"
        },
        "recipient": {
            "type": "string",
            "default": "",
            "description": "Email address to send reports to",
            "required": True
        },
        "subject": {
            "type": "string",
            "default": "Progress Report",
            "description": "Email subject line",
            "required": True
        },
        "template": {
            "type": "string",
            "default": "default_template.html",
            "description": "Email template file name"
        },
        "recipient_name": {
            "type": "string",
            "default": "User",
            "description": "Recipient name for personalization"
        },
        "send_empty_reports": {
            "type": "boolean",
            "default": False,
            "description": "Send reports even when no tasks are found"
        },
        "html_format": {
            "type": "boolean",
            "default": True,
            "description": "Send emails in HTML format"
        },
        "retry_failed_sends": {
            "type": "boolean",
            "default": True,
            "description": "Retry failed email sends"
        },
        "max_retries": {
            "type": "integer",
            "default": 3,
            "description": "Maximum number of retry attempts for failed sends"
        }
    }