from apscheduler.triggers.cron import CronTrigger
from .tasks.weekly_reporter import send_weekly_report
from .tasks.monthly_reporter import send_monthly_report
import pytz

# Weekly: 1st, 2nd, and 3rd Friday of each month at 21:50 IST
# Monthly: Last Friday of each month at 21:50 IST
JOB_CONFIG = [
    {
        "id": "weekly_reporter",
        "func": send_weekly_report,
        "trigger": CronTrigger(
            day="1-21",  # Only days 1-21 can be the 1st, 2nd, or 3rd Friday
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
            day="22-31",  # Last possible week of the month
            day_of_week="fri",  # Only on Fridays
            hour=21,
            minute=50,
            timezone=pytz.timezone('Asia/Kolkata')  # IST timezone
        ),
        "max_instances": 1,
        "replace_existing": True,
    }
]
