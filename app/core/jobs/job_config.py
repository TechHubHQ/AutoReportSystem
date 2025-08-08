from apscheduler.triggers.cron import CronTrigger
from .tasks.weekly_reporter import send_weekly_report
from .tasks.monthly_reporter import send_monthly_report
import pytz

# Policy:
# - Weekly: every Friday except the last Friday of the month (handled in task)
# - Monthly: only the last Friday of the month (handled in task)
# Both run at 21:50 IST
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
    }
]
