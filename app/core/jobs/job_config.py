from apscheduler.triggers.cron import CronTrigger
from .tasks.weekly_reporter import send_all_weeklies

JOB_CONFIG = [
    {
        "id": "weekly_reporter",
        "func": send_all_weeklies,
        # "trigger": CronTrigger(day_of_week="fri", hour=0, minute=0),
        "trigger": CronTrigger(minute="*/5"),
        "max_instances": 1,
        "replace_existing": True,
    },
]
