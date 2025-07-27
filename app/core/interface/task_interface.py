from datetime import datetime, timedelta, timezone
from app.database.db_connector import get_db
from app.database.models import Task


async def create_task(task, category, status):
    try:
        db = await get_db()
        new_task = Task(task=task, category=category, status=status)
        db.add(new_task)
        await db.commit()
        await db.refresh(new_task)
        return new_task
    except Exception as e:
        print(f"Error while creating new task {e}")
        raise e
    finally:
        await db.close()


async def get_tasks():
    try:
        db = await get_db()
        tasks = await db.execute(
            Task.__table__.select()
        )
        return tasks.fetchall()
    except Exception as e:
        print(f"Error while fetching tasks: {e}")
        raise e
    finally:
        await db.close()


async def get_weekly_tasks():

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

        query = Task.__table__.select().where(
            Task.created_at >= start_of_week,
            Task.created_at <= end_of_week
        )
        tasks = await db.execute(query)
        return tasks.fetchall()
    except Exception as e:
        print(f"Error while fetching weekly tasks: {e}")
        raise e
    finally:
        await db.close()


async def get_monthly_tasks():
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

        query = Task.__table__.select().where(
            Task.created_at >= start_of_month,
            Task.created_at <= end_of_month
        )
        tasks = await db.execute(query)
        return tasks.fetchall()
    except Exception as e:
        print(f"Error while fetching monthly tasks: {e}")
        raise e
    finally:
        await db.close()


async def get_task(task_id):
    try:
        db = await get_db()
        task = await db.get(Task, task_id)
        return task
    except Exception as e:
        print(f"Error while fetching task: {e}")
        raise e
    finally:
        await db.close()


async def update_task(task_id, task, category, status):
    try:
        db = await get_db()
        task = await get_task(task_id)
        task.task = task
        task.category = category
        task.status = status
        await db.commit()
        await db.refresh(task)
        return task
    except Exception as e:
        print(f"Error while updating task {e}")
        raise e
    finally:
        await db.close()
