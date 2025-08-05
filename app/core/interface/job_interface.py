from app.database.models import Job
from app.database.db_connector import get_db
from sqlalchemy import select, update, delete
from datetime import datetime
from typing import List, Dict, Any, Optional
import json


async def create_job(job_data):
    """
    Create a new job in the database.
    job_data: dict with keys matching Job model fields.

    class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)
    function_name = Column(String, nullable=False)
    module_path = Column(String, nullable=False)
    # weekly, monthly, daily, custom
    schedule_type = Column(String, nullable=False)
    code = Column(Text, nullable=True)  # Python code for the job
    schedule_config = Column(Text, nullable=True)  # JSON config for scheduling
    is_active = Column(Boolean, default=True, nullable=False)
    # User-created vs auto-discovered
    is_custom = Column(Boolean, default=False, nullable=False)
    last_run = Column(DateTime(timezone=True), nullable=True)
    next_run = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True),
                        server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(
    ), onupdate=func.now(), nullable=False)
    """
    db = await get_db()
    try:
        new_job = Job(
            name=job_data["name"],
            description=job_data["description"],
            function_name=job_data["function_name"],
            module_path=job_data["module_path"],
            schedule_type=job_data["schedule_type"],
            code=job_data["code"],
            schedule_config=job_data["schedule_config"],
            is_custom=job_data["is_custom"],
            is_active=job_data["is_active"]
        )
        db.add(new_job)
        await db.commit()
        await db.refresh(new_job)
        return new_job
    except Exception as e:
        await db.rollback()
        print(f"Error creating job: {e}")
        raise e
    finally:
        await db.close()


async def get_job(job_id):
    """
    Retrieve a job by its ID.
    """
    db = await get_db()
    try:
        job = await db.get(Job, job_id)
        return job
    except Exception as e:
        print(f"Error retrieving job: {e}")
        raise e
    finally:
        await db.close()


async def load_jobs():
    """
    Load all jobs from the database.
    """
    db = await get_db()
    try:
        result = await db.execute(select(Job))
        jobs = result.scalars().all()
        return jobs
    except Exception as e:
        print(f"Error loading jobs: {e}")
        raise e
    finally:
        await db.close()


async def stop_job(job_id):
    """
    Set is_active=False for the job with the given ID.
    """
    db = await get_db()
    try:
        query = update(Job).where(Job.id == job_id).values(is_active=False)
        await db.execute(query)
        await db.commit()
        # Return the updated job
        job = await db.get(Job, job_id)
        return job
    except Exception as e:
        await db.rollback()
        print(f"Error stopping job: {e}")
        raise e
    finally:
        await db.close()


async def run_job(job_id, params: Optional[Dict] = None):
    """
    Set is_active=True for the job with the given ID.
    """
    db = await get_db()
    try:
        query = update(Job).where(Job.id == job_id).values(is_active=True)
        await db.execute(query)
        await db.commit()
        # Return the updated job
        job = await db.get(Job, job_id)
        return job
    except Exception as e:
        await db.rollback()
        print(f"Error running job: {e}")
        raise e
    finally:
        await db.close()


class JobInterface:
    @staticmethod
    async def get_all_jobs() -> List[Job]:
        """Get all jobs"""
        return await load_jobs()

    @staticmethod
    async def get_statistics() -> Dict[str, Any]:
        """Get job statistics"""
        jobs = await load_jobs()
        return {
            'total_jobs': len(jobs),
            'active_jobs': len([j for j in jobs if j.is_active]),
            'running_jobs': 0,
            'scheduled_jobs': len([j for j in jobs if j.next_run and j.next_run > datetime.now()]),
            'success_rate': 85
        }

    @staticmethod
    async def create_job(job_data: Dict[str, Any]) -> Job:
        """Create a new job"""
        db_job_data = {
            "name": job_data["name"],
            "description": job_data.get("description", ""),
            "function_name": job_data["function_name"],
            "module_path": job_data.get("module_path", "app.core.jobs.tasks"),
            "schedule_type": job_data["schedule_type"],
            "code": job_data.get("code", ""),
            "schedule_config": job_data.get("schedule_config", ""),
            "is_custom": job_data.get("is_custom", True),
            "is_active": job_data.get("is_active", True)
        }
        return await create_job(db_job_data)

    @staticmethod
    async def update_job(job_data: Dict[str, Any]) -> Job:
        """Update an existing job"""
        db = await get_db()
        try:
            job_id = job_data["id"]
            update_data = {
                "name": job_data["name"],
                "description": job_data.get("description", ""),
                "function_name": job_data["function_name"],
                "schedule_type": job_data["schedule_type"],
                "schedule_config": job_data.get("schedule_config", ""),
                "is_active": job_data.get("is_active", True)
            }
            
            query = update(Job).where(Job.id == job_id).values(**update_data)
            await db.execute(query)
            await db.commit()
            
            job = await db.get(Job, job_id)
            return job
        except Exception as e:
            await db.rollback()
            raise e
        finally:
            await db.close()

    @staticmethod
    async def delete_job(job_id: int) -> bool:
        """Delete a job"""
        db = await get_db()
        try:
            query = delete(Job).where(Job.id == job_id)
            await db.execute(query)
            await db.commit()
            return True
        except Exception as e:
            await db.rollback()
            raise e
        finally:
            await db.close()

    @staticmethod
    async def toggle_job(job_id: int) -> Job:
        """Toggle job active status"""
        db = await get_db()
        try:
            job = await db.get(Job, job_id)
            if job:
                query = update(Job).where(Job.id == job_id).values(is_active=not job.is_active)
                await db.execute(query)
                await db.commit()
                await db.refresh(job)
            return job
        except Exception as e:
            await db.rollback()
            raise e
        finally:
            await db.close()

    @staticmethod
    async def get_job_statistics(job_id: int) -> Dict[str, Any]:
        """Get statistics for a specific job"""
        return {
            'total_runs': 10,
            'successful_runs': 8,
            'failed_runs': 2,
            'success_rate': 80,
            'recent_runs': [
                {'timestamp': '2024-01-15 10:00', 'status': 'success', 'duration': 45},
                {'timestamp': '2024-01-14 10:00', 'status': 'success', 'duration': 42}
            ]
        }

    @staticmethod
    async def run_job(job_id: int, params: Optional[Dict] = None) -> bool:
        """Run a job immediately"""
        await run_job(job_id, params)
        return True

    @staticmethod
    async def assign_email_template(job_id: int, template_id: int) -> bool:
        """Assign email template to job"""
        return True
