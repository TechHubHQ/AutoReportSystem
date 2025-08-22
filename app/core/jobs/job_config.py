from apscheduler.triggers.cron import CronTrigger
from .tasks.weekly_reporter import send_weekly_report
from .tasks.monthly_reporter import send_monthly_report
from .tasks.task_lifecycle_manager import manage_task_lifecycle
import pytz

# Import email settings from external configuration
try:
    from config.email_settings import (
        WEEKLY_REPORTER_CONFIG,
        MONTHLY_REPORTER_CONFIG,
        TASK_LIFECYCLE_CONFIG,
        NOTIFICATION_SETTINGS,
        get_job_email_config as get_external_email_config
    )
except ImportError:
    # Fallback to default configuration if external config is not available
    WEEKLY_REPORTER_CONFIG = {
        "enabled": True,
        "recipient": "santhosh.bommana@medicasapp.com",
        "subject": "Weekly Progress Report",
        "template": "weekly_update_template.html",
        "recipient_name": "Santosh",
        "send_empty_reports": False,
        "html_format": True,
        "retry_failed_sends": True,
        "max_retries": 3,
    }
    
    MONTHLY_REPORTER_CONFIG = {
        "enabled": True,
        "recipient": "santhosh.bommana@medicasapp.com",
        "subject": "Monthly Progress Report",
        "template": "monthly_update_template.html",
        "recipient_name": "Santosh",
        "send_empty_reports": False,
        "html_format": True,
        "retry_failed_sends": True,
        "max_retries": 3,
    }
    
    TASK_LIFECYCLE_CONFIG = {
        "enabled": False,
    }
    
    NOTIFICATION_SETTINGS = {
        "notify_on_success": False,
        "notify_on_failure": True,
        "admin_email": "admin@medicasapp.com",
    }
    
    def get_external_email_config(job_id: str) -> dict:
        config_map = {
            "weekly_reporter": WEEKLY_REPORTER_CONFIG,
            "monthly_reporter": MONTHLY_REPORTER_CONFIG,
            "task_lifecycle_manager": TASK_LIFECYCLE_CONFIG,
        }
        return config_map.get(job_id, {})

# Policy:
# - Weekly: every Friday except the last Friday of the month (handled in task)
# - Monthly: only the last Friday of the month (handled in task)
# Both run at 21:50 IST
# - Task Lifecycle: daily at 02:00 IST (low traffic time)
JOB_CONFIG = [
    {
        "id": "weekly_reporter",
        "func": send_weekly_report,
        "trigger": CronTrigger(
            day_of_week="fri",
            hour=21,
            minute=50,
            timezone=pytz.timezone('Asia/Kolkata')  # IST timezone
        ),
        "max_instances": 1,
        "replace_existing": True,
        "coalesce": True,  # Combine multiple pending executions into one
        "misfire_grace_time": 300,  # 5 minutes grace time for missed executions
        # Email Configuration for Weekly Reports
        "email_config": WEEKLY_REPORTER_CONFIG,
        "notification_config": NOTIFICATION_SETTINGS,
    },
    {
        "id": "monthly_reporter",
        "func": send_monthly_report,
        "trigger": CronTrigger(
            day_of_week="fri",
            hour=21,
            minute=50,
            timezone=pytz.timezone('Asia/Kolkata')  # IST timezone
        ),
        "max_instances": 1,
        "replace_existing": True,
        "coalesce": True,  # Combine multiple pending executions into one
        "misfire_grace_time": 300,  # 5 minutes grace time for missed executions
        # Email Configuration for Monthly Reports
        "email_config": MONTHLY_REPORTER_CONFIG,
        "notification_config": NOTIFICATION_SETTINGS,
    },
    {
        "id": "task_lifecycle_manager",
        "func": manage_task_lifecycle,
        "trigger": CronTrigger(
            hour=2,  # 2:00 AM IST (low traffic time)
            minute=0,
            timezone=pytz.timezone('Asia/Kolkata')  # IST timezone
        ),
        "max_instances": 1,
        "replace_existing": True,
        "coalesce": True,  # Combine multiple pending executions into one
        "misfire_grace_time": 600,  # 10 minutes grace time for missed executions
        # No email configuration for task lifecycle manager
        "email_config": TASK_LIFECYCLE_CONFIG,
        "notification_config": NOTIFICATION_SETTINGS,
    }
]

# Helper function to get email config for a specific job
def get_job_email_config(job_id: str) -> dict:
    """Get email configuration for a specific job"""
    # First try to get from external config
    external_config = get_external_email_config(job_id)
    if external_config:
        return external_config
    
    # Fallback to job config
    for job in JOB_CONFIG:
        if job["id"] == job_id:
            return job.get("email_config", {})
    return {}

# Helper function to update email config for a specific job
def update_job_email_config(job_id: str, email_config: dict) -> bool:
    """Update email configuration for a specific job"""
    # Try to update external config first
    try:
        from config.email_settings import update_job_email_config as update_external_config
        if update_external_config(job_id, email_config):
            return True
    except ImportError:
        pass
    
    # Fallback to updating job config
    for job in JOB_CONFIG:
        if job["id"] == job_id:
            if "email_config" not in job:
                job["email_config"] = {}
            job["email_config"].update(email_config)
            return True
    return False

# Helper function to get all available email configuration options
def get_available_email_options() -> dict:
    """Get all available email configuration options with descriptions"""
    return {
        "enabled": {
            "type": "boolean",
            "default": True,
            "description": "Enable or disable email functionality for this job"
        },
        "recipient": {
            "type": "string",
            "default": "santhosh.bommana@medicasapp.com",
            "description": "Email address to send reports to"
        },
        "subject": {
            "type": "string",
            "default": "Progress Report",
            "description": "Email subject line"
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

# Helper function to reload email configuration
def reload_email_config():
    """Reload email configuration from external settings"""
    try:
        import importlib
        import config.email_settings
        importlib.reload(config.email_settings)
        
        # Update job configs with reloaded settings
        for job in JOB_CONFIG:
            job_id = job["id"]
            external_config = get_external_email_config(job_id)
            if external_config:
                job["email_config"] = external_config
        
        return True
    except Exception as e:
        print(f"Error reloading email configuration: {e}")
        return False
