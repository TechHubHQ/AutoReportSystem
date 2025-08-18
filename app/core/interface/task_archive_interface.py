from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import select, update
from app.database.db_connector import get_db
from app.database.models import Task, TaskStatusHistory
from app.core.utils.datetime_utils import get_current_utc_datetime
from app.config.logging_config import get_logger

logger = get_logger(__name__)


async def archive_task(task_id: int, archived_by: int = None):
    """Archive a task by setting is_archived to True"""
    try:
        db = await get_db()
        
        # First, get the task to ensure it exists and is not already archived
        task_result = await db.execute(select(Task).where(Task.id == task_id))
        task = task_result.scalar_one_or_none()
        
        if not task:
            logger.warning(f"Task {task_id} not found for archiving")
            return False
            
        # Check if task has is_archived attribute (for backward compatibility)
        if not hasattr(task, 'is_archived'):
            logger.error(f"Task model does not support archiving. Please run database migration.")
            raise Exception("Archive functionality requires database migration")
        
        if task.is_archived:
            logger.warning(f"Task {task_id} is already archived")
            return False
        
        logger.info(f"Archiving task {task_id}: '{task.title}'")
        
        # Update the task to set archived status
        update_data = {
            'is_archived': True,
            'archived_at': get_current_utc_datetime(),
            'archived_by': archived_by,
            'updated_at': get_current_utc_datetime()
        }
        
        query = update(Task).where(Task.id == task_id).values(**update_data)
        result = await db.execute(query)
        
        if result.rowcount == 0:
            logger.warning(f"No task was archived for task_id {task_id}")
            await db.rollback()
            return False
        
        # Log the archive action in status history
        if archived_by is not None:
            status_history = TaskStatusHistory(
                task_id=task_id,
                old_status=task.status,
                new_status=task.status,  # Status doesn't change when archiving
                old_category=task.category,
                new_category=task.category,  # Category doesn't change when archiving
                changed_by=archived_by
            )
            db.add(status_history)
        
        await db.commit()
        logger.info(f"Successfully archived task {task_id}")
        return True
        
    except Exception as e:
        logger.error(f"Error while archiving task {task_id}: {e}")
        await db.rollback()
        raise e
    finally:
        await db.close()


async def revive_task(task_id: int, revived_by: int = None):
    """Revive an archived task by setting is_archived to False"""
    try:
        db = await get_db()
        
        # First, get the task to ensure it exists and is archived
        task_result = await db.execute(select(Task).where(Task.id == task_id))
        task = task_result.scalar_one_or_none()
        
        if not task:
            logger.warning(f"Task {task_id} not found for revival")
            return False
            
        # Check if task has is_archived attribute (for backward compatibility)
        if not hasattr(task, 'is_archived'):
            logger.error(f"Task model does not support archiving. Please run database migration.")
            raise Exception("Archive functionality requires database migration")
        
        if not task.is_archived:
            logger.warning(f"Task {task_id} is not archived, cannot revive")
            return False
        
        logger.info(f"Reviving task {task_id}: '{task.title}'")
        
        # Update the task to remove archived status
        update_data = {
            'is_archived': False,
            'archived_at': None,
            'archived_by': None,
            'updated_at': get_current_utc_datetime()
        }
        
        query = update(Task).where(Task.id == task_id).values(**update_data)
        result = await db.execute(query)
        
        if result.rowcount == 0:
            logger.warning(f"No task was revived for task_id {task_id}")
            await db.rollback()
            return False
        
        # Log the revival action in status history
        if revived_by is not None:
            status_history = TaskStatusHistory(
                task_id=task_id,
                old_status=task.status,
                new_status=task.status,  # Status doesn't change when reviving
                old_category=task.category,
                new_category=task.category,  # Category doesn't change when reviving
                changed_by=revived_by
            )
            db.add(status_history)
        
        await db.commit()
        logger.info(f"Successfully revived task {task_id}")
        return True
        
    except Exception as e:
        logger.error(f"Error while reviving task {task_id}: {e}")
        await db.rollback()
        raise e
    finally:
        await db.close()


async def get_active_tasks(user_id: Optional[int] = None) -> List[Task]:
    """Get all non-archived tasks, optionally filtered by user"""
    try:
        db = await get_db()
        query = select(Task).where(Task.is_archived == False)
        if user_id:
            query = query.where(Task.created_by == user_id)
        query = query.order_by(Task.created_at.desc())

        result = await db.execute(query)
        tasks = result.scalars().all()
        return tasks
    except Exception as e:
        logger.error(f"Error while fetching active tasks: {e}")
        raise e
    finally:
        await db.close()


async def get_archived_tasks_only(user_id: Optional[int] = None) -> List[Task]:
    """Get only archived tasks, optionally filtered by user"""
    try:
        db = await get_db()
        query = select(Task).where(Task.is_archived == True)
        if user_id:
            query = query.where(Task.created_by == user_id)
        query = query.order_by(Task.archived_at.desc())

        result = await db.execute(query)
        tasks = result.scalars().all()
        return tasks
    except Exception as e:
        logger.error(f"Error while fetching archived tasks: {e}")
        raise e
    finally:
        await db.close()


async def get_task_archive_statistics(user_id: Optional[int] = None):
    """Get archive statistics for dashboard"""
    try:
        db = await get_db()

        # Base query
        base_query = select(Task)
        if user_id:
            base_query = base_query.where(Task.created_by == user_id)

        # Get all tasks
        result = await db.execute(base_query)
        all_tasks = result.scalars().all()

        # Calculate statistics
        stats = {
            'total_tasks': len(all_tasks),
            'active_tasks': len([t for t in all_tasks if not getattr(t, 'is_archived', False)]),
            'archived_tasks': len([t for t in all_tasks if getattr(t, 'is_archived', False)]),
            'archive_percentage': 0
        }
        
        if stats['total_tasks'] > 0:
            stats['archive_percentage'] = round((stats['archived_tasks'] / stats['total_tasks']) * 100, 1)

        return stats
    except Exception as e:
        logger.error(f"Error while fetching archive statistics: {e}")
        raise e
    finally:
        await db.close()