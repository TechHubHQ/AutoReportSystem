from datetime import date, datetime
from typing import List, Optional
from sqlalchemy import select, update, delete
from app.database.db_connector import get_db
from app.database.models import TaskNote
from app.core.utils.datetime_utils import get_current_utc_datetime
from app.config.logging_config import get_logger

logger = get_logger(__name__)


async def create_task_note(task_id: int, note_date: date, issue_description: str,
                           timeline_content: str = None, analysis_content: str = None, 
                           resolution_notes: str = None, created_by: int = None) -> TaskNote:
    """Create a new task note for a specific date - saves directly to database"""
    db = None
    try:
        db = await get_db()

        # Check if a note already exists for this task on this date
        existing_note = await get_task_note_by_date(task_id, note_date)
        if existing_note:
            raise Exception(
                f"A note already exists for task {task_id} on {note_date}. Please update the existing note instead.")

        new_note = TaskNote(
            task_id=task_id,
            note_date=note_date,
            issue_description=issue_description,
            timeline_content=timeline_content,
            analysis_content=analysis_content,
            resolution_notes=resolution_notes,
            created_by=created_by
        )

        db.add(new_note)
        await db.commit()
        await db.refresh(new_note)

        logger.info(f"Successfully created task note for task {task_id} on {note_date} - saved directly")
        return new_note
    except Exception as e:
        logger.error(f"Error while creating task note: {e}")
        if db:
            await db.rollback()
        raise e
    finally:
        if db:
            await db.close()


async def get_task_notes(task_id: int) -> List[TaskNote]:
    """Get all notes for a specific task, ordered by date (newest first)"""
    try:
        db = await get_db()
        query = select(TaskNote).where(TaskNote.task_id ==
                                       task_id).order_by(TaskNote.note_date.desc())

        result = await db.execute(query)
        notes = result.scalars().all()
        return notes
    except Exception as e:
        logger.error(f"Error while fetching task notes: {e}")
        raise e
    finally:
        await db.close()


async def get_task_note_by_date(task_id: int, note_date: date) -> Optional[TaskNote]:
    """Get a specific note for a task on a specific date"""
    try:
        db = await get_db()
        query = select(TaskNote).where(
            TaskNote.task_id == task_id,
            TaskNote.note_date == note_date
        )

        result = await db.execute(query)
        note = result.scalar_one_or_none()
        return note
    except Exception as e:
        logger.error(f"Error while fetching task note by date: {e}")
        raise e
    finally:
        await db.close()


async def get_task_note_by_id(note_id: int) -> Optional[TaskNote]:
    """Get a specific note by ID"""
    try:
        db = await get_db()
        query = select(TaskNote).where(TaskNote.id == note_id)

        result = await db.execute(query)
        note = result.scalar_one_or_none()
        return note
    except Exception as e:
        logger.error(f"Error while fetching task note by ID: {e}")
        raise e
    finally:
        await db.close()


async def update_task_note(note_id: int, issue_description: str = None,
                           timeline_content: str = None, analysis_content: str = None, 
                           resolution_notes: str = None) -> TaskNote:
    """Update an existing task note - saves directly to database"""
    db = None
    try:
        db = await get_db()

        # First, get the current note to verify it exists and get its data
        query_select = select(TaskNote).where(TaskNote.id == note_id)
        result = await db.execute(query_select)
        current_note = result.scalar_one_or_none()
        
        if not current_note:
            raise Exception(f"Task note {note_id} not found")

        # Build update dictionary with only provided values
        update_data = {}
        if issue_description is not None:
            update_data['issue_description'] = issue_description
        if timeline_content is not None:
            update_data['timeline_content'] = timeline_content
        if analysis_content is not None:
            update_data['analysis_content'] = analysis_content
        if resolution_notes is not None:
            update_data['resolution_notes'] = resolution_notes

        update_data['updated_at'] = get_current_utc_datetime()

        # Update the note
        query_update = update(TaskNote).where(
            TaskNote.id == note_id).values(**update_data)
        await db.execute(query_update)
        await db.commit()

        logger.info(f"Successfully updated task note {note_id} - saved directly")
        
        # Create updated note object to return (avoid additional DB call)
        updated_note = TaskNote(
            id=current_note.id,
            task_id=current_note.task_id,
            note_date=current_note.note_date,
            issue_description=update_data.get('issue_description', current_note.issue_description),
            timeline_content=update_data.get('timeline_content', current_note.timeline_content),
            analysis_content=update_data.get('analysis_content', current_note.analysis_content),
            resolution_notes=update_data.get('resolution_notes', current_note.resolution_notes),
            created_by=current_note.created_by,
            created_at=current_note.created_at,
            updated_at=update_data['updated_at']
        )
        
        return updated_note
    except Exception as e:
        logger.error(f"Error while updating task note {note_id}: {e}")
        if db:
            await db.rollback()
        raise e
    finally:
        if db:
            await db.close()


async def delete_task_note(note_id: int) -> bool:
    """Delete a task note - saves directly to database"""
    db = None
    try:
        db = await get_db()
        query = delete(TaskNote).where(TaskNote.id == note_id)
        result = await db.execute(query)
        await db.commit()

        logger.info(f"Successfully deleted task note {note_id} - saved directly")
        return result.rowcount > 0
    except Exception as e:
        logger.error(f"Error while deleting task note: {e}")
        if db:
            await db.rollback()
        raise e
    finally:
        if db:
            await db.close()


async def get_notes_by_date_range(task_id: int, start_date: date, end_date: date) -> List[TaskNote]:
    """Get notes for a task within a specific date range"""
    try:
        db = await get_db()
        query = select(TaskNote).where(
            TaskNote.task_id == task_id,
            TaskNote.note_date >= start_date,
            TaskNote.note_date <= end_date
        ).order_by(TaskNote.note_date.desc())

        result = await db.execute(query)
        notes = result.scalars().all()
        return notes
    except Exception as e:
        logger.error(f"Error while fetching notes by date range: {e}")
        raise e
    finally:
        await db.close()


async def get_recent_notes(task_id: int, limit: int = 5) -> List[TaskNote]:
    """Get the most recent notes for a task"""
    try:
        db = await get_db()
        query = select(TaskNote).where(TaskNote.task_id == task_id).order_by(
            TaskNote.note_date.desc()
        ).limit(limit)

        result = await db.execute(query)
        notes = result.scalars().all()
        return notes
    except Exception as e:
        logger.error(f"Error while fetching recent notes: {e}")
        raise e
    finally:
        await db.close()


async def get_notes_with_resolution(task_id: int) -> List[TaskNote]:
    """Get notes that have resolution information"""
    try:
        db = await get_db()
        query = select(TaskNote).where(
            TaskNote.task_id == task_id,
            TaskNote.resolution_notes.isnot(None),
            TaskNote.resolution_notes != ""
        ).order_by(TaskNote.note_date.desc())

        result = await db.execute(query)
        notes = result.scalars().all()
        return notes
    except Exception as e:
        logger.error(f"Error while fetching notes with resolution: {e}")
        raise e
    finally:
        await db.close()


async def create_task_issue(task_id: int, issue_description: str, created_by: int = None) -> TaskNote:
    """Create or update the main issue description for a task - saves directly to database"""
    db = None
    try:
        db = await get_db()

        # Check if an issue note already exists (using a special date)
        issue_date = date(1900, 1, 1)  # Special date for issue notes
        existing_issue = await get_task_note_by_date(task_id, issue_date)

        if existing_issue:
            # Update existing issue
            logger.info(f"Updating existing task issue for task {task_id} - saved directly")
            return await update_task_note(
                existing_issue.id,
                issue_description=issue_description
            )
        else:
            # Create new issue note
            new_issue = TaskNote(
                task_id=task_id,
                note_date=issue_date,
                issue_description=issue_description,
                timeline_content=None,
                analysis_content="Task issue description",
                resolution_notes=None,
                created_by=created_by
            )

            db.add(new_issue)
            await db.commit()
            await db.refresh(new_issue)
            logger.info(f"Created new task issue for task {task_id} - saved directly")
            return new_issue

    except Exception as e:
        logger.error(f"Error while creating/updating task issue: {e}")
        if db:
            await db.rollback()
        raise e
    finally:
        if db:
            await db.close()


async def create_task_resolution(task_id: int, resolution_notes: str, created_by: int = None) -> TaskNote:
    """Create or update the resolution notes for a task - saves directly to database"""
    db = None
    try:
        db = await get_db()

        # Check if a resolution note already exists (using a special date)
        # Special date for resolution notes
        resolution_date = date(2100, 12, 31)
        existing_resolution = await get_task_note_by_date(task_id, resolution_date)

        if existing_resolution:
            # Update existing resolution
            logger.info(f"Updating existing task resolution for task {task_id} - saved directly")
            return await update_task_note(
                existing_resolution.id,
                resolution_notes=resolution_notes
            )
        else:
            # Create new resolution note
            new_resolution = TaskNote(
                task_id=task_id,
                note_date=resolution_date,
                issue_description="Task resolution",
                timeline_content=None,
                analysis_content="Task resolution notes",
                resolution_notes=resolution_notes,
                created_by=created_by
            )

            db.add(new_resolution)
            await db.commit()
            await db.refresh(new_resolution)
            logger.info(f"Created new task resolution for task {task_id} - saved directly")
            return new_resolution

    except Exception as e:
        logger.error(f"Error while creating/updating task resolution: {e}")
        if db:
            await db.rollback()
        raise e
    finally:
        if db:
            await db.close()


async def get_task_issue(task_id: int) -> Optional[TaskNote]:
    """Get the main issue description for a task"""
    try:
        issue_date = date(1900, 1, 1)  # Special date for issue notes
        return await get_task_note_by_date(task_id, issue_date)
    except Exception as e:
        logger.error(f"Error while fetching task issue: {e}")
        return None


async def get_task_resolution(task_id: int) -> Optional[TaskNote]:
    """Get the resolution notes for a task"""
    try:
        # Special date for resolution notes
        resolution_date = date(2100, 12, 31)
        return await get_task_note_by_date(task_id, resolution_date)
    except Exception as e:
        logger.error(f"Error while fetching task resolution: {e}")
        return None


async def get_task_progress_notes(task_id: int) -> List[TaskNote]:
    """Get only the progress notes for a task (excluding issue and resolution)"""
    try:
        db = await get_db()
        issue_date = date(1900, 1, 1)
        resolution_date = date(2100, 12, 31)

        query = select(TaskNote).where(
            TaskNote.task_id == task_id,
            TaskNote.note_date != issue_date,
            TaskNote.note_date != resolution_date
        ).order_by(TaskNote.note_date.desc())

        result = await db.execute(query)
        notes = result.scalars().all()
        return notes
    except Exception as e:
        logger.error(f"Error while fetching task progress notes: {e}")
        raise e
    finally:
        await db.close()
