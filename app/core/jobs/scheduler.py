"""=====================================================================
Async Scheduler to run jobs in the background.

Version History:
    1.0.0 (2024-12-24)
        - Initial Release
====================================================================="""

import asyncio
import psutil
import logging
import os
import threading
import datetime
from collections import defaultdict
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR

from .job_config import JOB_CONFIG

logger = logging.getLogger("async_scheduler")

scheduler = None
execution_history = defaultdict(list)


class ExecutionRecord:
    def __init__(self, job_id, scheduled_run_time, successful, error=None):
        self.job_id = job_id
        self.scheduled_run_time = scheduled_run_time
        self.successful = successful
        self.error = error
        self.execution_time = datetime.datetime.now()

    def __str__(self):
        status = "SUCCESS" if self.successful else "FAILURE"
        return f"{status} at {self.execution_time} (scheduled: {self.scheduled_run_time})"


def job_executed_event_listener(event):
    record = ExecutionRecord(event.job_id, event.scheduled_run_time, True)
    execution_history[event.job_id].append(record)
    logger.info(
        f"Job {event.job_id} executed successfully at {record.execution_time}")


def job_error_event_listener(event):
    record = ExecutionRecord(
        event.job_id, event.scheduled_run_time, False, str(event.exception))
    execution_history[event.job_id].append(record)
    logger.error(
        f"Job {event.job_id} failed at {record.execution_time}: {event.exception}")


async def health_check():
    global scheduler, execution_history

    one_hour_ago = datetime.datetime.now() - datetime.timedelta(hours=1)
    pid = os.getpid()
    thread_id = threading.get_ident()
    thread_name = threading.current_thread().name

    logger.info(
        f"Async scheduler health check: ALIVE at PID: {pid}, Thread ID: {thread_id}, Thread Name: {thread_name}")

    cpu_usage = psutil.cpu_percent(interval=1)
    memory_info = psutil.virtual_memory()
    logger.info(
        f"System resources - CPU: {cpu_usage}%, Memory: {memory_info.percent}%")

    logger.info(f"Scheduler running: {scheduler.running}")
    logger.info(f"Number of jobs: {len(scheduler.get_jobs())}")

    for job in scheduler.get_jobs():
        logger.info(f"Job {job.id} next run at {job.next_run_time}")

        job_history = execution_history.get(job.id, [])
        if job_history:
            recent_executions = [
                r for r in job_history if r.execution_time >= one_hour_ago]
            success_count = sum(
                1 for record in recent_executions if record.successful)
            failure_count = len(recent_executions) - success_count
            last_run = job_history[-1].execution_time if job_history else "Never"

            logger.info(
                f"Job {job.id} stats (past hour) - Runs: {len(recent_executions)} | Success: {success_count} | Failures: {failure_count} | Last: {last_run}")
        else:
            logger.info(f"Job {job.id} execution stats: No executions yet")

    scheduler.add_job(
        id="health_check",
        func=health_check,
        trigger="interval",
        hours=1,
        replace_existing=True
    )


async def start_scheduler():
    global scheduler

    pid = os.getpid()
    thread_id = threading.get_ident()
    thread_name = threading.current_thread().name
    logger.info(
        f"Starting async scheduler. PID: {pid}, Thread ID: {thread_id}, Thread Name: {thread_name}")

    scheduler = AsyncIOScheduler()

    scheduler.add_listener(job_executed_event_listener, EVENT_JOB_EXECUTED)
    scheduler.add_listener(job_error_event_listener, EVENT_JOB_ERROR)

    for job_config in JOB_CONFIG:
        scheduler.add_job(
            id=job_config["id"],
            func=job_config["func"],
            trigger=job_config["trigger"],
            max_instances=job_config.get("max_instances", 1),
            replace_existing=job_config.get("replace_existing", True),
        )
        logger.info(
            f"Scheduled async job {job_config['id']} with trigger {job_config['trigger']}")

    scheduler.start()
    logger.info("Scheduler started successfully.")

    await health_check()

    try:
        while True:
            await asyncio.sleep(2)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
        logger.info("Scheduler shutdown successfully.")


def run_scheduler():
    """Run the async scheduler in a separate thread"""
    asyncio.run(start_scheduler())
