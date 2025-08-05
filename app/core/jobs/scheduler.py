from apscheduler.schedulers.asyncio import AsyncIOScheduler


class Scheduler:
    _instance = None
    _scheduler = None
    _started = False
    _job_queue = []

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(Scheduler, cls).__new__(cls)
            cls._scheduler = AsyncIOScheduler()
            cls._started = False
            cls._job_queue = []
        return cls._instance

    def add_job(self, func, trigger, **kwargs):
        """
        Add a job to the scheduler and queue.
        :param func: The function to schedule.
        :param trigger: The trigger type (e.g., 'interval', 'cron', etc.).
        :param kwargs: Additional arguments for the trigger.
        """
        # Add job to the queue (store job details, not the job object itself)
        job_info = {
            "func": func,
            "trigger": trigger,
            "kwargs": kwargs
        }
        self._job_queue.append(job_info)
        return self._scheduler.add_job(func, trigger, **kwargs)

    def remove_job(self, job_id):
        """
        Remove a job from the scheduler by its ID and from the queue.
        """
        self._scheduler.remove_job(job_id)
        self._job_queue = [
            job for job in self._job_queue
            if job.get("kwargs", {}).get("id") != job_id
        ]

    def start(self):
        """
        Start the scheduler if not already started.
        """
        if not self._started:
            self._scheduler.start()
            self._started = True

    def shutdown(self, wait=True):
        """
        Shutdown the scheduler.
        """
        if self._started:
            self._scheduler.shutdown(wait=wait)
            self._started = False

    def get_jobs(self):
        """
        Get all scheduled jobs.
        """
        return self._scheduler.get_jobs()

    def get_queued_jobs(self):
        """
        Get all jobs currently in the queue (not necessarily scheduled).
        """
        return self._job_queue


scheduler = Scheduler()
