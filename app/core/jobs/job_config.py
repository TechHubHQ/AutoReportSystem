from apscheduler.triggers.cron import CronTrigger
from .tasks.weekly_reporter import send_weekly_report
from .tasks.monthly_reporter import send_monthly_report
from .tasks.task_lifecycle_manager import manage_task_lifecycle
import pytz

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
    }
]
