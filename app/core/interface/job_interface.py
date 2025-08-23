"""Job interface for managing scheduled jobs and monitoring."""

from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import time
import pytz
import inspect
from apscheduler.triggers.date import DateTrigger
from app.core.jobs.scheduler import get_scheduler_instance, is_scheduler_running, ensure_scheduler_running, get_scheduler_uptime, execution_history
from app.config.logging_config import get_logger

logger = get_logger(__name__)


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

    # Get real-time job information from scheduler
    scheduled_jobs = scheduler.get_jobs()

    for job_config in JOB_CONFIG:
        # Find the corresponding scheduled job
        scheduled_job = next(
            (j for j in scheduled_jobs if j.id == job_config['id']), None)

        # Get execution history for this job
        job_history = execution_history.get(job_config['id'], [])
        last_execution = job_history[-1] if job_history else None

        # Safely get next_run_time from scheduled job
        next_run_time = None
        if scheduled_job:
            try:
                next_run_time = getattr(scheduled_job, 'next_run_time', None)
            except AttributeError:
                logger.warning(f"Scheduled job {job_config['id']} has no next_run_time attribute")
                next_run_time = None
        
        job_data = {
            'id': job_config['id'],
            'name': job_config['id'].replace('_', ' ').title(),
            'description': f"Automated {job_config['id'].replace('_', ' ')} job",
            'schedule_type': str(job_config['trigger']),
            'is_active': scheduled_job is not None,
            'is_custom': False,
            'last_run': last_execution.execution_time if last_execution else None,
            'next_run': next_run_time,
            'created_at': datetime.now(),
            'status': 'running' if scheduled_job else 'not_scheduled'
        }
        job_list.append(job_data)

    return job_list


async def run_job_now(job_id: str) -> Dict[str, Any]:
    """Execute a job immediately and return the results.

    Returns a dict with execution status and results.
    """
    from app.core.jobs.job_config import JOB_CONFIG
    import asyncio
    import traceback

    # Find job config
    job_config = next((j for j in JOB_CONFIG if j['id'] == job_id), None)
    if not job_config:
        return {"ok": False, "message": f"Job '{job_id}' not found"}

    job_func = job_config["func"]
    manual_id = f"{job_id}_manual_{int(time.time())}"

    # Get the actual function from the lambda
    try:
        actual_func = job_func()
    except Exception as e:
        return {"ok": False, "message": f"Failed to get job function: {e}"}
    
    # Prepare kwargs to support force-run, job_id, and user_id if the function accepts them
    kwargs = {}
    try:
        sig = inspect.signature(actual_func)
        if 'force' in sig.parameters:
            kwargs['force'] = True
        if 'job_id' in sig.parameters:
            kwargs['job_id'] = manual_id
        if 'user_id' in sig.parameters:
            # Get current user from session
            from app.security.route_protection import RouteProtection
            current_user = RouteProtection.get_current_user()
            if current_user:
                kwargs['user_id'] = current_user.get('id')
    except Exception:
        pass

    # Execute the job immediately
    try:
        logger.info(f"Executing job {job_id} immediately with kwargs: {kwargs}")
        
        # Check if the function is async
        if asyncio.iscoroutinefunction(actual_func):
            result = await actual_func(**kwargs)
        else:
            # Run sync function in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, lambda: actual_func(**kwargs))
        
        logger.info(f"Job {job_id} executed successfully. Result type: {type(result)}")
        
        # Store the result in global storage for UI display
        from app.core.jobs.job_results_store import store_job_result
        if isinstance(result, dict):
            store_job_result(job_id, result)
            store_job_result(manual_id, result)  # Also store with manual ID
        
        return {
            "ok": True,
            "message": f"Job '{job_id}' executed successfully",
            "execution_id": manual_id,
            "result": result,
            "execution_time": datetime.now().isoformat()
        }
        
    except Exception as e:
        error_msg = f"Job execution failed: {str(e)}"
        logger.error(f"Error executing job {job_id}: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        
        # Store error result
        error_result = {
            'job_id': manual_id,
            'status': 'error',
            'message': error_msg,
            'details': [f"Error: {str(e)}"],
            'users_processed': 0,
            'emails_sent': 0,
            'errors': [str(e)],
            'execution_time': datetime.now().isoformat(),
            'forced': True
        }
        
        from app.core.jobs.job_results_store import store_job_result
        store_job_result(job_id, error_result)
        store_job_result(manual_id, error_result)
        
        return {
            "ok": False, 
            "message": error_msg,
            "execution_id": manual_id,
            "error": str(e),
            "execution_time": datetime.now().isoformat()
        }


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
    """Get job execution history from database."""
    try:
        # Try to get from database first
        from app.core.interface.job_tracking_interface import get_job_execution_history as get_db_history
        db_history = await get_db_history(job_name=job_id, limit=limit)
        
        if db_history:
            # Convert database format to expected format
            history = []
            for record in db_history:
                history.append({
                    'job_id': record['job_name'],
                    'execution_time': record['started_at'],
                    'scheduled_time': record['scheduled_time'],
                    'successful': record['status'] == 'success',
                    'error': record['error_message'],
                    'duration': f"0:00:{record['duration'] or 0:02d}"
                })
            return history
    except Exception as e:
        logger.error(f"Error getting database execution history: {e}")
    
    # Fallback to in-memory history
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


async def get_job_results() -> Dict[str, Any]:
    """Get job execution results from global storage."""
    from app.core.jobs.job_results_store import get_all_job_results, get_job_results_summary
    
    return {
        'results': get_all_job_results(),
        'summary': get_job_results_summary()
    }
