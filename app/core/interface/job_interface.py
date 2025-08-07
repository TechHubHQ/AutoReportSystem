from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy import select, func
from app.database.db_connector import get_async_session
from app.database.models import Job
from app.core.jobs.scheduler import scheduler, execution_history


async def get_all_jobs() -> List[Dict[str, Any]]:
    """Get all jobs from database."""
    async with get_async_session() as session:
        result = await session.execute(select(Job))
        jobs = result.scalars().all()

        job_list = []
        for job in jobs:
            job_data = {
                'id': job.id,
                'name': job.name,
                'description': job.description,
                'schedule_type': job.schedule_type,
                'is_active': job.is_active,
                'is_custom': job.is_custom,
                'last_run': job.last_run,
                'next_run': job.next_run,
                'created_at': job.created_at,
                'status': 'running' if job.is_active else 'stopped'
            }
            job_list.append(job_data)

        return job_list


async def get_job_statistics() -> Dict[str, Any]:
    """Get job statistics."""
    async with get_async_session() as session:
        total_jobs = await session.execute(select(func.count(Job.id)))
        active_jobs = await session.execute(
            select(func.count(Job.id)).where(Job.is_active == True)
        )
        custom_jobs = await session.execute(
            select(func.count(Job.id)).where(Job.is_custom == True)
        )

        return {
            'total': total_jobs.scalar() or 0,
            'active': active_jobs.scalar() or 0,
            'inactive': (total_jobs.scalar() or 0) - (active_jobs.scalar() or 0),
            'custom': custom_jobs.scalar() or 0,
            'system': (total_jobs.scalar() or 0) - (custom_jobs.scalar() or 0)
        }


async def get_scheduler_status() -> Dict[str, Any]:
    """Get current scheduler status."""
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
        'uptime': str(datetime.now() - datetime.now().replace(hour=0, minute=0, second=0))
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
