"""
Task Lifecycle Management Job

This job handles the automatic lifecycle of tasks:
1. Auto-archive: Move tasks older than 30 days to archive
2. Auto-delete: Permanently delete archived tasks older than 30 days

Flow: Task Creation → 30 days → Archive → 30 days → Delete
"""

from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any
from sqlalchemy import select, update, delete, and_

from app.database.db_connector import get_db
from app.database.models import Task, TaskStatusHistory, TaskNote
from app.core.utils.datetime_utils import get_current_utc_datetime
from app.core.interface.job_tracking_interface import JobExecutionTracker
from app.config.logging_config import get_logger

logger = get_logger(__name__)


async def get_tasks_to_archive() -> List[Task]:
    """Get tasks that are older than 30 days and should be archived"""
    try:
        db = await get_db()

        # Calculate the cutoff date (30 days ago)
        cutoff_date = get_current_utc_datetime() - timedelta(days=30)

        # Find active tasks older than 30 days
        query = select(Task).where(
            and_(
                Task.is_archived == False,
                Task.created_at < cutoff_date
            )
        ).order_by(Task.created_at.asc())

        result = await db.execute(query)
        tasks = result.scalars().all()

        logger.info(f"Found {len(tasks)} tasks eligible for auto-archiving")
        return tasks

    except Exception as e:
        logger.error(f"Error fetching tasks to archive: {e}")
        raise e
    finally:
        await db.close()


async def get_archived_tasks_to_delete() -> List[Task]:
    """Get archived tasks that are older than 30 days and should be deleted"""
    try:
        db = await get_db()

        # Calculate the cutoff date (30 days ago)
        cutoff_date = get_current_utc_datetime() - timedelta(days=30)

        # Find archived tasks older than 30 days
        query = select(Task).where(
            and_(
                Task.is_archived == True,
                Task.archived_at < cutoff_date
            )
        ).order_by(Task.archived_at.asc())

        result = await db.execute(query)
        tasks = result.scalars().all()

        logger.info(f"Found {len(tasks)} archived tasks eligible for deletion")
        return tasks

    except Exception as e:
        logger.error(f"Error fetching archived tasks to delete: {e}")
        raise e
    finally:
        await db.close()


async def auto_archive_task(task: Task) -> bool:
    """Archive a single task automatically"""
    try:
        db = await get_db()

        # Update task with archive information
        update_data = {
            'is_archived': True,
            'archived_at': get_current_utc_datetime(),
            'archived_by': None,  # System archival, no specific user
            'updated_at': get_current_utc_datetime()
        }

        query = update(Task).where(Task.id == task.id).values(**update_data)
        result = await db.execute(query)

        if result.rowcount == 0:
            logger.warning(f"No task was archived for task_id {task.id}")
            await db.rollback()
            return False

        await db.commit()
        logger.info(
            f"Successfully auto-archived task {task.id}: '{task.title}'")
        return True

    except Exception as e:
        logger.error(f"Error auto-archiving task {task.id}: {e}")
        await db.rollback()
        raise e
    finally:
        await db.close()


async def auto_delete_task(task: Task) -> bool:
    """Permanently delete an archived task and all its related records"""
    try:
        db = await get_db()

        logger.info(
            f"Auto-deleting archived task {task.id}: '{task.title}' and all related records")

        # Delete related records first to avoid foreign key constraint violations
        # Delete task status history
        status_history_result = await db.execute(
            delete(TaskStatusHistory).where(
                TaskStatusHistory.task_id == task.id)
        )
        logger.debug(
            f"Deleted {status_history_result.rowcount} status history records for task {task.id}")

        # Delete task notes
        notes_result = await db.execute(
            delete(TaskNote).where(TaskNote.task_id == task.id)
        )
        logger.debug(
            f"Deleted {notes_result.rowcount} note records for task {task.id}")

        # Now delete the task itself
        task_delete_result = await db.execute(delete(Task).where(Task.id == task.id))

        if task_delete_result.rowcount == 0:
            logger.warning(f"No task was deleted for task_id {task.id}")
            await db.rollback()
            return False

        await db.commit()
        logger.info(
            f"Successfully auto-deleted task {task.id} and all related records")
        return True

    except Exception as e:
        logger.error(f"Error auto-deleting task {task.id}: {e}")
        await db.rollback()
        raise e
    finally:
        await db.close()


async def run_task_lifecycle_management(force: bool = False, job_id: str = None) -> Dict[str, Any]:
    """
    Main function to run task lifecycle management

    Args:
        force: If True, run regardless of schedule
        job_id: Job ID for tracking

    Returns:
        Dict with execution results
    """
    # Use provided job_id or default
    actual_job_id = job_id if job_id else 'task_lifecycle_manager'

    # Use the job tracking system
    async with JobExecutionTracker(
        job_name=actual_job_id,
        trigger_type="scheduled" if not force else "manual"
    ) as tracker:

        await tracker.log("INFO", "Starting task lifecycle management execution")

        execution_result = {
            'job_id': actual_job_id,
            'status': 'success',
            'message': '',
            'details': [],
            'tasks_archived': 0,
            'tasks_deleted': 0,
            'errors': [],
            'execution_time': datetime.now(),
            'forced': force
        }

        try:
            current_time = get_current_utc_datetime()
            execution_result['details'].append(
                f"Execution started at {current_time.strftime('%Y-%m-%d %H:%M:%S')} UTC"
            )

            if force:
                execution_result['details'].append(
                    "⚡ FORCED EXECUTION - Running manually")
                await tracker.log("WARNING", "FORCED EXECUTION - Running manually")

            # Phase 1: Auto-archive old tasks
            await tracker.log("INFO", "Phase 1: Auto-archiving tasks older than 30 days")
            execution_result['details'].append(
                "📦 Phase 1: Auto-archiving tasks older than 30 days")

            tasks_to_archive = await get_tasks_to_archive()
            execution_result['details'].append(
                f"Found {len(tasks_to_archive)} tasks to archive")

            for task in tasks_to_archive:
                try:
                    days_old = (
                        current_time - task.created_at.replace(tzinfo=timezone.utc)).days
                    await tracker.log("INFO", f"Auto-archiving task {task.id}: '{task.title}' (created {days_old} days ago)")

                    success = await auto_archive_task(task)
                    if success:
                        execution_result['tasks_archived'] += 1
                        execution_result['details'].append(
                            f"✅ Archived: '{task.title}' (ID: {task.id}, {days_old} days old)"
                        )
                        await tracker.log("INFO", f"✅ Successfully archived task {task.id}")
                    else:
                        error_msg = f"Failed to archive task {task.id}: '{task.title}'"
                        execution_result['errors'].append(error_msg)
                        execution_result['details'].append(f"❌ {error_msg}")
                        await tracker.log("ERROR", error_msg)

                except Exception as e:
                    error_msg = f"Error archiving task {task.id}: {str(e)}"
                    execution_result['errors'].append(error_msg)
                    execution_result['details'].append(f"❌ {error_msg}")
                    await tracker.log("ERROR", error_msg)

            # Phase 2: Auto-delete old archived tasks
            await tracker.log("INFO", "Phase 2: Auto-deleting archived tasks older than 30 days")
            execution_result['details'].append(
                "🗑️ Phase 2: Auto-deleting archived tasks older than 30 days")

            archived_tasks_to_delete = await get_archived_tasks_to_delete()
            execution_result['details'].append(
                f"Found {len(archived_tasks_to_delete)} archived tasks to delete")

            for task in archived_tasks_to_delete:
                try:
                    days_archived = (
                        current_time - task.archived_at.replace(tzinfo=timezone.utc)).days
                    await tracker.log("INFO", f"Auto-deleting archived task {task.id}: '{task.title}' (archived {days_archived} days ago)")

                    success = await auto_delete_task(task)
                    if success:
                        execution_result['tasks_deleted'] += 1
                        execution_result['details'].append(
                            f"✅ Deleted: '{task.title}' (ID: {task.id}, archived {days_archived} days ago)"
                        )
                        await tracker.log("INFO", f"✅ Successfully deleted archived task {task.id}")
                    else:
                        error_msg = f"Failed to delete archived task {task.id}: '{task.title}'"
                        execution_result['errors'].append(error_msg)
                        execution_result['details'].append(f"❌ {error_msg}")
                        await tracker.log("ERROR", error_msg)

                except Exception as e:
                    error_msg = f"Error deleting archived task {task.id}: {str(e)}"
                    execution_result['errors'].append(error_msg)
                    execution_result['details'].append(f"❌ {error_msg}")
                    await tracker.log("ERROR", error_msg)

            # Determine final status and message
            if execution_result['errors']:
                execution_result['status'] = 'partial_success'
                execution_result['message'] = (
                    f"Task lifecycle management completed with {len(execution_result['errors'])} errors. "
                    f"Archived: {execution_result['tasks_archived']}, Deleted: {execution_result['tasks_deleted']}"
                )
            else:
                execution_result['message'] = (
                    f"Task lifecycle management completed successfully. "
                    f"Archived: {execution_result['tasks_archived']}, Deleted: {execution_result['tasks_deleted']}"
                )

            await tracker.log("INFO", execution_result['message'])

        except Exception as e:
            execution_result['status'] = 'error'
            execution_result[
                'message'] = f"Critical error in task lifecycle management: {str(e)}"
            execution_result['errors'].append(str(e))
            execution_result['details'].append(f"❌ Critical error: {str(e)}")
            await tracker.log("ERROR", f"Critical error: {str(e)}")
            logger.error(f"Critical error in task lifecycle management: {e}")
            raise  # Re-raise to trigger failure in tracker

        finally:
            execution_result['details'].append(
                f"Execution completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )

            # Store result data in the tracker
            await tracker.set_result_data(execution_result)

            # Store result in global storage for UI display (backward compatibility)
            from app.core.jobs.job_results_store import store_job_result
            store_job_result(actual_job_id, execution_result)

            await tracker.log("INFO", "Task lifecycle management execution completed")

            return execution_result


# Alias for easier job configuration
async def manage_task_lifecycle(force: bool = False, job_id: str = None):
    """Alias for run_task_lifecycle_management for job configuration"""
    return await run_task_lifecycle_management(force=force, job_id=job_id)
