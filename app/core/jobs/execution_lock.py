"""
Job Execution Lock System

Provides database-based locking mechanism to prevent concurrent execution of the same job.
Uses PostgreSQL advisory locks for distributed locking across multiple processes.
"""

import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional
from sqlalchemy import select, text, update
from sqlalchemy.exc import SQLAlchemyError

from app.database.db_connector import get_db
from app.database.models import JobExecution
from app.config.logging_config import get_logger

logger = get_logger(__name__)


class JobExecutionLock:
    """Database-based execution lock to prevent concurrent job runs"""
    
    def __init__(self, job_name: str, timeout_minutes: int = 30):
        self.job_name = job_name
        self.timeout_minutes = timeout_minutes
        self.lock_id = hash(job_name) % (2**31)  # Convert to 32-bit integer for PostgreSQL
        self.acquired = False
        
    async def __aenter__(self):
        """Acquire the lock"""
        await self.acquire()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Release the lock"""
        await self.release()
        
    async def acquire(self) -> bool:
        """
        Acquire execution lock for the job.
        Returns True if lock acquired, False if job is already running.
        """
        try:
            db = await get_db()
            
            # First, check if there's already a running execution for this job
            if await self._is_job_currently_running(db):
                logger.info(f"Job {self.job_name} is already running, skipping execution")
                return False
            
            # Try to acquire PostgreSQL advisory lock
            result = await db.execute(
                text("SELECT pg_try_advisory_lock(:lock_id)"),
                {"lock_id": self.lock_id}
            )
            lock_acquired = result.scalar()
            
            if lock_acquired:
                self.acquired = True
                logger.info(f"Acquired execution lock for job {self.job_name} (lock_id: {self.lock_id})")
                return True
            else:
                logger.info(f"Failed to acquire execution lock for job {self.job_name} - another instance is running")
                return False
                
        except Exception as e:
            logger.error(f"Error acquiring execution lock for job {self.job_name}: {e}")
            return False
        finally:
            await db.close()
    
    async def release(self):
        """Release the execution lock"""
        if not self.acquired:
            return
            
        try:
            db = await get_db()
            
            # Release PostgreSQL advisory lock
            await db.execute(
                text("SELECT pg_advisory_unlock(:lock_id)"),
                {"lock_id": self.lock_id}
            )
            
            self.acquired = False
            logger.info(f"Released execution lock for job {self.job_name} (lock_id: {self.lock_id})")
            
        except Exception as e:
            logger.error(f"Error releasing execution lock for job {self.job_name}: {e}")
        finally:
            await db.close()
    
    async def _is_job_currently_running(self, db) -> bool:
        """Check if there's a currently running execution for this job"""
        try:
            # Look for running executions in the last hour (safety margin)
            cutoff_time = datetime.now(timezone.utc) - timedelta(hours=1)
            
            result = await db.execute(
                select(JobExecution)
                .join(JobExecution.job)
                .where(
                    JobExecution.job.has(name=self.job_name),
                    JobExecution.status == "running",
                    JobExecution.started_at >= cutoff_time
                )
            )
            
            running_executions = result.scalars().all()
            
            if running_executions:
                logger.warning(f"Found {len(running_executions)} running executions for job {self.job_name}")
                
                # Clean up stale running executions (older than timeout)
                stale_cutoff = datetime.now(timezone.utc) - timedelta(minutes=self.timeout_minutes)
                for execution in running_executions:
                    if execution.started_at < stale_cutoff:
                        logger.warning(f"Marking stale execution {execution.execution_id} as failed")
                        await db.execute(
                            update(JobExecution)
                            .where(JobExecution.execution_id == execution.execution_id)
                            .values(
                                status="failure",
                                completed_at=datetime.now(timezone.utc),
                                error_message="Execution timed out and was marked as failed"
                            )
                        )
                
                await db.commit()
                
                # Re-check for still running executions
                result = await db.execute(
                    select(JobExecution)
                    .join(JobExecution.job)
                    .where(
                        JobExecution.job.has(name=self.job_name),
                        JobExecution.status == "running",
                        JobExecution.started_at >= stale_cutoff
                    )
                )
                
                current_running = result.scalars().all()
                return len(current_running) > 0
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking running executions for job {self.job_name}: {e}")
            return True  # Err on the side of caution


async def cleanup_stale_locks():
    """Clean up stale advisory locks and running executions"""
    try:
        db = await get_db()
        
        # Mark executions older than 2 hours as failed
        stale_cutoff = datetime.now(timezone.utc) - timedelta(hours=2)
        
        result = await db.execute(
            update(JobExecution)
            .where(
                JobExecution.status == "running",
                JobExecution.started_at < stale_cutoff
            )
            .values(
                status="failure",
                completed_at=datetime.now(timezone.utc),
                error_message="Execution timed out and was automatically marked as failed"
            )
        )
        
        if result.rowcount > 0:
            logger.info(f"Cleaned up {result.rowcount} stale job executions")
            
        await db.commit()
        
    except Exception as e:
        logger.error(f"Error cleaning up stale locks: {e}")
    finally:
        await db.close()


def get_job_lock_id(job_name: str) -> int:
    """Get consistent lock ID for a job name"""
    return hash(job_name) % (2**31)