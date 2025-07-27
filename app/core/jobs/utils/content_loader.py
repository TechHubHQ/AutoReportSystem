from app.core.interface.task_interface import *


async def load_content(timeframe):
    if timeframe == "weekly":
        content = get_weekly_tasks()
    if timeframe == "monthly":
        content = get_monthly_tasks()
    return content
