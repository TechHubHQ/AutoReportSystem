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

from app.core.jobs.job_config import JOB_CONFIG

logger = logging.getLogger("async_scheduler")

# Thread-safe scheduler instance management
_scheduler_lock = threading.Lock()
_scheduler_instance = None
_scheduler_thread = None
_scheduler_started = False
_scheduler_start_time = None
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
    global execution_history

    scheduler = get_scheduler_instance()
    if not scheduler:
        logger.warning("Health check: Scheduler not available")
        return

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
    global _scheduler_instance, _scheduler_start_time

    pid = os.getpid()
    thread_id = threading.get_ident()
    thread_name = threading.current_thread().name
    logger.info(
        f"Starting async scheduler. PID: {pid}, Thread ID: {thread_id}, Thread Name: {thread_name}")

    # Create scheduler instance
    scheduler = AsyncIOScheduler()

    # Set the global instance and start time in a thread-safe way
    with _scheduler_lock:
        _scheduler_instance = scheduler
        _scheduler_start_time = datetime.datetime.now()
        logger.info(f"Scheduler instance set: {_scheduler_instance}")
        logger.info(f"Scheduler start time: {_scheduler_start_time}")

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
            await asyncio.sleep(3600)  # Sleep for 1 hour
    except (KeyboardInterrupt, SystemExit):
        with _scheduler_lock:
            if _scheduler_instance:
                _scheduler_instance.shutdown()
                _scheduler_instance = None
        logger.info("Scheduler shutdown successfully.")


def get_scheduler_instance():
    """Get the current scheduler instance safely."""
    global _scheduler_instance
    with _scheduler_lock:
        if _scheduler_instance:
            logger.debug(
                f"Scheduler instance found: running={_scheduler_instance.running}")
        else:
            logger.debug("No scheduler instance found")
        return _scheduler_instance


def is_scheduler_running():
    """Check if scheduler is running."""
    global _scheduler_instance
    with _scheduler_lock:
        return _scheduler_instance is not None and _scheduler_instance.running


def get_scheduler_uptime():
    """Get scheduler uptime as a formatted string."""
    global _scheduler_start_time, _scheduler_instance
    
    with _scheduler_lock:
        if not _scheduler_instance or not _scheduler_instance.running or not _scheduler_start_time:
            return "0:00:00"
        
        uptime_delta = datetime.datetime.now() - _scheduler_start_time
        
        # Format uptime as HH:MM:SS or D days, HH:MM:SS
        total_seconds = int(uptime_delta.total_seconds())
        days = total_seconds // 86400
        hours = (total_seconds % 86400) // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        
        if days > 0:
            return f"{days}d {hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


def get_scheduler_debug_info():
    """Get detailed scheduler debug information."""
    global _scheduler_instance, _scheduler_thread, _scheduler_started

    with _scheduler_lock:
        return {
            'scheduler_instance': _scheduler_instance is not None,
            'scheduler_running': _scheduler_instance.running if _scheduler_instance else False,
            'thread_exists': _scheduler_thread is not None,
            'thread_alive': _scheduler_thread.is_alive() if _scheduler_thread else False,
            'scheduler_started_flag': _scheduler_started,
            'jobs_count': len(_scheduler_instance.get_jobs()) if _scheduler_instance else 0,
            'uptime': get_scheduler_uptime()
        }


def ensure_scheduler_running():
    """Ensure the scheduler is running, start it if not."""
    global _scheduler_instance, _scheduler_thread, _scheduler_started

    with _scheduler_lock:
        # Check if scheduler is already running
        if _scheduler_instance and _scheduler_instance.running:
            return True

        # Check if we already started the scheduler thread
        if _scheduler_started and _scheduler_thread and _scheduler_thread.is_alive():
            logger.info(
                "Scheduler thread is alive, waiting for initialization...")
            return True

        # Start new scheduler thread
        if not _scheduler_started or not _scheduler_thread or not _scheduler_thread.is_alive():
            logger.info("Starting new scheduler thread...")
            _scheduler_thread = threading.Thread(
                target=run_scheduler, daemon=True)
            _scheduler_thread.start()
            _scheduler_started = True

            # Wait a bit for the scheduler to initialize
            import time
            time.sleep(2)

            return _scheduler_instance is not None

    return False


def run_scheduler():
    """Run the async scheduler in a separate thread"""
    try:
        asyncio.run(start_scheduler())
    except Exception as e:
        logger.error(f"Scheduler thread failed: {e}")
        global _scheduler_started
        _scheduler_started = False
