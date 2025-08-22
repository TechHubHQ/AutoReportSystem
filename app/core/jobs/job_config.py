from apscheduler.triggers.cron import CronTrigger
import pytz

# Import job functions - these will be imported dynamically to avoid circular imports
# from .tasks.weekly_reporter import send_weekly_report
# from .tasks.monthly_reporter import send_monthly_report
# from .tasks.task_lifecycle_manager import manage_task_lifecycle

# Default notification settings
NOTIFICATION_SETTINGS = {
    "notify_on_success": False,
    "notify_on_failure": True,
    "admin_email": "admin@medicasapp.com",
}


def _import_job_function(module_path: str, function_name: str):
    """Dynamically import job function to avoid circular imports."""
    import importlib
    module = importlib.import_module(module_path)
    return getattr(module, function_name)

# Policy:
# - Weekly: every Friday except the last Friday of the month (handled in task)
# - Monthly: only the last Friday of the month (handled in task)
# Both run at 21:50 IST
# - Task Lifecycle: daily at 02:00 IST (low traffic time)
JOB_CONFIG = [
    {
        "id": "weekly_reporter",
        "func": lambda: _import_job_function("app.core.jobs.tasks.weekly_reporter", "send_weekly_report"),
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
        "notification_config": NOTIFICATION_SETTINGS,
    },
    {
        "id": "monthly_reporter",
        "func": lambda: _import_job_function("app.core.jobs.tasks.monthly_reporter", "send_monthly_report"),
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
        "notification_config": NOTIFICATION_SETTINGS,
    },
    {
        "id": "task_lifecycle_manager",
        "func": lambda: _import_job_function("app.core.jobs.tasks.task_lifecycle_manager", "manage_task_lifecycle"),
        "trigger": CronTrigger(
            hour=2,  # 2:00 AM IST (low traffic time)
            minute=0,
            timezone=pytz.timezone('Asia/Kolkata')  # IST timezone
        ),
        "max_instances": 1,
        "replace_existing": True,
        "coalesce": True,  # Combine multiple pending executions into one
        "misfire_grace_time": 600,  # 10 minutes grace time for missed executions
        "notification_config": NOTIFICATION_SETTINGS,
    }
]

# Note: Email configuration is now handled through the UI and database
# See app.core.interface.job_email_config_interface for email configuration management
# This removes the circular import dependency that existed before
