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
