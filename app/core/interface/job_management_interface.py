"""
Job Management Interface

Comprehensive interface for managing jobs, their configurations, and execution history.
Provides CRUD operations for jobs and integration with the job tracking system.
"""

import json
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy import select, update, delete, desc, func, and_, or_
from sqlalchemy.orm import selectinload

from app.database.db_connector import get_db
from app.database.models import Job, JobExecution, JobExecutionLog
from app.config.logging_config import get_logger

logger = get_logger(__name__)


async def create_job(
    name: str,
    description: str = None,
    function_name: str = None,
    module_path: str = None,
    schedule_type: str = "custom",
    schedule_config: Dict[str, Any] = None,
    code: str = None,
    is_custom: bool = True,
    is_active: bool = True
) -> Dict[str, Any]:
    """Create a new job"""
    try:
        db = await get_db()

        # Check if job with same name exists
        existing = await db.execute(select(Job).where(Job.name == name))
        if existing.scalar_one_or_none():
            raise ValueError(f"Job with name '{name}' already exists")

        job = Job(
            name=name,
            description=description,
            function_name=function_name or name,
            module_path=module_path or "custom",
            schedule_type=schedule_type,
            schedule_config=json.dumps(
                schedule_config) if schedule_config else None,
            code=code,
            is_custom=is_custom,
            is_active=is_active,
            status="active" if is_active else "disabled"
        )

        db.add(job)
        await db.commit()
        await db.refresh(job)

        logger.info(f"Created new job: {name}")

        return {
            'id': job.id,
            'name': job.name,
            'description': job.description,
            'schedule_type': job.schedule_type,
            'is_active': job.is_active,
            'status': job.status,
            'created_at': job.created_at
        }
    except Exception as e:
        logger.error(f"Error creating job: {e}")
        raise
    finally:
        await db.close()


async def get_job(job_id: int = None, job_name: str = None) -> Optional[Dict[str, Any]]:
    """Get a specific job by ID or name"""
    try:
        db = await get_db()

        if job_id:
            query = select(Job).where(Job.id == job_id)
        elif job_name:
            query = select(Job).where(Job.name == job_name)
        else:
            raise ValueError("Either job_id or job_name must be provided")

        result = await db.execute(query)
        job = result.scalar_one_or_none()

        if not job:
            return None

        return {
            'id': job.id,
            'name': job.name,
            'description': job.description,
            'function_name': job.function_name,
            'module_path': job.module_path,
            'schedule_type': job.schedule_type,
            'schedule_config': json.loads(job.schedule_config) if job.schedule_config else None,
            'code': job.code,
            'is_active': job.is_active,
            'is_custom': job.is_custom,
            'status': job.status,
            'last_run': job.last_run,
            'next_run': job.next_run,
            'total_runs': job.total_runs,
            'successful_runs': job.successful_runs,
            'failed_runs': job.failed_runs,
            'average_duration': job.average_duration,
            'last_success': job.last_success,
            'last_failure': job.last_failure,
            'last_error_message': job.last_error_message,
            'success_rate': (job.successful_runs / job.total_runs * 100) if job.total_runs > 0 else 0,
            'created_at': job.created_at,
            'updated_at': job.updated_at
        }
    except Exception as e:
        logger.error(f"Error getting job: {e}")
        return None
    finally:
        await db.close()


async def get_all_jobs(include_inactive: bool = True) -> List[Dict[str, Any]]:
    """Get all jobs with their statistics"""
    try:
        db = await get_db()

        query = select(Job)
        if not include_inactive:
            query = query.where(Job.is_active == True)

        query = query.order_by(Job.name)

        result = await db.execute(query)
        jobs = result.scalars().all()

        job_list = []
        for job in jobs:
            job_list.append({
                'id': job.id,
                'name': job.name,
                'description': job.description,
                'schedule_type': job.schedule_type,
                'is_active': job.is_active,
                'is_custom': job.is_custom,
                'status': job.status,
                'last_run': job.last_run,
                'next_run': job.next_run,
                'total_runs': job.total_runs,
                'successful_runs': job.successful_runs,
                'failed_runs': job.failed_runs,
                'average_duration': job.average_duration,
                'success_rate': (job.successful_runs / job.total_runs * 100) if job.total_runs > 0 else 0,
                'last_success': job.last_success,
                'last_failure': job.last_failure,
                'created_at': job.created_at,
                'updated_at': job.updated_at
            })

        return job_list
    except Exception as e:
        logger.error(f"Error getting all jobs: {e}")
        return []
    finally:
        await db.close()


async def update_job(
    job_id: int,
    name: str = None,
    description: str = None,
    schedule_type: str = None,
    schedule_config: Dict[str, Any] = None,
    code: str = None,
    is_active: bool = None,
    next_run: datetime = None
) -> bool:
    """Update an existing job"""
    try:
        db = await get_db()

        # Build update dictionary
        update_data = {}
        if name is not None:
            # Check if new name conflicts with existing job
            existing = await db.execute(
                select(Job).where(and_(Job.name == name, Job.id != job_id))
            )
            if existing.scalar_one_or_none():
                raise ValueError(f"Job with name '{name}' already exists")
            update_data['name'] = name

        if description is not None:
            update_data['description'] = description
        if schedule_type is not None:
            update_data['schedule_type'] = schedule_type
        if schedule_config is not None:
            update_data['schedule_config'] = json.dumps(schedule_config)
        if code is not None:
            update_data['code'] = code
        if is_active is not None:
            update_data['is_active'] = is_active
            update_data['status'] = "active" if is_active else "disabled"
        if next_run is not None:
            update_data['next_run'] = next_run

        if not update_data:
            return True  # Nothing to update

        update_data['updated_at'] = datetime.now(timezone.utc)

        query = update(Job).where(Job.id == job_id).values(**update_data)
        result = await db.execute(query)
        await db.commit()

        if result.rowcount == 0:
            logger.warning(f"No job found with ID {job_id}")
            return False

        logger.info(f"Updated job ID {job_id}")
        return True
    except Exception as e:
        logger.error(f"Error updating job: {e}")
        raise
    finally:
        await db.close()


async def delete_job(job_id: int) -> bool:
    """Delete a job and all its execution history"""
    try:
        db = await get_db()

        # Check if job exists
        job_result = await db.execute(select(Job).where(Job.id == job_id))
        job = job_result.scalar_one_or_none()

        if not job:
            logger.warning(f"No job found with ID {job_id}")
            return False

        # Delete the job (cascading will handle executions and logs)
        await db.execute(delete(Job).where(Job.id == job_id))
        await db.commit()

        logger.info(f"Deleted job: {job.name} (ID: {job_id})")
        return True
    except Exception as e:
        logger.error(f"Error deleting job: {e}")
        raise
    finally:
        await db.close()


async def get_job_execution_details(execution_id: str) -> Optional[Dict[str, Any]]:
    """Get detailed information about a specific job execution"""
    try:
        db = await get_db()

        result = await db.execute(
            select(JobExecution)
            .options(selectinload(JobExecution.job))
            .where(JobExecution.execution_id == execution_id)
        )
        execution = result.scalar_one_or_none()

        if not execution:
            return None

        # Get logs for this execution
        logs_result = await db.execute(
            select(JobExecutionLog)
            .where(JobExecutionLog.execution_id == execution_id)
            .order_by(JobExecutionLog.timestamp)
        )
        logs = logs_result.scalars().all()

        return {
            'execution_id': execution.execution_id,
            'job_id': execution.job_id,
            'job_name': execution.job.name,
            'scheduled_time': execution.scheduled_time,
            'started_at': execution.started_at,
            'completed_at': execution.completed_at,
            'duration': execution.duration,
            'status': execution.status,
            'result_data': json.loads(execution.result_data) if execution.result_data else None,
            'error_message': execution.error_message,
            'error_traceback': execution.error_traceback,
            'trigger_type': execution.trigger_type,
            'retry_count': execution.retry_count,
            'cpu_usage_start': execution.cpu_usage_start,
            'cpu_usage_end': execution.cpu_usage_end,
            'memory_usage_start': execution.memory_usage_start,
            'memory_usage_end': execution.memory_usage_end,
            'logs': [
                {
                    'level': log.log_level,
                    'message': log.message,
                    'timestamp': log.timestamp,
                    'source': log.source
                }
                for log in logs
            ]
        }
    except Exception as e:
        logger.error(f"Error getting job execution details: {e}")
        return None
    finally:
        await db.close()


async def get_job_executions(
    job_id: int = None,
    job_name: str = None,
    status: str = None,
    limit: int = 50,
    offset: int = 0
) -> List[Dict[str, Any]]:
    """Get job executions with filtering and pagination"""
    try:
        db = await get_db()

        query = select(JobExecution).options(selectinload(JobExecution.job))

        if job_id:
            query = query.where(JobExecution.job_id == job_id)
        elif job_name:
            query = query.join(Job).where(Job.name == job_name)

        if status:
            query = query.where(JobExecution.status == status)

        query = query.order_by(desc(JobExecution.started_at)
                               ).offset(offset).limit(limit)

        result = await db.execute(query)
        executions = result.scalars().all()

        execution_list = []
        for execution in executions:
            execution_list.append({
                'execution_id': execution.execution_id,
                'job_id': execution.job_id,
                'job_name': execution.job.name,
                'scheduled_time': execution.scheduled_time,
                'started_at': execution.started_at,
                'completed_at': execution.completed_at,
                'duration': execution.duration,
                'status': execution.status,
                'trigger_type': execution.trigger_type,
                'retry_count': execution.retry_count,
                'error_message': execution.error_message,
                'cpu_usage_start': execution.cpu_usage_start,
                'cpu_usage_end': execution.cpu_usage_end,
                'memory_usage_start': execution.memory_usage_start,
                'memory_usage_end': execution.memory_usage_end
            })

        return execution_list
    except Exception as e:
        logger.error(f"Error getting job executions: {e}")
        return []
    finally:
        await db.close()


async def get_job_dashboard_summary() -> Dict[str, Any]:
    """Get comprehensive dashboard summary for jobs"""
    try:
        db = await get_db()

        # Get all jobs
        jobs_result = await db.execute(select(Job))
        jobs = jobs_result.scalars().all()

        # Calculate summary statistics
        total_jobs = len(jobs)
        active_jobs = len([j for j in jobs if j.is_active])
        custom_jobs = len([j for j in jobs if j.is_custom])

        # Job status breakdown
        status_counts = {}
        for job in jobs:
            status_counts[job.status] = status_counts.get(job.status, 0) + 1

        # Recent executions (last 24 hours)
        yesterday = datetime.now(timezone.utc) - timedelta(days=1)
        recent_executions_result = await db.execute(
            select(JobExecution)
            .where(JobExecution.started_at >= yesterday)
            .order_by(desc(JobExecution.started_at))
        )
        recent_executions = recent_executions_result.scalars().all()

        # Execution statistics
        total_executions_today = len(recent_executions)
        successful_today = len(
            [e for e in recent_executions if e.status == "success"])
        failed_today = len(
            [e for e in recent_executions if e.status == "failure"])

        # Overall statistics
        total_all_runs = sum(job.total_runs for job in jobs)
        total_all_successes = sum(job.successful_runs for job in jobs)
        total_all_failures = sum(job.failed_runs for job in jobs)

        # Jobs with issues
        error_jobs = [j for j in jobs if j.status == "error"]
        jobs_with_recent_failures = [
            j for j in jobs
            if j.last_failure and j.last_failure >= yesterday
        ]

        # Performance metrics
        avg_durations = [
            j.average_duration for j in jobs if j.average_duration]
        overall_avg_duration = sum(avg_durations) / \
            len(avg_durations) if avg_durations else 0

        return {
            'summary': {
                'total_jobs': total_jobs,
                'active_jobs': active_jobs,
                'custom_jobs': custom_jobs,
                'error_jobs': len(error_jobs),
                'jobs_with_recent_failures': len(jobs_with_recent_failures)
            },
            'status_breakdown': status_counts,
            'execution_stats': {
                'total_executions_today': total_executions_today,
                'successful_today': successful_today,
                'failed_today': failed_today,
                'success_rate_today': (successful_today / total_executions_today * 100) if total_executions_today > 0 else 0,
                'total_all_runs': total_all_runs,
                'total_all_successes': total_all_successes,
                'total_all_failures': total_all_failures,
                'overall_success_rate': (total_all_successes / total_all_runs * 100) if total_all_runs > 0 else 0
            },
            'performance': {
                'overall_avg_duration': overall_avg_duration,
                'jobs_with_performance_data': len(avg_durations)
            },
            'recent_executions': [
                {
                    'execution_id': e.execution_id,
                    'job_id': e.job_id,
                    'started_at': e.started_at,
                    'duration': e.duration,
                    'status': e.status
                }
                for e in recent_executions[:10]  # Last 10 executions
            ],
            'problem_jobs': [
                {
                    'id': j.id,
                    'name': j.name,
                    'status': j.status,
                    'last_error': j.last_error_message,
                    'last_failure': j.last_failure
                }
                for j in error_jobs + jobs_with_recent_failures
            ]
        }
    except Exception as e:
        logger.error(f"Error getting job dashboard summary: {e}")
        return {}
    finally:
        await db.close()


async def trigger_manual_job_execution(job_name: str, triggered_by: int = None) -> str:
    """Trigger a manual execution of a job"""
    try:
        # This would integrate with the scheduler to trigger a job manually
        # For now, we'll create a placeholder execution record
        from app.core.interface.job_tracking_interface import JobExecutionTracker

        # Create a manual execution tracker
        tracker = JobExecutionTracker(
            job_name=job_name,
            trigger_type="manual",
            triggered_by=triggered_by
        )

        # Return the execution ID for tracking
        return tracker.execution_id
    except Exception as e:
        logger.error(f"Error triggering manual job execution: {e}")
        raise


async def get_job_performance_trends(job_name: str = None, days: int = 30) -> Dict[str, Any]:
    """Get performance trends for jobs over time"""
    try:
        db = await get_db()

        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)

        query = select(JobExecution).options(selectinload(JobExecution.job))
        query = query.where(JobExecution.started_at >= cutoff_date)

        if job_name:
            query = query.join(Job).where(Job.name == job_name)

        query = query.order_by(JobExecution.started_at)

        result = await db.execute(query)
        executions = result.scalars().all()

        # Group by date
        daily_stats = {}
        for execution in executions:
            date_key = execution.started_at.date().isoformat()

            if date_key not in daily_stats:
                daily_stats[date_key] = {
                    'date': date_key,
                    'total': 0,
                    'successful': 0,
                    'failed': 0,
                    'avg_duration': 0,
                    'durations': []
                }

            daily_stats[date_key]['total'] += 1
            if execution.status == "success":
                daily_stats[date_key]['successful'] += 1
            elif execution.status == "failure":
                daily_stats[date_key]['failed'] += 1

            if execution.duration:
                daily_stats[date_key]['durations'].append(execution.duration)

        # Calculate averages
        for stats in daily_stats.values():
            if stats['durations']:
                stats['avg_duration'] = sum(
                    stats['durations']) / len(stats['durations'])
            del stats['durations']  # Remove raw data

        return {
            'period_days': days,
            'job_name': job_name,
            'daily_trends': list(daily_stats.values()),
            'total_executions': len(executions),
            'overall_success_rate': (
                len([e for e in executions if e.status == "success"]) /
                len(executions) * 100
            ) if executions else 0
        }
    except Exception as e:
        logger.error(f"Error getting job performance trends: {e}")
        return {}
    finally:
        await db.close()
