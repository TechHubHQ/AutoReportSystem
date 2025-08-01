from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.models import Job
from app.database.db_connector import get_db
from typing import List, Optional
from datetime import datetime


class JobInterface:
    @staticmethod
    async def get_all_jobs() -> List[Job]:
        """Get all jobs from database"""
        db = await get_db()
        try:
            result = await db.execute(select(Job))
            return result.scalars().all()
        finally:
            await db.close()

    @staticmethod
    async def get_active_jobs() -> List[Job]:
        """Get only active jobs"""
        db = await get_db()
        try:
            result = await db.execute(select(Job).where(Job.is_active == True))
            return result.scalars().all()
        finally:
            await db.close()

    @staticmethod
    async def update_job_status(job_id: int, is_active: bool) -> bool:
        """Update job active status"""
        db = await get_db()
        try:
            await db.execute(
                update(Job)
                .where(Job.id == job_id)
                .values(is_active=is_active)
            )
            await db.commit()
            return True
        finally:
            await db.close()

    @staticmethod
    async def update_job_run_times(job_name: str, last_run: datetime, next_run: Optional[datetime] = None):
        """Update job run times"""
        db = await get_db()
        try:
            values = {"last_run": last_run}
            if next_run:
                values["next_run"] = next_run

            await db.execute(
                update(Job)
                .where(Job.name == job_name)
                .values(**values)
            )
            await db.commit()
        finally:
            await db.close()
