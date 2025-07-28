from datetime import datetime, timedelta, timezone
from typing import List, Optional
from sqlalchemy import select, update, delete
from app.database.db_connector import get_db
from app.database.models import Task


async def create_task(title: str, description: str = "", status: str = "todo", 
                     priority: str = "medium", category: str = "general", 
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
        return new_task
    except Exception as e:
        print(f"Error while creating new task: {e}")
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
        print(f"Error while fetching tasks: {e}")
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
        print(f"Error while fetching tasks by status: {e}")
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
        print(f"Error while fetching task: {e}")
        raise e
    finally:
        await db.close()


async def update_task(task_id: int, title: str = None, description: str = None, 
                     status: str = None, priority: str = None, category: str = None,
                     due_date: datetime = None):
    """Update an existing task"""
    try:
        db = await get_db()
        
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
        
        update_data['updated_at'] = datetime.now(timezone.utc)
        
        query = update(Task).where(Task.id == task_id).values(**update_data)
        await db.execute(query)
        await db.commit()
        
        # Return updated task
        return await get_task(task_id)
    except Exception as e:
        print(f"Error while updating task: {e}")
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
        print(f"Error while deleting task: {e}")
        await db.rollback()
        raise e
    finally:
        await db.close()


async def get_weekly_tasks(user_id: Optional[int] = None):
    """Get tasks for the current week"""
    try:
        db = await get_db()
        ist = timezone(timedelta(hours=5, minutes=30))
        today = datetime.now(ist)
        # Find Monday of the current week
        start_of_week = today - timedelta(days=today.weekday())
        start_of_week = start_of_week.replace(
            hour=0, minute=0, second=0, microsecond=0)
        # Find Friday of the current week
        end_of_week = start_of_week + \
            timedelta(days=4, hours=23, minutes=59,
                      seconds=59, microseconds=999999)

        query = select(Task).where(
            Task.created_at >= start_of_week,
            Task.created_at <= end_of_week
        )
        if user_id:
            query = query.where(Task.created_by == user_id)
        
        result = await db.execute(query)
        tasks = result.scalars().all()
        return tasks
    except Exception as e:
        print(f"Error while fetching weekly tasks: {e}")
        raise e
    finally:
        await db.close()


async def get_monthly_tasks(user_id: Optional[int] = None):
    """Get tasks for the current month"""
    try:
        db = await get_db()
        ist = timezone(timedelta(hours=5, minutes=30))
        today = datetime.now(ist)
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

        query = select(Task).where(
            Task.created_at >= start_of_month,
            Task.created_at <= end_of_month
        )
        if user_id:
            query = query.where(Task.created_by == user_id)
        
        result = await db.execute(query)
        tasks = result.scalars().all()
        return tasks
    except Exception as e:
        print(f"Error while fetching monthly tasks: {e}")
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
            'overdue': len([t for t in all_tasks if t.due_date and t.due_date < datetime.now(timezone.utc) and t.status != 'completed'])
        }
        
        return stats
    except Exception as e:
        print(f"Error while fetching task statistics: {e}")
        raise e
    finally:
        await db.close()