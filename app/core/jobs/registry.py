import inspect
import importlib
from typing import Dict, Callable, Any
from functools import wraps
from sqlalchemy import select
from app.database.db_connector import get_db
from app.database.models import Job


class JobRegistry:
    _jobs: Dict[str, Dict[str, Any]] = {}

    @classmethod
    def register(cls, name: str, description: str = "", schedule_type: str = "custom"):
        """Decorator to register a job function"""
        def decorator(func: Callable):
            cls._jobs[name] = {
                "function": func,
                "name": name,
                "description": description,
                "function_name": func.__name__,
                "module_path": func.__module__,
                "schedule_type": schedule_type
            }

            @wraps(func)
            async def wrapper(*args, **kwargs):
                return await func(*args, **kwargs)
            return wrapper
        return decorator

    @classmethod
    def get_jobs(cls) -> Dict[str, Dict[str, Any]]:
        """Get all registered jobs"""
        return cls._jobs

    @classmethod
    async def sync_to_database(cls):
        """Sync registered jobs to database"""
        db = await get_db()
        try:
            for job_name, job_info in cls._jobs.items():
                # Check if job exists
                result = await db.execute(select(Job).where(Job.name == job_name))
                existing_job = result.scalar_one_or_none()

                if not existing_job:
                    # Create new job record
                    new_job = Job(
                        name=job_name,
                        description=job_info["description"],
                        function_name=job_info["function_name"],
                        module_path=job_info["module_path"],
                        schedule_type=job_info["schedule_type"]
                    )
                    db.add(new_job)

            await db.commit()
        finally:
            await db.close()


# Global registry instance
job_registry = JobRegistry()
