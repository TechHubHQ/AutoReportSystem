"""
Enhanced Job Scheduler for AutomateReportSystem with IST Support

Provides better job management capabilities including job cancellation,
status tracking, and rescheduling using IST timezone.
"""

import asyncio
import heapq
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Callable, Awaitable, Optional, Tuple, Dict, Any
from app.core.interface.job_interface import JobInterface
from app.core.utils.timezone_utils import (
    IST, UTC, now_ist, now_utc, ist_to_utc, utc_to_ist,
    seconds_until_ist_time, format_ist_time_display
)


@dataclass
class ScheduledJob:
    """Enhanced scheduled job with better tracking capabilities"""

    def __init__(
        self,
        job_id: str,
        run_at: float,
        coro: Callable[..., Awaitable],
        args: Tuple,
        kwargs: dict,
        repeat: Optional[float] = None,
        day_of_week: Optional[int] = None,
        hour: Optional[int] = None,
        minute: Optional[int] = None,
        next_run: Optional[Callable[[], float]] = None,
        job_name: str = "",
        db_job_id: Optional[int] = None
    ):
        self.job_id = job_id
        self.run_at = run_at
        self.coro = coro
        self.args = args
        self.kwargs = kwargs
        self.repeat = repeat
        self.day_of_week = day_of_week
        self.hour = hour
        self.minute = minute
        self.custom_next_run = next_run
        self.job_name = job_name
        self.db_job_id = db_job_id
        self.created_at = now_ist()
        self.last_run = None
        self.run_count = 0
        self.error_count = 0
        self.last_error = None

    def __lt__(self, other):
        return self.run_at < other.run_at


class JobScheduler:
    """Enhanced job scheduler with better management capabilities and IST support"""

    def __init__(self):
        self._jobs = []
        self._job_lookup = {}  # job_id -> job mapping
        self._lock = asyncio.Lock()
        self._running = False
        self._task = None

    async def start(self):
        """Start the scheduler"""
        if not self._running:
            self._running = True
            self._task = asyncio.create_task(self._run())
            print("✅ Enhanced Job Scheduler started (IST timezone)")

    async def stop(self):
        """Stop the scheduler"""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        print("🛑 Enhanced Job Scheduler stopped")

    def _seconds_until(self, day_of_week: int, hour: int, minute: int) -> float:
        """Returns seconds until next (day_of_week, hour, minute) in IST."""
        return seconds_until_ist_time(day_of_week, hour, minute)

    async def schedule_task(
        self,
        coro: Callable[..., Awaitable],
        delay: float = 0,
        args: Tuple = (),
        kwargs: dict = {},
        repeat: Optional[float] = None,
        day_of_week: Optional[int] = None,
        hour: Optional[int] = None,
        minute: Optional[int] = None,
        next_run: Optional[Callable[[], float]] = None,
        job_name: str = "",
        db_job_id: Optional[int] = None
    ) -> str:
        """Schedule a task and return job ID for management"""

        if day_of_week is not None and hour is not None and minute is not None:
            delay = self._seconds_until(day_of_week, hour, minute)
            repeat = 7 * 86400  # Weekly repeat
        elif next_run:
            delay = next_run() - time.time()

        run_at = time.monotonic() + delay
        job_id = str(uuid.uuid4())

        job = ScheduledJob(
            job_id=job_id,
            run_at=run_at,
            coro=coro,
            args=args,
            kwargs=kwargs,
            repeat=repeat,
            day_of_week=day_of_week,
            hour=hour,
            minute=minute,
            next_run=next_run,
            job_name=job_name,
            db_job_id=db_job_id
        )

        async with self._lock:
            heapq.heappush(self._jobs, job)
            self._job_lookup[job_id] = job

        await self.start()

        # Calculate IST time for display
        ist_run_time = now_ist() + timedelta(seconds=delay)
        print(
            f"📅 Scheduled job '{job_name}' (ID: {job_id[:8]}...) to run at {format_ist_time_display(ist_run_time)}")
        return job_id

    async def cancel_job(self, job_id: str) -> bool:
        """Cancel a scheduled job by ID"""
        async with self._lock:
            if job_id in self._job_lookup:
                job = self._job_lookup[job_id]

                # Remove from lookup
                del self._job_lookup[job_id]

                # Mark as cancelled (we can't easily remove from heap, so we mark it)
                job.cancelled = True

                print(
                    f"❌ Cancelled job '{job.job_name}' (ID: {job_id[:8]}...)")
                return True
            return False

    async def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific job"""
        async with self._lock:
            if job_id in self._job_lookup:
                job = self._job_lookup[job_id]
                return {
                    'job_id': job.job_id,
                    'job_name': job.job_name,
                    'db_job_id': job.db_job_id,
                    'created_at': format_ist_time_display(job.created_at),
                    'next_run': format_ist_time_display(datetime.fromtimestamp(job.run_at, UTC).astimezone(IST)),
                    'last_run': format_ist_time_display(job.last_run) if job.last_run else None,
                    'run_count': job.run_count,
                    'error_count': job.error_count,
                    'last_error': job.last_error,
                    'repeat_interval': job.repeat,
                    'schedule_type': self._get_schedule_type(job)
                }
            return None

    def _get_schedule_type(self, job: ScheduledJob) -> str:
        """Determine schedule type from job configuration"""
        if job.day_of_week is not None:
            return "weekly"
        elif job.custom_next_run:
            return "custom"
        elif job.repeat == 86400:  # 24 hours
            return "daily"
        elif job.repeat:
            return "recurring"
        else:
            return "one-time"

    async def get_all_jobs_status(self) -> Dict[str, Any]:
        """Get status of all scheduled jobs"""
        async with self._lock:
            jobs_status = []
            for job_id, job in self._job_lookup.items():
                if not getattr(job, 'cancelled', False):
                    status = await self.get_job_status(job_id)
                    if status:
                        jobs_status.append(status)

            return {
                'total_jobs': len(jobs_status),
                'scheduler_running': self._running,
                'timezone': 'IST (Indian Standard Time)',
                'current_time': format_ist_time_display(now_ist()),
                'jobs': jobs_status
            }

    async def reschedule_job(self, job_id: str, new_delay: float = None, **kwargs) -> bool:
        """Reschedule an existing job with new parameters"""
        async with self._lock:
            if job_id in self._job_lookup:
                old_job = self._job_lookup[job_id]

                # Cancel old job
                old_job.cancelled = True
                del self._job_lookup[job_id]

                # Create new job with updated parameters
                new_run_at = time.monotonic() + (new_delay or 0)

                # Update job parameters
                for key, value in kwargs.items():
                    if hasattr(old_job, key):
                        setattr(old_job, key, value)

                old_job.run_at = new_run_at
                old_job.job_id = str(uuid.uuid4())  # New ID
                old_job.cancelled = False

                # Re-add to scheduler
                heapq.heappush(self._jobs, old_job)
                self._job_lookup[old_job.job_id] = old_job

                print(
                    f"🔄 Rescheduled job '{old_job.job_name}' (New ID: {old_job.job_id[:8]}...)")
                return True
            return False

    async def _run(self):
        """Main scheduler loop"""
        while self._running:
            now = time.monotonic()
            job_to_execute = None

            async with self._lock:
                # Clean up cancelled jobs from heap top
                while self._jobs and getattr(self._jobs[0], 'cancelled', False):
                    cancelled_job = heapq.heappop(self._jobs)
                    print(
                        f"🗑️ Removed cancelled job from queue: {cancelled_job.job_name}")

                # Check if there's a job ready to run
                if self._jobs and self._jobs[0].run_at <= now:
                    job_to_execute = heapq.heappop(self._jobs)

            if job_to_execute and not getattr(job_to_execute, 'cancelled', False):
                # Execute the job
                asyncio.create_task(self._execute_job(job_to_execute))

                # Reschedule if it's a repeating job
                if job_to_execute.custom_next_run:
                    try:
                        next_run_time = job_to_execute.custom_next_run()
                        job_to_execute.run_at = next_run_time
                        async with self._lock:
                            heapq.heappush(self._jobs, job_to_execute)
                    except Exception as e:
                        print(
                            f"❌ Error calculating next run for {job_to_execute.job_name}: {e}")
                        job_to_execute.error_count += 1
                        job_to_execute.last_error = str(e)

                elif job_to_execute.repeat:
                    job_to_execute.run_at = time.monotonic() + job_to_execute.repeat
                    async with self._lock:
                        heapq.heappush(self._jobs, job_to_execute)
                else:
                    # One-time job, remove from lookup
                    async with self._lock:
                        if job_to_execute.job_id in self._job_lookup:
                            del self._job_lookup[job_to_execute.job_id]
            else:
                # Calculate sleep time
                async with self._lock:
                    if self._jobs:
                        next_job_time = min(
                            job.run_at for job in self._jobs if not getattr(job, 'cancelled', False))
                        sleep_time = max(0.1, next_job_time - time.monotonic())
                    else:
                        sleep_time = 1.0

                await asyncio.sleep(min(sleep_time, 1.0))  # Max 1 second sleep

    async def _execute_job(self, job: ScheduledJob):
        """Execute a scheduled job with error handling and tracking"""
        try:
            print(
                f"🚀 Executing job: {job.job_name} at {format_ist_time_display(now_ist())}")

            # Update job tracking
            job.last_run = now_ist()
            job.run_count += 1

            # Update database if this is a DB job
            if job.db_job_id:
                next_run_time = None
                if job.repeat:
                    next_run_time = now_ist() + timedelta(seconds=job.repeat)
                elif job.custom_next_run:
                    try:
                        next_timestamp = job.custom_next_run()
                        next_run_time = datetime.fromtimestamp(
                            next_timestamp, IST)
                    except:
                        pass

                await JobInterface.update_job_run_times(
                    job.job_name,
                    ist_to_utc(job.last_run),  # Convert to UTC for database
                    ist_to_utc(next_run_time) if next_run_time else None
                )

            # Execute the job
            start_time = time.time()
            print(f"💼 Starting job execution...")
            await job.coro(*job.args, **job.kwargs)
            execution_time = time.time() - start_time

            print(
                f"✅ Job '{job.job_name}' completed successfully in {execution_time:.2f}s at {format_ist_time_display(now_ist())}")

        except Exception as e:
            job.error_count += 1
            job.last_error = str(e)
            print(
                f"❌ Job '{job.job_name}' failed at {format_ist_time_display(now_ist())}: {e}")
            
            # Print full traceback for debugging
            import traceback
            traceback.print_exc()

            # Log error to database if needed
            if job.db_job_id:
                try:
                    await JobInterface.update_job_run_times(
                        job.job_name,
                        ist_to_utc(now_ist()),  # Convert to UTC for database
                        None
                    )
                except:
                    pass

    async def clear(self):
        """Clear all scheduled jobs"""
        async with self._lock:
            self._jobs.clear()
            self._job_lookup.clear()
        print("🗑️ All scheduled jobs cleared")


# Global enhanced scheduler instance
scheduler = JobScheduler()
