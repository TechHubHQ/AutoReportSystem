from datetime import datetime, timedelta, timezone
from typing import List, Optional
from sqlalchemy import select, update, delete
from app.database.db_connector import get_db
from app.database.models import Task, TaskStatusHistory
from app.core.utils.datetime_utils import (
    ensure_timezone_aware, get_current_utc_datetime, safe_datetime_compare
)
from app.core.utils.task_automation_utils import (
    should_auto_categorize_to_accomplishments, should_auto_categorize_to_in_progress,
    log_automatic_category_change, TaskAutomationNotifier
)
from app.config.logging_config import get_logger

logger = get_logger(__name__)


async def create_task(title: str, description: str = "", status: str = "todo",
                      priority: str = "medium", category: str = "in progress",
                      due_date: Optional[datetime] = None, created_by: int = None):
    """Create a new task"""
    try:
        db = await get_db()
        new_task = Task(
            title=title,
            description=description,
            status=status,
            priority=priority,
            category=category,
            due_date=due_date,
            created_by=created_by
        )
        db.add(new_task)
        await db.commit()
        await db.refresh(new_task)

        # Log initial status in history
        status_history = TaskStatusHistory(
            task_id=new_task.id,
            old_status=None,  # No previous status for new task
            new_status=status,
            old_category=None,  # No previous category for new task
            new_category=category,
            changed_by=created_by
        )
        db.add(status_history)
        await db.commit()

        return new_task
    except Exception as e:
        logger.error(f"Error while creating new task: {e}")
        await db.rollback()
        raise e
    finally:
        await db.close()


async def get_tasks(user_id: Optional[int] = None) -> List[Task]:
    """Get all tasks, optionally filtered by user"""
    try:
        db = await get_db()
        query = select(Task)
        if user_id:
            query = query.where(Task.created_by == user_id)
        query = query.order_by(Task.created_at.desc())

        result = await db.execute(query)
        tasks = result.scalars().all()
        return tasks
    except Exception as e:
        logger.error(f"Error while fetching tasks: {e}")
        raise e
    finally:
        await db.close()


async def get_tasks_by_status(status: str, user_id: Optional[int] = None) -> List[Task]:
    """Get tasks filtered by status"""
    try:
        db = await get_db()
        query = select(Task).where(Task.status == status)
        if user_id:
            query = query.where(Task.created_by == user_id)
        query = query.order_by(Task.created_at.desc())

        result = await db.execute(query)
        tasks = result.scalars().all()
        return tasks
    except Exception as e:
        logger.error(f"Error while fetching tasks by status: {e}")
        raise e
    finally:
        await db.close()


async def get_tasks_by_category(category: str, user_id: Optional[int] = None) -> List[Task]:
    """Get tasks filtered by category"""
    try:
        db = await get_db()
        query = select(Task).where(Task.category == category)
        if user_id:
            query = query.where(Task.created_by == user_id)
        query = query.order_by(Task.created_at.desc())

        result = await db.execute(query)
        tasks = result.scalars().all()
        return tasks
    except Exception as e:
        logger.error(f"Error while fetching tasks by category: {e}")
        raise e
    finally:
        await db.close()


async def get_task(task_id: int) -> Optional[Task]:
    """Get a single task by ID"""
    try:
        db = await get_db()
        result = await db.execute(select(Task).where(Task.id == task_id))
        task = result.scalar_one_or_none()
        return task
    except Exception as e:
        logger.error(f"Error while fetching task: {e}")
        raise e
    finally:
        await db.close()


async def update_task(task_id: int, title: str = None, description: str = None,
                      status: str = None, priority: str = None, category: str = None,
                      due_date: datetime = None, updated_by: int = None):
    """Update an existing task"""
    try:
        db = await get_db()

        # Get current task to compare status/category changes
        current_task_result = await db.execute(select(Task).where(Task.id == task_id))
        current_task = current_task_result.scalar_one_or_none()
        if not current_task:
            raise Exception(f"Task {task_id} not found")

        # Build update dictionary with only provided values
        update_data = {}
        if title is not None:
            update_data['title'] = title
        if description is not None:
            update_data['description'] = description
        if status is not None:
            update_data['status'] = status
        if priority is not None:
            update_data['priority'] = priority
        if category is not None:
            update_data['category'] = category
        if due_date is not None:
            update_data['due_date'] = due_date

        # AUTOMATIC CATEGORY CHANGES:
        auto_category_changed = False

        # 1. If status is being changed to "completed", automatically set category to "accomplishments"
        if should_auto_categorize_to_accomplishments(current_task.status, status):
            update_data['category'] = "accomplishments"
            category = "accomplishments"  # Update the local variable for logging
            auto_category_changed = True
            log_automatic_category_change(
                task_id, current_task.category, "accomplishments", "completed", updated_by
            )

        # 2. If status is being changed from "completed" to any other status,
        # automatically set category back to "in progress"
        elif should_auto_categorize_to_in_progress(current_task.status, status):
            update_data['category'] = "in progress"
            category = "in progress"  # Update the local variable for logging
            auto_category_changed = True
            log_automatic_category_change(
                task_id, current_task.category, "in progress", status, updated_by
            )

        update_data['updated_at'] = get_current_utc_datetime()

        # Check if status or category changed
        status_changed = status is not None and status != current_task.status
        category_changed = category is not None and category != current_task.category

        # Update the task
        query = update(Task).where(Task.id == task_id).values(**update_data)
        await db.execute(query)

        # Log status/category changes if they occurred
        if (status_changed or category_changed) and updated_by is not None:
            status_history = TaskStatusHistory(
                task_id=task_id,
                old_status=current_task.status,
                new_status=status if status is not None else current_task.status,
                old_category=current_task.category,
                new_category=category if category is not None else current_task.category,
                changed_by=updated_by
            )
            db.add(status_history)

        await db.commit()

        # Send notification for automatic category changes
        if auto_category_changed:
            TaskAutomationNotifier.notify_category_change(
                task_id, current_task.title, current_task.category,
                category, updated_by
            )

        # Return updated task
        return await get_task(task_id)
    except Exception as e:
        logger.error(f"Error while updating task: {e}")
        await db.rollback()
        raise e
    finally:
        await db.close()


async def delete_task(task_id: int):
    """Delete a task"""
    try:
        db = await get_db()
        query = delete(Task).where(Task.id == task_id)
        await db.execute(query)
        await db.commit()
        return True
    except Exception as e:
        logger.error(f"Error while deleting task: {e}")
        await db.rollback()
        raise e
    finally:
        await db.close()


async def get_weekly_tasks(user_id: Optional[int] = None):
    """Get tasks for the current week (Monday to Sunday, inclusive)"""
    try:
        db = await get_db()
        # Use UTC for database comparison
        today = datetime.now(timezone.utc)
        # Find Monday of the current week
        start_of_week = today - timedelta(days=today.weekday())
        start_of_week = start_of_week.replace(
            hour=0, minute=0, second=0, microsecond=0)
        # Find Sunday of the current week
        end_of_week = start_of_week + \
            timedelta(days=6, hours=23, minutes=59,
                      seconds=59, microseconds=999999)

        # Convert to naive datetime for database comparison
        start_naive = start_of_week.replace(tzinfo=None)
        end_naive = end_of_week.replace(tzinfo=None)

        # Some databases store created_at as UTC, some as local/naive. Try both comparisons.
        query = select(Task).where(
            Task.created_at >= start_naive,
            Task.created_at <= end_naive
        )
        if user_id:
            query = query.where(Task.created_by == user_id)

        result = await db.execute(query)
        tasks = result.scalars().all()

        # If no tasks found, try with aware datetimes (for debugging)
        if not tasks:
            query2 = select(Task).where(
                Task.created_at >= start_of_week,
                Task.created_at <= end_of_week
            )
            if user_id:
                query2 = query2.where(Task.created_by == user_id)
            result2 = await db.execute(query2)
            tasks2 = result2.scalars().all()
            if tasks2:
                logger.debug("Found tasks with aware datetime comparison")
                tasks = tasks2
        for task in tasks:
            logger.debug(
                f"Task ID: {task.id}, Title: {task.title}, Created At: {task.created_at}, Created By: {task.created_by}")
        return tasks
    except Exception as e:
        logger.error(f"Error while fetching weekly tasks: {e}")
        raise e
    finally:
        await db.close()


async def get_monthly_tasks(user_id: Optional[int] = None):
    """Get tasks for the current month"""
    try:
        db = await get_db()
        # Use UTC for database comparison
        today = datetime.now(timezone.utc)
        # Get the first day of the current month
        start_of_month = today.replace(
            day=1, hour=0, minute=0, second=0, microsecond=0)
        # Get the first day of the next month, then subtract a microsecond for end of current month
        if today.month == 12:
            next_month = today.replace(
                year=today.year + 1, month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        else:
            next_month = today.replace(
                month=today.month + 1, day=1, hour=0, minute=0, second=0, microsecond=0)
        end_of_month = next_month - timedelta(microseconds=1)

        # Convert to naive datetime for database comparison
        start_naive = start_of_month.replace(tzinfo=None)
        end_naive = end_of_month.replace(tzinfo=None)

        query = select(Task).where(
            Task.created_at >= start_naive,
            Task.created_at <= end_naive
        )
        if user_id:
            query = query.where(Task.created_by == user_id)

        result = await db.execute(query)
        tasks = result.scalars().all()
        return tasks
    except Exception as e:
        logger.error(f"Error while fetching monthly tasks: {e}")
        raise e
    finally:
        await db.close()


async def get_current_month_tasks(user_id: Optional[int] = None) -> List[Task]:
    """Get tasks for the current month only (for kanban board)"""
    try:
        db = await get_db()
        # Use UTC for database comparison
        today = datetime.now(timezone.utc)
        # Get the first day of the current month
        start_of_month = today.replace(
            day=1, hour=0, minute=0, second=0, microsecond=0)
        # Get the first day of the next month, then subtract a microsecond for end of current month
        if today.month == 12:
            next_month = today.replace(
                year=today.year + 1, month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        else:
            next_month = today.replace(
                month=today.month + 1, day=1, hour=0, minute=0, second=0, microsecond=0)
        end_of_month = next_month - timedelta(microseconds=1)

        # Convert to naive datetime for database comparison
        start_naive = start_of_month.replace(tzinfo=None)
        end_naive = end_of_month.replace(tzinfo=None)

        query = select(Task).where(
            Task.created_at >= start_naive,
            Task.created_at <= end_naive
        )
        if user_id:
            query = query.where(Task.created_by == user_id)
        query = query.order_by(Task.created_at.desc())

        result = await db.execute(query)
        tasks = result.scalars().all()
        return tasks
    except Exception as e:
        logger.error(f"Error while fetching current month tasks: {e}")
        raise e
    finally:
        await db.close()


async def get_archived_tasks(user_id: Optional[int] = None) -> List[Task]:
    """Get tasks older than the current month (archived tasks)"""
    try:
        db = await get_db()
        # Use UTC for database comparison
        today = datetime.now(timezone.utc)
        # Get the first day of the current month
        start_of_month = today.replace(
            day=1, hour=0, minute=0, second=0, microsecond=0)

        # Convert to naive datetime for database comparison
        start_naive = start_of_month.replace(tzinfo=None)

        query = select(Task).where(Task.created_at < start_naive)
        if user_id:
            query = query.where(Task.created_by == user_id)
        query = query.order_by(Task.created_at.desc())

        result = await db.execute(query)
        tasks = result.scalars().all()
        return tasks
    except Exception as e:
        logger.error(f"Error while fetching archived tasks: {e}")
        raise e
    finally:
        await db.close()


async def get_task_statistics(user_id: Optional[int] = None):
    """Get task statistics for dashboard"""
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
            'total': len(all_tasks),
            'todo': len([t for t in all_tasks if t.status == 'todo']),
            'inprogress': len([t for t in all_tasks if t.status == 'inprogress']),
            'completed': len([t for t in all_tasks if t.status == 'completed']),
            'pending': len([t for t in all_tasks if t.status == 'pending']),
            'high_priority': len([t for t in all_tasks if t.priority == 'high']),
            'urgent': len([t for t in all_tasks if t.priority == 'urgent']),
            'overdue': len([t for t in all_tasks if t.due_date and safe_datetime_compare(ensure_timezone_aware(t.due_date), get_current_utc_datetime()) and t.status != 'completed']),
            'in_progress_category': len([t for t in all_tasks if t.category == 'in progress']),
            'accomplishments_category': len([t for t in all_tasks if t.category == 'accomplishments'])
        }

        return stats
    except Exception as e:
        logger.error(f"Error while fetching task statistics: {e}")
        raise e
    finally:
        await db.close()


async def get_tasks_with_status_changes(user_id: Optional[int] = None,
                                        from_date: datetime = None,
                                        to_date: datetime = None,
                                        old_status: str = None,
                                        new_status: str = None,
                                        old_category: str = None,
                                        new_category: str = None) -> List[Task]:
    """Get tasks that had specific status/category changes within a date range"""
    try:
        db = await get_db()

        # Build query to find tasks with status changes
        query = select(Task).join(TaskStatusHistory,
                                  Task.id == TaskStatusHistory.task_id)

        # Filter by user if provided
        if user_id:
            query = query.where(Task.created_by == user_id)

        # Filter by date range if provided
        if from_date:
            query = query.where(TaskStatusHistory.changed_at >= from_date)
        if to_date:
            query = query.where(TaskStatusHistory.changed_at <= to_date)

        # Filter by status changes if provided
        if old_status:
            query = query.where(TaskStatusHistory.old_status == old_status)
        if new_status:
            query = query.where(TaskStatusHistory.new_status == new_status)

        # Filter by category changes if provided
        if old_category:
            query = query.where(TaskStatusHistory.old_category == old_category)
        if new_category:
            query = query.where(TaskStatusHistory.new_category == new_category)

        # Distinct tasks (avoid duplicates if multiple status changes)
        query = query.distinct()

        result = await db.execute(query)
        tasks = result.scalars().all()
        return tasks
    except Exception as e:
        logger.error(f"Error while fetching tasks with status changes: {e}")
        raise e
    finally:
        await db.close()


async def get_tasks_for_weekly_report_enhanced(user_id: Optional[int] = None):
    """Get tasks for weekly report including status change tracking"""
    try:
        # Get current week tasks (created this week)
        current_week_tasks = await get_weekly_tasks(user_id)

        # Get date ranges for last week and this week
        today = datetime.now(timezone.utc)
        # Current week: Monday to Sunday
        start_of_week = today - timedelta(days=today.weekday())
        start_of_week = start_of_week.replace(
            hour=0, minute=0, second=0, microsecond=0)
        end_of_week = start_of_week + \
            timedelta(days=6, hours=23, minutes=59,
                      seconds=59, microseconds=999999)

        # Last week: Previous Monday to Sunday
        start_of_last_week = start_of_week - timedelta(days=7)
        end_of_last_week = start_of_week - timedelta(microseconds=1)

        # Get tasks that changed from "in progress" to "accomplishments" between last week and this week
        status_changed_tasks = await get_tasks_with_status_changes(
            user_id=user_id,
            from_date=start_of_last_week,
            to_date=end_of_week,
            old_category="in progress",
            new_category="accomplishments"
        )

        # Categorize current week tasks
        accomplishments = [
            task for task in current_week_tasks if task.category == "accomplishments"]
        in_progress = [
            task for task in current_week_tasks if task.category == "in progress"]

        # Add tasks that changed from in progress to accomplishments
        # These should appear in accomplishments for this week's report
        for task in status_changed_tasks:
            if task.category == "accomplishments" and task not in accomplishments:
                accomplishments.append(task)

        return {
            'accomplishments': accomplishments,
            'in_progress': in_progress,
            'status_changed_tasks': status_changed_tasks  # For reference
        }
    except Exception as e:
        logger.error(f"Error while fetching enhanced weekly report tasks: {e}")
        raise e
