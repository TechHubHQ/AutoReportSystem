import asyncio
from .report_sender import *
from .utils.dateutils import *


# 9:50 p.m. IST is 16:20 UTC (IST is UTC+5:30)
asyncio.run(scheduler.schedule_task(
    send_w_report,
    "weekly",
    day_of_week=4,  # Friday (Monday=0)
    hour=16,
    minute=20,
))


asyncio.run(scheduler.schedule_task(
    send_m_report,
    "monthly",
    next_run=next_monthly_run,
))
