"""=====================================================================
Enhanced Async Scheduler with Session Independence and Comprehensive Logging

Version History:
    1.0.0 (2024-12-24) - Initial Release
    1.1.0 (2025-01-27) - Enhanced startup logging with detailed job information
    2.0.0 (2025-01-27) - Session-independent scheduler with dynamic job imports
===================================================================="""

import asyncio
import psutil
import logging
import os
import sys
import threading
import datetime
from collections import defaultdict
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR

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
    logger.info(f"✅ Job '{event.job_id}' executed successfully at {record.execution_time}")
    print(f"[SCHEDULER] ✅ Job '{event.job_id}' executed successfully at {record.execution_time}")


def job_error_event_listener(event):
    record = ExecutionRecord(
        event.job_id, event.scheduled_run_time, False, str(event.exception))
    execution_history[event.job_id].append(record)
    logger.error(f"❌ Job '{event.job_id}' failed at {record.execution_time}: {event.exception}")
    print(f"[SCHEDULER] ❌ Job '{event.job_id}' failed at {record.execution_time}: {event.exception}")
    
    # Log additional details for debugging
    if hasattr(event, 'retval'):
        logger.error(f"📋 Job '{event.job_id}' return value: {event.retval}")
    if hasattr(event, 'traceback'):
        logger.error(f"📋 Job '{event.job_id}' traceback: {event.traceback}")


def log_to_console_and_file(message, level="INFO"):
    """Force log to both console and file"""
    # Log to file
    if level.upper() == "DEBUG":
        logger.debug(message)
    elif level.upper() == "INFO":
        logger.info(message)
    elif level.upper() == "WARNING":
        logger.warning(message)
    elif level.upper() == "ERROR":
        logger.error(message)
    else:
        logger.info(message)
    
    # Also force to stdout
    print(f"[SCHEDULER] {message}")
    sys.stdout.flush()


def get_session_independent_job_config():
    """Get job configuration without importing job functions that have database dependencies"""
    from apscheduler.triggers.cron import CronTrigger
    import pytz
    
    # Session-independent job configuration
    # Jobs will be imported dynamically only when they execute
    return [
        {
            "id": "weekly_reporter",
            "module_path": "app.core.jobs.tasks.weekly_reporter",
            "function_name": "send_weekly_report",
            "trigger": CronTrigger(
                day_of_week="fri",
                hour=21,
                minute=50,
                timezone=pytz.timezone('Asia/Kolkata')
            ),
            "max_instances": 1,
            "replace_existing": True,
            "coalesce": True,
            "misfire_grace_time": 300,
        },
        {
            "id": "monthly_reporter", 
            "module_path": "app.core.jobs.tasks.monthly_reporter",
            "function_name": "send_monthly_report",
            "trigger": CronTrigger(
                day_of_week="fri",
                hour=21,
                minute=50,
                timezone=pytz.timezone('Asia/Kolkata')
            ),
            "max_instances": 1,
            "replace_existing": True,
            "coalesce": True,
            "misfire_grace_time": 300,
        },
        {
            "id": "task_lifecycle_manager",
            "module_path": "app.core.jobs.tasks.task_lifecycle_manager", 
            "function_name": "manage_task_lifecycle",
            "trigger": CronTrigger(
                hour=2,
                minute=0,
                timezone=pytz.timezone('Asia/Kolkata')
            ),
            "max_instances": 1,
            "replace_existing": True,
            "coalesce": True,
            "misfire_grace_time": 600,
        }
    ]


async def dynamic_job_wrapper(module_path, function_name, *args, **kwargs):
    """Dynamically import and execute job function only when needed"""
    try:
        log_to_console_and_file(f"🔧 Dynamically importing {module_path}.{function_name}", "INFO")
        
        import importlib
        module = importlib.import_module(module_path)
        job_func = getattr(module, function_name)
        
        log_to_console_and_file(f"✅ Successfully imported {function_name}", "INFO")
        
        # Execute the job function
        result = await job_func(*args, **kwargs)
        
        log_to_console_and_file(f"✅ Job {function_name} completed successfully", "INFO")
        return result
        
    except Exception as e:
        log_to_console_and_file(f"❌ Error in dynamic job execution: {e}", "ERROR")
        raise


async def simple_health_check():
    """Simple health check without database dependencies"""
    scheduler = get_scheduler_instance()
    if not scheduler:
        log_to_console_and_file("⚠️  Health check: Scheduler not available", "WARNING")
        return

    pid = os.getpid()
    thread_id = threading.get_ident()
    thread_name = threading.current_thread().name

    log_to_console_and_file(f"💓 Scheduler health check: ALIVE at PID: {pid}, Thread ID: {thread_id}, Thread Name: {thread_name}", "INFO")

    try:
        cpu_usage = psutil.cpu_percent(interval=1)
        memory_info = psutil.virtual_memory()
        log_to_console_and_file(f"📊 System resources - CPU: {cpu_usage}%, Memory: {memory_info.percent}%", "INFO")
    except Exception as e:
        log_to_console_and_file(f"⚠️  Could not get system resources: {e}", "WARNING")

    log_to_console_and_file(f"🏃 Scheduler running: {scheduler.running}", "INFO")
    log_to_console_and_file(f"📋 Number of jobs: {len(scheduler.get_jobs())}", "INFO")

    for job in scheduler.get_jobs():
        log_to_console_and_file(f"🕐 Job '{job.id}' next run at {job.next_run_time} (max_instances: {job.max_instances})", "INFO")

    # Schedule next health check
    scheduler.add_job(
        id="health_check",
        func=simple_health_check,
        trigger="interval",
        hours=1,
        replace_existing=True,
        max_instances=1,
        coalesce=True
    )


async def start_scheduler():
    global _scheduler_instance, _scheduler_start_time

    startup_time = datetime.datetime.now()
    pid = os.getpid()
    thread_id = threading.get_ident()
    thread_name = threading.current_thread().name

    log_to_console_and_file("="*80, "INFO")
    log_to_console_and_file("🚀 ENHANCED SCHEDULER STARTUP INITIATED", "INFO")
    log_to_console_and_file("="*80, "INFO")
    log_to_console_and_file(f"📅 Startup Time: {startup_time.strftime('%Y-%m-%d %H:%M:%S %Z')}", "INFO")
    log_to_console_and_file(f"🔧 Process ID: {pid}", "INFO")
    log_to_console_and_file(f"🧵 Thread ID: {thread_id}", "INFO")
    log_to_console_and_file(f"📛 Thread Name: {thread_name}", "INFO")
    log_to_console_and_file(f"🐍 Python Version: {os.sys.version.split()[0]}", "INFO")
    log_to_console_and_file("💡 Session-independent scheduler - no database dependencies at startup", "INFO")
    log_to_console_and_file("-"*80, "INFO")

    # Create scheduler instance with improved configuration
    log_to_console_and_file("⚙️  Creating AsyncIOScheduler instance...", "INFO")
    scheduler = AsyncIOScheduler(
        job_defaults={
            'coalesce': True,
            'max_instances': 1,
            'misfire_grace_time': 300
        }
    )
    log_to_console_and_file("✅ Scheduler instance created successfully", "INFO")
    log_to_console_and_file("   📋 Default job settings:", "INFO")
    log_to_console_and_file("      • Coalesce: True (combine multiple pending executions)", "INFO")
    log_to_console_and_file("      • Max Instances: 1 (prevent concurrent runs)", "INFO")
    log_to_console_and_file("      • Misfire Grace Time: 300s (5 minutes)", "INFO")

    # Set the global instance and start time in a thread-safe way
    with _scheduler_lock:
        _scheduler_instance = scheduler
        _scheduler_start_time = startup_time
        log_to_console_and_file("🔒 Scheduler instance set in thread-safe context", "INFO")
        log_to_console_and_file(f"⏰ Scheduler start time recorded: {_scheduler_start_time}", "INFO")

    # Add event listeners
    log_to_console_and_file("🎧 Adding event listeners...", "INFO")
    scheduler.add_listener(job_executed_event_listener, EVENT_JOB_EXECUTED)
    scheduler.add_listener(job_error_event_listener, EVENT_JOB_ERROR)
    log_to_console_and_file("✅ Event listeners added (job execution & error tracking)", "INFO")

    # Add jobs from session-independent configuration
    job_configs = get_session_independent_job_config()
    log_to_console_and_file("-"*80, "INFO")
    log_to_console_and_file(f"📋 CONFIGURING SCHEDULED JOBS ({len(job_configs)} jobs found)", "INFO")
    log_to_console_and_file("-"*80, "INFO")

    for i, job_config in enumerate(job_configs, 1):
        log_to_console_and_file(f"🔧 [{i}/{len(job_configs)}] Configuring job: {job_config['id']}", "INFO")

        try:
            # Extract trigger details for logging
            trigger = job_config["trigger"]
            trigger_info = []

            if hasattr(trigger, 'day_of_week') and trigger.day_of_week:
                trigger_info.append(f"Day: {trigger.day_of_week}")
            if hasattr(trigger, 'hour') and trigger.hour is not None:
                trigger_info.append(f"Hour: {trigger.hour:02d}")
            if hasattr(trigger, 'minute') and trigger.minute is not None:
                trigger_info.append(f"Minute: {trigger.minute:02d}")
            if hasattr(trigger, 'timezone') and trigger.timezone:
                trigger_info.append(f"Timezone: {trigger.timezone}")

            trigger_desc = ", ".join(trigger_info) if trigger_info else str(trigger)

            # Add job with dynamic wrapper
            scheduler.add_job(
                id=job_config["id"],
                func=dynamic_job_wrapper,
                args=[job_config["module_path"], job_config["function_name"]],
                trigger=job_config["trigger"],
                max_instances=job_config.get("max_instances", 1),
                replace_existing=job_config.get("replace_existing", True),
                coalesce=job_config.get("coalesce", True),
                misfire_grace_time=job_config.get("misfire_grace_time", 300),
            )

            log_to_console_and_file(f"   ✅ Function: {job_config['function_name']} (dynamic import)", "INFO")
            log_to_console_and_file(f"   📅 Schedule: {trigger_desc}", "INFO")
            log_to_console_and_file(f"   ⚙️  Max Instances: {job_config.get('max_instances', 1)}", "INFO")
            log_to_console_and_file(f"   🔄 Coalesce: {job_config.get('coalesce', True)}", "INFO")
            log_to_console_and_file(f"   ⏱️  Misfire Grace: {job_config.get('misfire_grace_time', 300)}s", "INFO")
            log_to_console_and_file(f"   ✅ Job '{job_config['id']}' scheduled successfully", "INFO")

        except Exception as e:
            log_to_console_and_file(f"   ❌ Failed to configure job '{job_config['id']}': {e}", "ERROR")
            log_to_console_and_file(f"   📋 Job config: {job_config}", "ERROR")

        if i < len(job_configs):
            log_to_console_and_file("   " + "-"*50, "INFO")

    # Start the scheduler
    log_to_console_and_file("-"*80, "INFO")
    log_to_console_and_file("🚀 STARTING SCHEDULER ENGINE", "INFO")
    log_to_console_and_file("-"*80, "INFO")

    try:
        scheduler.start()
        actual_start_time = datetime.datetime.now()
        startup_duration = (actual_start_time - startup_time).total_seconds()

        log_to_console_and_file("✅ Scheduler engine started successfully!", "INFO")
        log_to_console_and_file(f"⏱️  Startup duration: {startup_duration:.2f} seconds", "INFO")
        log_to_console_and_file("🏃 Scheduler is now running and ready to execute jobs", "INFO")

        # Log next run times for all jobs
        log_to_console_and_file("-"*80, "INFO")
        log_to_console_and_file("📅 NEXT SCHEDULED EXECUTIONS", "INFO")
        log_to_console_and_file("-"*80, "INFO")

        jobs = scheduler.get_jobs()
        if jobs:
            for job in sorted(jobs, key=lambda j: j.next_run_time or datetime.datetime.max):
                if job.next_run_time:
                    log_to_console_and_file(f"🕐 {job.id}: {job.next_run_time.strftime('%Y-%m-%d %H:%M:%S %Z')}", "INFO")
                else:
                    log_to_console_and_file(f"⏸️  {job.id}: No next run time scheduled", "INFO")
        else:
            log_to_console_and_file("⚠️  No jobs found in scheduler!", "WARNING")

    except Exception as e:
        log_to_console_and_file(f"❌ Failed to start scheduler: {e}", "ERROR")
        raise

    log_to_console_and_file("="*80, "INFO")
    log_to_console_and_file("🎉 ENHANCED SCHEDULER STARTUP COMPLETED SUCCESSFULLY", "INFO")
    log_to_console_and_file("="*80, "INFO")

    # Run initial health check
    await simple_health_check()

    try:
        while True:
            await asyncio.sleep(3600)  # Sleep for 1 hour
    except (KeyboardInterrupt, SystemExit):
        log_to_console_and_file("-"*80, "INFO")
        log_to_console_and_file("🛑 SCHEDULER SHUTDOWN INITIATED", "INFO")
        log_to_console_and_file("-"*80, "INFO")
        shutdown_time = datetime.datetime.now()

        with _scheduler_lock:
            if _scheduler_instance:
                uptime = get_scheduler_uptime()
                log_to_console_and_file(f"⏰ Shutdown time: {shutdown_time.strftime('%Y-%m-%d %H:%M:%S %Z')}", "INFO")
                log_to_console_and_file(f"⏱️  Total uptime: {uptime}", "INFO")
                log_to_console_and_file("🔧 Shutting down scheduler instance...", "INFO")
                _scheduler_instance.shutdown()
                _scheduler_instance = None
                log_to_console_and_file("✅ Scheduler shutdown completed successfully", "INFO")

        log_to_console_and_file("="*80, "INFO")


def get_scheduler_instance():
    """Get the current scheduler instance safely."""
    global _scheduler_instance
    with _scheduler_lock:
        if _scheduler_instance:
            logger.debug(f"Scheduler instance found: running={_scheduler_instance.running}")
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
            log_to_console_and_file("🏃 Scheduler is already running", "DEBUG")
            return True

        # Check if we already started the scheduler thread
        if _scheduler_started and _scheduler_thread and _scheduler_thread.is_alive():
            log_to_console_and_file("🧵 Scheduler thread is alive, waiting for initialization...", "INFO")
            # Wait a bit longer for the scheduler to fully initialize
            import time
            time.sleep(3)
            # Check again if scheduler instance is available
            return _scheduler_instance is not None

        # Start new scheduler thread
        if not _scheduler_started or not _scheduler_thread or not _scheduler_thread.is_alive():
            log_to_console_and_file("🚀 Starting new enhanced scheduler thread...", "INFO")
            _scheduler_thread = threading.Thread(
                target=run_scheduler, daemon=True)
            _scheduler_thread.start()
            _scheduler_started = True

            # Wait longer for the scheduler to initialize
            import time
            time.sleep(5)  # Increased wait time

            # Check if scheduler instance is available
            if _scheduler_instance is not None:
                log_to_console_and_file("✅ Scheduler thread started and instance is available", "INFO")
                return True
            else:
                log_to_console_and_file("⚠️  Scheduler thread started but instance not yet available", "WARNING")
                return False

    return False


def run_scheduler():
    """Run the async scheduler in a separate thread"""
    try:
        asyncio.run(start_scheduler())
    except Exception as e:
        log_to_console_and_file(f"❌ Scheduler thread failed: {e}", "ERROR")
        global _scheduler_started
        _scheduler_started = False