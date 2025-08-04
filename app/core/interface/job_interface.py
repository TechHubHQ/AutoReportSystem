from sqlalchemy import select, update, delete as sql_delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.models import Job
from app.database.db_connector import get_db
from typing import List, Optional
from datetime import datetime
import json


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

    @staticmethod
    async def create_job(name: str, description: str, function_name: str, code: str,
                         schedule_type: str, schedule_config: str = None, 
                         job_config: str = None) -> bool:
        """Create a new custom job with optional job configuration"""
        db = await get_db()
        try:
            # Combine schedule_config and job_config properly
            final_config = {}
            
            # First add schedule configuration (time settings)
            if schedule_config:
                try:
                    schedule_data = json.loads(schedule_config)
                    final_config.update(schedule_data)
                except json.JSONDecodeError:
                    pass
            
            # Then add job configuration (template, recipients, etc.)
            if job_config:
                try:
                    job_data = json.loads(job_config)
                    final_config['job'] = job_data
                except json.JSONDecodeError:
                    pass
            
            new_job = Job(
                name=name,
                description=description,
                function_name=function_name,
                module_path="custom_jobs",
                code=code,
                schedule_type=schedule_type,
                schedule_config=json.dumps(final_config) if final_config else None,
                is_custom=True
            )
            db.add(new_job)
            await db.commit()
            return True
        finally:
            await db.close()

    @staticmethod
    async def update_job(job_id: int, schedule_config: str = None, job_config: str = None, **kwargs) -> bool:
        """Update job details with optional job configuration"""
        db = await get_db()
        try:
            # Handle configuration updates properly
            if schedule_config is not None or job_config is not None:
                # Get current job to merge configs
                current_job = await JobInterface.get_job_by_id(job_id)
                current_config = {}
                
                if current_job and current_job.schedule_config:
                    try:
                        current_config = json.loads(current_job.schedule_config)
                    except json.JSONDecodeError:
                        current_config = {}
                
                # Update schedule configuration (time settings)
                if schedule_config:
                    try:
                        schedule_data = json.loads(schedule_config)
                        current_config.update(schedule_data)
                    except json.JSONDecodeError:
                        pass
                
                # Update job configuration (template, recipients, etc.)
                if job_config:
                    try:
                        job_data = json.loads(job_config)
                        current_config['job'] = job_data
                    except json.JSONDecodeError:
                        pass
                
                kwargs['schedule_config'] = json.dumps(current_config)
            
            await db.execute(
                update(Job)
                .where(Job.id == job_id)
                .values(**kwargs)
            )
            await db.commit()
            return True
        finally:
            await db.close()

    @staticmethod
    async def delete_job(job_id: int) -> bool:
        """Delete a job"""
        db = await get_db()
        try:
            await db.execute(sql_delete(Job).where(Job.id == job_id))
            await db.commit()
            return True
        finally:
            await db.close()

    @staticmethod
    async def get_job_by_id(job_id: int) -> Optional[Job]:
        """Get job by ID"""
        db = await get_db()
        try:
            result = await db.execute(select(Job).where(Job.id == job_id))
            return result.scalar_one_or_none()
        finally:
            await db.close()

    @staticmethod
    async def test_job_code(code: str) -> dict:
        """Test job code execution"""
        try:
            # Create a safe execution environment
            exec_globals = {
                '__builtins__': {
                    'print': print,
                    'len': len,
                    'str': str,
                    'int': int,
                    'float': float,
                    'dict': dict,
                    'list': list
                }
            }
            exec(code, exec_globals)
            return {"success": True, "message": "Code executed successfully"}
        except Exception as e:
            return {"success": False, "message": str(e)}
    
    @staticmethod
    async def get_job_config(job_id: int) -> dict:
        """Get job configuration for a job"""
        job = await JobInterface.get_job_by_id(job_id)
        if job and job.schedule_config:
            try:
                config = json.loads(job.schedule_config)
                return config.get('job', {})
            except json.JSONDecodeError:
                return {}
        return {}
