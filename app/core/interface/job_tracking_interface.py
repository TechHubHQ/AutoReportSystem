"""
Job Tracking Interface

Comprehensive interface for managing job executions, logging, and statistics.
Provides database storage for job execution details, performance metrics, and logs.
"""

import json
import uuid
import psutil
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy import select, update, desc, func, and_
from sqlalchemy.orm import selectinload

from app.database.db_connector import get_db
from app.database.models import Job, JobExecution, JobExecutionLog
from app.config.logging_config import get_logger

logger = get_logger(__name__)


class JobExecutionTracker:
    """Context manager for tracking job execution with detailed logging"""

    def __init__(self, job_name: str, scheduled_time: datetime = None,
                 trigger_type: str = "scheduled", triggered_by: int = None):
        self.job_name = job_name
        self.execution_id = str(uuid.uuid4())
        self.scheduled_time = scheduled_time or datetime.now(timezone.utc)
        self.trigger_type = trigger_type
        self.triggered_by = triggered_by
        self.started_at = None
        self.job_id = None
        self.cpu_start = None
        self.memory_start = None

    async def __aenter__(self):
        """Start tracking job execution"""
        self.started_at = datetime.now(timezone.utc)

        # Get system metrics at start
        try:
            self.cpu_start = psutil.cpu_percent(interval=None)
            self.memory_start = psutil.virtual_memory().percent
        except:
            self.cpu_start = None
            self.memory_start = None

        # Get or create job record
        self.job_id = await self._get_or_create_job()

        # Create execution record
        await self._create_execution_record()

        logger.info(
            f"Started tracking execution {self.execution_id} for job {self.job_name}")
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Complete job execution tracking"""
        completed_at = datetime.now(timezone.utc)
        duration = int((completed_at - self.started_at).total_seconds())

        # Get system metrics at end
        try:
            cpu_end = psutil.cpu_percent(interval=None)
            memory_end = psutil.virtual_memory().percent
        except:
            cpu_end = None
            memory_end = None

        # Determine status
        if exc_type is None:
            status = "success"
            error_message = None
            error_traceback = None
        else:
            status = "failure"
            error_message = str(exc_val) if exc_val else "Unknown error"
            error_traceback = str(exc_tb) if exc_tb else None

        # Update execution record
        await self._complete_execution_record(
            completed_at, duration, status, error_message, error_traceback,
            cpu_end, memory_end
        )

        # Update job statistics
        await self._update_job_statistics(status, duration, completed_at, error_message)

        logger.info(
            f"Completed tracking execution {self.execution_id}: {status} in {duration}s")

    async def log(self, level: str, message: str, source: str = None):
        """Add a log entry for this execution"""
        await add_execution_log(self.execution_id, level, message, source)

    async def set_result_data(self, result_data: Dict[str, Any]):
        """Set result data for this execution"""
        try:
            db = await get_db()
            query = update(JobExecution).where(
                JobExecution.execution_id == self.execution_id
            ).values(result_data=json.dumps(result_data))
            await db.execute(query)
            await db.commit()
        except Exception as e:
            logger.error(
                f"Error setting result data for execution {self.execution_id}: {e}")
        finally:
            await db.close()

    async def _get_or_create_job(self) -> int:
        """Get or create job record"""
        try:
            db = await get_db()

            # Try to find existing job
            result = await db.execute(select(Job).where(Job.name == self.job_name))
            job = result.scalar_one_or_none()

            if not job:
                # Create new job record
                job = Job(
                    name=self.job_name,
                    description=f"Auto-created job for {self.job_name}",
                    function_name=self.job_name,
                    module_path="auto_discovered",
                    schedule_type="auto",
                    is_custom=False,
                    status="active"
                )
                db.add(job)
                await db.commit()
                await db.refresh(job)
                logger.info(f"Created new job record for {self.job_name}")

            return job.id
        except Exception as e:
            logger.error(f"Error getting/creating job record: {e}")
            raise
        finally:
            await db.close()

    async def _create_execution_record(self):
        """Create initial execution record"""
        try:
            db = await get_db()
            execution = JobExecution(
                job_id=self.job_id,
                execution_id=self.execution_id,
                scheduled_time=self.scheduled_time,
                started_at=self.started_at,
                status="running",
                trigger_type=self.trigger_type,
                triggered_by=self.triggered_by,
                cpu_usage_start=self.cpu_start,
                memory_usage_start=self.memory_start
            )
            db.add(execution)
            await db.commit()
        except Exception as e:
            logger.error(f"Error creating execution record: {e}")
            raise
        finally:
            await db.close()

    async def _complete_execution_record(self, completed_at: datetime, duration: int,
                                         status: str, error_message: str, error_traceback: str,
                                         cpu_end: int, memory_end: int):
        """Complete execution record with final details"""
        try:
            db = await get_db()
            query = update(JobExecution).where(
                JobExecution.execution_id == self.execution_id
            ).values(
                completed_at=completed_at,
                duration=duration,
                status=status,
                error_message=error_message,
                error_traceback=error_traceback,
                cpu_usage_end=cpu_end,
                memory_usage_end=memory_end
            )
            await db.execute(query)
            await db.commit()
        except Exception as e:
            logger.error(f"Error completing execution record: {e}")
        finally:
            await db.close()

    async def _update_job_statistics(self, status: str, duration: int,
                                     completed_at: datetime, error_message: str):
        """Update job-level statistics"""
        try:
            db = await get_db()

            # Get current job stats
            result = await db.execute(select(Job).where(Job.id == self.job_id))
            job = result.scalar_one()

            # Update counters
            job.total_runs += 1
            if status == "success":
                job.successful_runs += 1
                job.last_success = completed_at
            else:
                job.failed_runs += 1
                job.last_failure = completed_at
                job.last_error_message = error_message

            # Update last run and average duration
            job.last_run = completed_at
            if job.average_duration is None:
                job.average_duration = duration
            else:
                # Calculate rolling average
                job.average_duration = int(
                    (job.average_duration + duration) / 2)

            # Update job status based on recent performance
            if job.failed_runs > 0 and job.successful_runs == 0:
                job.status = "error"
            elif status == "success":
                job.status = "active"

            await db.commit()
        except Exception as e:
            logger.error(f"Error updating job statistics: {e}")
        finally:
            await db.close()


async def get_job_execution_history(job_name: str = None, limit: int = 50) -> List[Dict[str, Any]]:
    """Get job execution history with optional filtering"""
    try:
        db = await get_db()

        query = select(JobExecution).options(selectinload(JobExecution.job))

        if job_name:
            query = query.join(Job).where(Job.name == job_name)

        query = query.order_by(desc(JobExecution.started_at)).limit(limit)

        result = await db.execute(query)
        executions = result.scalars().all()

        history = []
        for execution in executions:
            history.append({
                'execution_id': execution.execution_id,
                'job_name': execution.job.name,
                'scheduled_time': execution.scheduled_time,
                'started_at': execution.started_at,
                'completed_at': execution.completed_at,
                'duration': execution.duration,
                'status': execution.status,
                'trigger_type': execution.trigger_type,
                'error_message': execution.error_message,
                'cpu_usage_start': execution.cpu_usage_start,
                'cpu_usage_end': execution.cpu_usage_end,
                'memory_usage_start': execution.memory_usage_start,
                'memory_usage_end': execution.memory_usage_end,
                'result_data': json.loads(execution.result_data) if execution.result_data else None
            })

        return history
    except Exception as e:
        logger.error(f"Error getting job execution history: {e}")
        return []
    finally:
        await db.close()


async def get_job_statistics(job_name: str = None) -> Dict[str, Any]:
    """Get comprehensive job statistics"""
    try:
        db = await get_db()

        if job_name:
            # Get stats for specific job
            result = await db.execute(
                select(Job).where(Job.name == job_name)
            )
            job = result.scalar_one_or_none()

            if not job:
                return {}

            return {
                'job_name': job.name,
                'total_runs': job.total_runs,
                'successful_runs': job.successful_runs,
                'failed_runs': job.failed_runs,
                'success_rate': (job.successful_runs / job.total_runs * 100) if job.total_runs > 0 else 0,
                'average_duration': job.average_duration,
                'last_run': job.last_run,
                'last_success': job.last_success,
                'last_failure': job.last_failure,
                'last_error_message': job.last_error_message,
                'status': job.status,
                'next_run': job.next_run
            }
        else:
            # Get overall statistics
            result = await db.execute(select(Job))
            jobs = result.scalars().all()

            total_jobs = len(jobs)
            active_jobs = len([j for j in jobs if j.status == "active"])
            error_jobs = len([j for j in jobs if j.status == "error"])
            total_executions = sum(j.total_runs for j in jobs)
            total_successes = sum(j.successful_runs for j in jobs)
            total_failures = sum(j.failed_runs for j in jobs)

            return {
                'total_jobs': total_jobs,
                'active_jobs': active_jobs,
                'error_jobs': error_jobs,
                'total_executions': total_executions,
                'total_successes': total_successes,
                'total_failures': total_failures,
                'overall_success_rate': (total_successes / total_executions * 100) if total_executions > 0 else 0,
                'jobs': [
                    {
                        'name': job.name,
                        'status': job.status,
                        'total_runs': job.total_runs,
                        'success_rate': (job.successful_runs / job.total_runs * 100) if job.total_runs > 0 else 0,
                        'last_run': job.last_run
                    }
                    for job in jobs
                ]
            }
    except Exception as e:
        logger.error(f"Error getting job statistics: {e}")
        return {}
    finally:
        await db.close()


async def get_execution_logs(execution_id: str) -> List[Dict[str, Any]]:
    """Get logs for a specific execution"""
    try:
        db = await get_db()

        result = await db.execute(
            select(JobExecutionLog)
            .where(JobExecutionLog.execution_id == execution_id)
            .order_by(JobExecutionLog.timestamp)
        )
        logs = result.scalars().all()

        return [
            {
                'log_level': log.log_level,
                'message': log.message,
                'timestamp': log.timestamp,
                'source': log.source
            }
            for log in logs
        ]
    except Exception as e:
        logger.error(f"Error getting execution logs: {e}")
        return []
    finally:
        await db.close()


async def add_execution_log(execution_id: str, level: str, message: str, source: str = None):
    """Add a log entry for an execution"""
    try:
        db = await get_db()

        log_entry = JobExecutionLog(
            execution_id=execution_id,
            log_level=level.upper(),
            message=message,
            source=source
        )
        db.add(log_entry)
        await db.commit()
    except Exception as e:
        logger.error(f"Error adding execution log: {e}")
    finally:
        await db.close()


async def get_job_performance_metrics(days: int = 30) -> Dict[str, Any]:
    """Get job performance metrics for the last N days"""
    try:
        db = await get_db()

        # Get executions from last N days
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)

        result = await db.execute(
            select(JobExecution)
            .options(selectinload(JobExecution.job))
            .where(JobExecution.started_at >= cutoff_date)
            .order_by(desc(JobExecution.started_at))
        )
        executions = result.scalars().all()

        # Calculate metrics
        total_executions = len(executions)
        successful_executions = len(
            [e for e in executions if e.status == "success"])
        failed_executions = len(
            [e for e in executions if e.status == "failure"])

        # Average duration
        completed_executions = [
            e for e in executions if e.duration is not None]
        avg_duration = sum(e.duration for e in completed_executions) / \
            len(completed_executions) if completed_executions else 0

        # Performance by job
        job_metrics = {}
        for execution in executions:
            job_name = execution.job.name
            if job_name not in job_metrics:
                job_metrics[job_name] = {
                    'total': 0,
                    'successful': 0,
                    'failed': 0,
                    'avg_duration': 0,
                    'durations': []
                }

            job_metrics[job_name]['total'] += 1
            if execution.status == "success":
                job_metrics[job_name]['successful'] += 1
            elif execution.status == "failure":
                job_metrics[job_name]['failed'] += 1

            if execution.duration:
                job_metrics[job_name]['durations'].append(execution.duration)

        # Calculate average durations
        for job_name, metrics in job_metrics.items():
            if metrics['durations']:
                metrics['avg_duration'] = sum(
                    metrics['durations']) / len(metrics['durations'])
                metrics['success_rate'] = (
                    metrics['successful'] / metrics['total']) * 100
            del metrics['durations']  # Remove raw durations from output

        return {
            'period_days': days,
            'total_executions': total_executions,
            'successful_executions': successful_executions,
            'failed_executions': failed_executions,
            'success_rate': (successful_executions / total_executions * 100) if total_executions > 0 else 0,
            'average_duration': avg_duration,
            'job_metrics': job_metrics
        }
    except Exception as e:
        logger.error(f"Error getting job performance metrics: {e}")
        return {}
    finally:
        await db.close()


async def cleanup_old_executions(days_to_keep: int = 90):
    """Clean up old execution records to prevent database bloat"""
    try:
        db = await get_db()

        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_to_keep)

        # Delete old execution logs first (foreign key constraint)
        log_result = await db.execute(
            select(JobExecutionLog.execution_id)
            .join(JobExecution)
            .where(JobExecution.started_at < cutoff_date)
        )
        old_execution_ids = [row[0] for row in log_result.fetchall()]

        if old_execution_ids:
            await db.execute(
                JobExecutionLog.__table__.delete()
                .where(JobExecutionLog.execution_id.in_(old_execution_ids))
            )

        # Delete old executions
        execution_result = await db.execute(
            JobExecution.__table__.delete()
            .where(JobExecution.started_at < cutoff_date)
        )

        await db.commit()

        deleted_count = execution_result.rowcount
        logger.info(
            f"Cleaned up {deleted_count} old job execution records older than {days_to_keep} days")

        return deleted_count
    except Exception as e:
        logger.error(f"Error cleaning up old executions: {e}")
        return 0
    finally:
        await db.close()
