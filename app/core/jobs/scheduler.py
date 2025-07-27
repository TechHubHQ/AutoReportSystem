import asyncio
import heapq
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Callable, Awaitable, Optional, Tuple


@dataclass
class ScheduledJob:
    def __init__(
        self,
        run_at: float,
        coro: Callable[..., Awaitable],
        args: Tuple,
        kwargs: dict,
        repeat: Optional[float] = None,
        day_of_week: Optional[int] = None,
        hour: Optional[int] = None,
        minute: Optional[int] = None,
        next_run: Optional[Callable[[], float]] = None,
    ):
        self.run_at = run_at
        self.coro = coro
        self.args = args
        self.kwargs = kwargs
        self.repeat = repeat
        self.day_of_week = day_of_week
        self.hour = hour
        self.minute = minute
        self.custom_next_run = next_run

    def __lt__(self, other):
        return self.run_at < other.run_at


class JobScheduler:
    def __init__(self):
        self._jobs = []
        self._lock = asyncio.Lock()
        self._running = False
        self._task = None

    async def start(self):
        if not self._running:
            self._running = True
            self._task = asyncio.create_task(self._run())

    async def stop(self):
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

    def _seconds_until(self, day_of_week: int, hour: int, minute: int) -> float:
        """Returns seconds until next (day_of_week, hour, minute) in UTC."""
        now = datetime.now(timezone.utc)
        today = now.weekday()
        target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)

        days_ahead = (day_of_week - today + 7) % 7
        if days_ahead == 0 and now >= target:
            days_ahead = 7

        next_run = target + timedelta(days=days_ahead)
        return (next_run - now).total_seconds()

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
        next_run: Optional[Callable[[], float]] = None
    ):
        if day_of_week is not None and hour is not None and minute is not None:
            delay = self._seconds_until(day_of_week, hour, minute)
            repeat = 7 * 86400
        elif next_run:
            delay = next_run() - time.time()

        run_at = time.monotonic() + delay
        job = ScheduledJob(run_at, coro, args, kwargs, repeat,
                        day_of_week, hour, minute, next_run)
        async with self._lock:
            heapq.heappush(self._jobs, job)
        await self.start()
        return job


    async def _run(self):
        while self._running:
            now = time.monotonic()
            async with self._lock:
                if self._jobs and self._jobs[0].run_at <= now:
                    job = heapq.heappop(self._jobs)
                else:
                    job = None
            if job:
                asyncio.create_task(self._execute_job(job))
                if job.next_run:
                    job.run_at = job.next_run()
                elif job.repeat:
                    job.run_at = time.monotonic() + job.repeat
                async with self._lock:
                    heapq.heappush(self._jobs, job)

            else:
                async with self._lock:
                    sleep_time = (
                        max(0, self._jobs[0].run_at - time.monotonic())
                        if self._jobs else 0.5
                    )
                await asyncio.sleep(sleep_time)

    async def _execute_job(self, job: ScheduledJob):
        try:
            await job.coro(*job.args, **job.kwargs)
        except Exception as e:
            print(f"Scheduled job error: {e}")

    async def clear(self):
        async with self._lock:
            self._jobs.clear()


scheduler = JobScheduler()
