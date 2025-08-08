"""Job interface for managing scheduled jobs and monitoring."""

from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import time
import pytz
import inspect
from apscheduler.triggers.date import DateTrigger
from app.core.jobs.scheduler import get_scheduler_instance, is_scheduler_running, ensure_scheduler_running, get_scheduler_uptime, execution_history


async def get_all_jobs() -> List[Dict[str, Any]]:
    """Get all jobs from scheduler with real-time information."""
    from app.core.jobs.job_config import JOB_CONFIG
    import asyncio

    job_list = []

    # Ensure scheduler is running
    ensure_scheduler_running()

    # Get scheduler instance with retry mechanism
    scheduler = get_scheduler_instance()

    # If scheduler is None, wait a bit and try again (it might be starting up)
    if scheduler is None:
        await asyncio.sleep(1)
        scheduler = get_scheduler_instance()

    # If scheduler is still not available, return basic config info
    if not scheduler:
        for job_config in JOB_CONFIG:
            job_data = {
                'id': job_config['id'],
                'name': job_config['id'].replace('_', ' ').title(),
                'description': f"Automated {job_config['id'].replace('_', ' ')} job",
                'schedule_type': str(job_config['trigger']),
                'is_active': False,
                'is_custom': False,
                'last_run': None,
                'next_run': None,
                'created_at': datetime.now(),
                'status': 'not_scheduled'
            }
            job_list.append(job_data)
        return job_list


async def run_job_now(job_id: str) -> Dict[str, Any]:
    """Schedule a one-off immediate run of a configured job.

    Returns a dict with status and scheduling info.
    """
    from app.core.jobs.job_config import JOB_CONFIG

    # Ensure scheduler running
    ensure_scheduler_running()
    scheduler = get_scheduler_instance()
    if not scheduler:
        return {"ok": False, "message": "Scheduler is not available"}

    # Find job config
    job_config = next((j for j in JOB_CONFIG if j['id'] == job_id), None)
    if not job_config:
        return {"ok": False, "message": f"Job '{job_id}' not found"}

    job_func = job_config["func"]

    # Schedule a one-off run a moment in the future
    run_date = datetime.now(pytz.utc) + timedelta(seconds=2)
    manual_id = f"{job_id}_manual_{int(time.time())}"

    # Prepare kwargs to support force-run if the function accepts it
    kwargs = {}
    try:
        sig = inspect.signature(job_func)
        if 'force' in sig.parameters:
            kwargs['force'] = True
    except Exception:
        pass

    try:
        scheduler.add_job(
            id=manual_id,
            func=job_func,
            trigger=DateTrigger(run_date=run_date),
            replace_existing=False,
            max_instances=job_config.get("max_instances", 1),
            kwargs=kwargs if kwargs else None,
        )
        return {
            "ok": True,
            "message": f"Job '{job_id}' scheduled to run now",
            "scheduled_id": manual_id,
            "run_date": run_date,
        }
    except Exception as e:
        return {"ok": False, "message": f"Failed to schedule job: {e}"}

    # Get real-time job information from scheduler
    scheduled_jobs = scheduler.get_jobs()

    for job_config in JOB_CONFIG:
        # Find the corresponding scheduled job
        scheduled_job = next(
            (j for j in scheduled_jobs if j.id == job_config['id']), None)

        # Get execution history for this job
        job_history = execution_history.get(job_config['id'], [])
        last_execution = job_history[-1] if job_history else None

        job_data = {
            'id': job_config['id'],
            'name': job_config['id'].replace('_', ' ').title(),
            'description': f"Automated {job_config['id'].replace('_', ' ')} job",
            'schedule_type': str(job_config['trigger']),
            'is_active': scheduled_job is not None,
            'is_custom': False,
            'last_run': last_execution.execution_time if last_execution else None,
            'next_run': scheduled_job.next_run_time if scheduled_job else None,
            'created_at': datetime.now(),
            'status': 'running' if scheduled_job else 'not_scheduled'
        }
        job_list.append(job_data)

    return job_list


async def get_job_statistics() -> Dict[str, Any]:
    """Get job statistics from scheduler."""
    from app.core.jobs.job_config import JOB_CONFIG

    total = len(JOB_CONFIG)
    active = 0

    # Ensure scheduler is running
    ensure_scheduler_running()

    scheduler = get_scheduler_instance()
    if scheduler:
        scheduled_jobs = scheduler.get_jobs()
        # Count how many of our configured jobs are actually scheduled
        for job_config in JOB_CONFIG:
            if any(j.id == job_config['id'] for j in scheduled_jobs):
                active += 1

    return {
        'total': total,
        'active': active,
        'inactive': total - active,
        'custom': 0,
        'system': total
    }


async def get_scheduler_status() -> Dict[str, Any]:
    """Get current scheduler status."""
    # Ensure scheduler is running
    ensure_scheduler_running()

    scheduler = get_scheduler_instance()

    if not scheduler:
        return {
            'running': False,
            'jobs_count': 0,
            'health': 'stopped',
            'uptime': '0:00:00'
        }

    return {
        'running': scheduler.running,
        'jobs_count': len(scheduler.get_jobs()),
        'health': 'healthy' if scheduler.running else 'unhealthy',
        'uptime': get_scheduler_uptime()
    }


async def get_job_execution_history(job_id: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
    """Get job execution history."""
    history = []

    if job_id:
        job_history = execution_history.get(job_id, [])
    else:
        job_history = []
        for job_executions in execution_history.values():
            job_history.extend(job_executions)

    # Sort by execution time and limit
    job_history.sort(key=lambda x: x.execution_time, reverse=True)
    job_history = job_history[:limit]

    for record in job_history:
        history.append({
            'job_id': record.job_id,
            'execution_time': record.execution_time,
            'scheduled_time': record.scheduled_run_time,
            'successful': record.successful,
            'error': record.error,
            'duration': '0:00:05'  # Mock duration
        })

    return history


async def get_job_health_metrics() -> Dict[str, Any]:
    """Get job health metrics."""
    now = datetime.now()
    one_hour_ago = now - timedelta(hours=1)

    total_executions = 0
    successful_executions = 0
    failed_executions = 0

    for job_executions in execution_history.values():
        recent_executions = [
            r for r in job_executions
            if r.execution_time >= one_hour_ago
        ]
        total_executions += len(recent_executions)
        successful_executions += sum(
            1 for r in recent_executions if r.successful)
        failed_executions += sum(1 for r in recent_executions if not r.successful)

    success_rate = (successful_executions / total_executions *
                    100) if total_executions > 0 else 100

    return {
        'total_executions': total_executions,
        'successful_executions': successful_executions,
        'failed_executions': failed_executions,
        'success_rate': success_rate,
        'avg_execution_time': '0:00:03',  # Mock average
        'last_execution': now - timedelta(minutes=5) if total_executions > 0 else None
    }
