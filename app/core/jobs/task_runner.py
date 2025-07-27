import asyncio
from app.core.jobs.scheduler import scheduler
from app.core.jobs.report_sender import *
from app.core.jobs.utils.dateutils import *


async def run_tasks():
    print("Initializing task scheduling sequence...")

    print("Preparing to schedule weekly report task...")
    # 9:50 p.m. IST is 16:20 UTC (IST is UTC+5:30)
    await scheduler.schedule_task(
        send_w_report,
        "weekly",
        day_of_week=5,
        hour=16,
        minute=20,
    )
    print("Weekly report task scheduled successfully at 16:20 UTC on Friday.")

    print("Initiating inter-task delay... 5 seconds")
    await asyncio.sleep(5)

    print("Preparing to schedule monthly report task...")
    await scheduler.schedule_task(
        send_m_report,
        "monthly",
        next_run=next_monthly_run,
    )
    print("Monthly report task scheduled successfully based on calculated date.")

    print("All tasks scheduled. System ready.")

    while True:
        print("Health check: Task runner is alive and running.")
        await asyncio.sleep(24*60*60)  # sleep for 24 hours


if __name__ == "__main__":
    print("Entering main execution block...\n")
    asyncio.run(run_tasks())
    print("Execution completed. Shutting down...")
