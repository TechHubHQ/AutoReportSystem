"""
Task Runner for AutomateReportSystem

Runs tasks based on configuration from the database instead of static times.
Integrates with the job management UI to use user-configured schedules.
"""

import asyncio
import json
import importlib
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional, Callable
from app.core.jobs.scheduler import scheduler
from app.core.interface.job_interface import JobInterface
from app.core.jobs.discovery import initialize_jobs
from app.core.jobs.report_sender import send_report
from app.core.utils.timezone_utils import (
    IST, UTC, now_ist, get_next_daily_run_ist, next_monthly_run_ist
)


class task_runner:
    """Handles task scheduling based on database configuration"""

    def __init__(self):
        self.scheduled_jobs = {}
        self.running = False

    async def start(self):
        """Start the task runner"""
        print("🚀 Starting Task Runner...")

        # Initialize job discovery and registration
        print("📋 Discovering and registering jobs...")
        await initialize_jobs()
        print("✅ Job registration complete.")

        # Load and schedule all active jobs from database
        await self.load_and_schedule_jobs()

        # Start the enhanced scheduler
        await scheduler.start()

        self.running = True
        print("🎯 Task Runner is now active and monitoring jobs.")

        # Start monitoring loop
        await self.monitor_jobs()

    async def stop(self):
        """Stop the task runner"""
        print("🛑 Stopping Task Runner...")
        self.running = False
        await scheduler.stop()
        print("✅ Task Runner stopped.")

    async def load_and_schedule_jobs(self):
        """Load all active jobs from database and schedule them"""
        try:
            jobs = await JobInterface.get_active_jobs()
            print(f"📊 Found {len(jobs)} active jobs to schedule")

            for job in jobs:
                await self.schedule_job(job)

        except Exception as e:
            print(f"❌ Error loading jobs: {e}")

    async def schedule_job(self, job):
        """Schedule a single job based on its configuration"""
        try:
            print(f"⏰ Scheduling job: {job.name}")

            # Parse schedule configuration
            schedule_config = {}
            if job.schedule_config:
                try:
                    schedule_config = json.loads(job.schedule_config)
                except json.JSONDecodeError:
                    print(f"⚠️ Invalid schedule config for job {job.name}")
                    return

            # Get job configuration
            job_config = schedule_config.get('job', {})

            # Use schedule config for time settings if available
            if not job_config and schedule_config:
                # If no job config but schedule config exists, use schedule config directly
                job_config = schedule_config

            # Create the job function
            job_function = await self.create_job_function(job, job_config)
            if not job_function:
                print(f"❌ Failed to create function for job {job.name}")
                return

            # Schedule based on schedule type
            if job.schedule_type == "daily":
                await self.schedule_daily_job(job, job_function, schedule_config)
            elif job.schedule_type == "weekly":
                await self.schedule_weekly_job(job, job_function, schedule_config)
            elif job.schedule_type == "monthly":
                await self.schedule_monthly_job(job, job_function, schedule_config)
            elif job.schedule_type == "custom":
                await self.schedule_custom_job(job, job_function, schedule_config)

            print(f"✅ Job {job.name} scheduled successfully")

        except Exception as e:
            print(f"❌ Error scheduling job {job.name}: {e}")

    async def create_job_function(self, job, job_config: Dict[str, Any]) -> Optional[Callable]:
        """Create a callable function for the job"""
        try:
            # Check if it's a template-based job
            if job_config.get('template_id'):
                # Create template-based job function
                async def template_job():
                    print(f"📧 Sending report with template {job_config['template_id']}")
                    print(f"📄 Content type: {job_config.get('content_type', 'all')}")
                    print(f"👤 User ID: {job_config.get('user_id')}")
                    print(f"📧 Recipients: {job_config.get('recipients', [])}")
                    
                    result = await send_report(
                        template_id=job_config['template_id'],
                        content_type=job_config.get('content_type', 'all'),
                        user_id=job_config.get('user_id'),
                        recipients=job_config.get('recipients', [])
                    )
                    
                    if result:
                        print(f"✅ Report sent successfully")
                    else:
                        print(f"❌ Report sending failed")
                    
                    return result
                return template_job

            # Check if it's a custom job with code
            elif hasattr(job, 'code') and job.code:
                # Execute custom code
                async def custom_job():
                    try:
                        # Create execution environment
                        exec_globals = {
                            '__builtins__': __builtins__,
                            'send_report': send_report,
                            'print': print,
                            'datetime': datetime,
                            'json': json
                        }

                        # Execute the job code
                        exec(job.code, exec_globals)

                        # Try to find and call the function
                        function_name = job.function_name
                        if function_name in exec_globals:
                            func = exec_globals[function_name]
                            if asyncio.iscoroutinefunction(func):
                                await func()
                            else:
                                func()
                        else:
                            print(
                                f"⚠️ Function {function_name} not found in job code")

                    except Exception as e:
                        print(f"❌ Error executing custom job {job.name}: {e}")
                        raise e

                return custom_job

            # Try to import and call registered function
            else:
                try:
                    module = importlib.import_module(job.module_path)
                    function = getattr(module, job.function_name)
                    return function
                except (ImportError, AttributeError) as e:
                    print(
                        f"⚠️ Could not import function {job.function_name} from {job.module_path}: {e}")
                    return None

        except Exception as e:
            print(f"❌ Error creating job function for {job.name}: {e}")
            return None

    async def schedule_daily_job(self, job, job_function, config: Dict[str, Any]):
        """Schedule a daily job"""
        # Check both job config and schedule config for time settings
        job_config = config.get('job', {})
        hour = config.get('hour', job_config.get('hour', 9))
        minute = config.get('minute', job_config.get('minute', 0))

        print(
            f"📅 Scheduling daily job '{job.name}' for {hour:02d}:{minute:02d} IST")

        # Calculate seconds until next run in IST
        target = get_next_daily_run_ist(hour, minute)
        now = now_ist()
        delay = (target - now).total_seconds()

        job_id = await scheduler.schedule_task(
            job_function,
            delay=delay,
            repeat=24 * 60 * 60,  # 24 hours
            job_name=job.name,
            db_job_id=job.id
        )

        self.scheduled_jobs[job.id] = job_id

    async def schedule_weekly_job(self, job, job_function, config: Dict[str, Any]):
        """Schedule a weekly job"""
        # Check both job config and schedule config for time settings
        job_config = config.get('job', {})
        day_of_week = config.get('day_of_week', job_config.get(
            'day_of_week', 0))  # Monday = 0
        hour = config.get('hour', job_config.get('hour', 9))
        minute = config.get('minute', job_config.get('minute', 0))

        days = ["Monday", "Tuesday", "Wednesday",
                "Thursday", "Friday", "Saturday", "Sunday"]
        day_name = days[day_of_week]

        print(
            f"📅 Scheduling weekly job '{job.name}' for {day_name} at {hour:02d}:{minute:02d} IST")

        job_id = await scheduler.schedule_task(
            job_function,
            day_of_week=day_of_week,
            hour=hour,
            minute=minute,
            job_name=job.name,
            db_job_id=job.id
        )

        self.scheduled_jobs[job.id] = job_id

    async def schedule_monthly_job(self, job, job_function, config: Dict[str, Any]):
        """Schedule a monthly job"""
        # Check both job config and schedule config for time settings
        job_config = config.get('job', {})
        day_of_month = config.get(
            'day_of_month', job_config.get('day_of_month', 1))
        hour = config.get('hour', job_config.get('hour', 9))
        minute = config.get('minute', job_config.get('minute', 0))

        print(
            f"📅 Scheduling monthly job '{job.name}' for day {day_of_month} at {hour:02d}:{minute:02d} IST")

        def next_monthly_run():
            return next_monthly_run_ist(day_of_month, hour, minute)

        job_id = await scheduler.schedule_task(
            job_function,
            next_run=next_monthly_run,
            job_name=job.name,
            db_job_id=job.id
        )

        self.scheduled_jobs[job.id] = job_id

    async def schedule_custom_job(self, job, job_function, config: Dict[str, Any]):
        """Schedule a custom cron-based job"""
        cron_expression = config.get(
            'cron', '0 9 * * *')  # Default: daily at 9 AM

        # Parse cron expression (simplified implementation)
        # Format: minute hour day month day_of_week
        try:
            parts = cron_expression.split()
            if len(parts) != 5:
                raise ValueError("Invalid cron expression format")

            minute_part, hour_part, day_part, month_part, dow_part = parts

            def next_cron_run():
                now = datetime.now(timezone.utc)

                # Simple cron parsing - handle basic cases
                minute = int(minute_part) if minute_part != '*' else now.minute
                hour = int(hour_part) if hour_part != '*' else now.hour

                # Calculate next run time in IST
                now = now_ist()
                target = now.replace(minute=minute, second=0, microsecond=0)

                if hour_part != '*':
                    target = target.replace(hour=int(hour_part))

                # If time has passed today, move to tomorrow
                if now >= target:
                    target += timedelta(days=1)

                return target.timestamp()

            job_id = await scheduler.schedule_task(
                job_function,
                next_run=next_cron_run,
                job_name=job.name,
                db_job_id=job.id
            )

            self.scheduled_jobs[job.id] = job_id

        except Exception as e:
            print(
                f"❌ Error parsing cron expression '{cron_expression}' for job {job.name}: {e}")

    async def monitor_jobs(self):
        """Monitor for job configuration changes and reschedule as needed"""
        print("👁️ Starting job monitoring loop...")

        while self.running:
            try:
                # Check for job updates every 5 minutes
                await asyncio.sleep(300)  # 5 minutes

                if not self.running:
                    break

                print("🔍 Checking for job configuration changes...")
                await self.reload_jobs()

            except Exception as e:
                print(f"❌ Error in job monitoring: {e}")
                await asyncio.sleep(60)  # Wait 1 minute before retrying

    async def reload_jobs(self):
        """Reload and reschedule jobs if configurations have changed"""
        try:
            # Get current active jobs
            current_jobs = await JobInterface.get_active_jobs()
            current_job_ids = {job.id for job in current_jobs}
            scheduled_job_ids = set(self.scheduled_jobs.keys())

            # Find jobs that need to be added or updated
            jobs_to_schedule = []
            for job in current_jobs:
                if job.id not in scheduled_job_ids:
                    jobs_to_schedule.append(job)
                    print(f"🆕 New job detected: {job.name}")

            # Find jobs that need to be removed
            jobs_to_remove = scheduled_job_ids - current_job_ids
            for db_job_id in jobs_to_remove:
                scheduler_job_id = self.scheduled_jobs.get(db_job_id)
                if scheduler_job_id:
                    print(f"🗑️ Removing inactive job: {db_job_id}")
                    await scheduler.cancel_job(scheduler_job_id)
                    del self.scheduled_jobs[db_job_id]

            # Schedule new jobs
            for job in jobs_to_schedule:
                await self.schedule_job(job)

            if jobs_to_schedule or jobs_to_remove:
                print(
                    f"🔄 Job reload complete: +{len(jobs_to_schedule)} -{len(jobs_to_remove)}")

        except Exception as e:
            print(f"❌ Error reloading jobs: {e}")

    async def run_job_now(self, job_name: str) -> bool:
        """Run a job immediately for testing"""
        try:
            jobs = await JobInterface.get_active_jobs()
            target_job = next((job for job in jobs if job.name == job_name), None)
            
            if not target_job:
                print(f"❌ Job '{job_name}' not found")
                return False
            
            print(f"⚡ Running job '{job_name}' immediately...")
            
            # Parse job configuration
            schedule_config = {}
            if target_job.schedule_config:
                try:
                    schedule_config = json.loads(target_job.schedule_config)
                    print(f"📋 Job config: {schedule_config}")
                except json.JSONDecodeError:
                    print(f"⚠️ Invalid JSON in schedule config")
            
            job_config = schedule_config.get('job', {})
            if not job_config and schedule_config:
                job_config = schedule_config
            
            print(f"📄 Template ID: {job_config.get('template_id')}")
            print(f"📧 Recipients: {job_config.get('recipients')}")
            
            # Create and execute job function
            job_function = await self.create_job_function(target_job, job_config)
            if job_function:
                await job_function()
                print(f"✅ Job '{job_name}' executed successfully")
                return True
            else:
                print(f"❌ Failed to create function for job '{job_name}'")
                return False
                
        except Exception as e:
            print(f"❌ Error running job immediately: {e}")
            import traceback
            traceback.print_exc()
            return False

    async def get_job_status(self) -> Dict[str, Any]:
        """Get status of all scheduled jobs"""
        try:
            jobs = await JobInterface.get_active_jobs()
            scheduler_status = await scheduler.get_all_jobs_status()

            status = {
                'total_jobs': len(jobs),
                'scheduled_jobs': len(self.scheduled_jobs),
                'running': self.running,
                'scheduler_status': scheduler_status,
                'jobs': []
            }

            for job in jobs:
                scheduler_job_id = self.scheduled_jobs.get(job.id)
                scheduler_job_status = None

                if scheduler_job_id:
                    scheduler_job_status = await scheduler.get_job_status(scheduler_job_id)

                job_info = {
                    'id': job.id,
                    'name': job.name,
                    'schedule_type': job.schedule_type,
                    'is_active': job.is_active,
                    'last_run': job.last_run.isoformat() if job.last_run else None,
                    'next_run': job.next_run.isoformat() if job.next_run else None,
                    'scheduled': job.id in self.scheduled_jobs,
                    'scheduler_status': scheduler_job_status
                }
                status['jobs'].append(job_info)

            return status

        except Exception as e:
            print(f"❌ Error getting job status: {e}")
            return {'error': str(e)}


# Global instance
task_runner = task_runner()


async def run_tasks():
    """Main entry point for task runner"""
    try:
        await task_runner.start()
    except KeyboardInterrupt:
        print("🛑 Received interrupt signal")
    except Exception as e:
        print(f"❌ task runner error: {e}")
    finally:
        await task_runner.stop()


if __name__ == "__main__":
    print("🚀 Starting Task Runner...")
    asyncio.run(run_tasks())
