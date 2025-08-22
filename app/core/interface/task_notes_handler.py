"""
Direct task notes operations that save immediately without session state dependency.
This module provides async functions that can be called directly from UI components
to perform task notes operations with immediate database persistence.
"""

import asyncio
from datetime import date
from typing import List, Optional
from app.core.interface.task_notes_interface import (
    create_task_note, update_task_note, delete_task_note,
    create_task_issue, create_task_resolution,
    get_task_notes, get_task_issue, get_task_resolution, get_task_progress_notes
)
from app.config.logging_config import get_logger

logger = get_logger(__name__)


async def create_progress_note_direct(task_id: int, note_date: date, timeline_content: str = None, analysis_content: str = None, created_by: int = None) -> dict:
    """
    Create a progress note directly and return result with status.

    Args:
        task_id: ID of the task
        note_date: Date for the note
        timeline_content: Daily actions and activities
        analysis_content: Detailed analysis content
        created_by: User ID who created the note

    Returns:
        dict: {'success': bool, 'message': str, 'note': TaskNote or None}
    """
    try:
        # Create the note with a descriptive issue description
        issue_description = f"Daily progress for {note_date.strftime('%B %d, %Y')}"

        note = await create_task_note(
            task_id=task_id,
            note_date=note_date,
            issue_description=issue_description,
            timeline_content=timeline_content,
            analysis_content=analysis_content,
            resolution_notes=None,
            created_by=created_by
        )

        logger.info(
            f"Successfully created progress note for task {task_id} on {note_date}")
        return {
            'success': True,
            'message': 'Progress note created successfully!',
            'note': note
        }

    except Exception as e:
        error_msg = str(e)
        logger.error(
            f"Failed to create progress note for task {task_id}: {error_msg}")
        return {
            'success': False,
            'message': f'Error creating note: {error_msg}',
            'note': None
        }


async def update_progress_note_direct(note_id: int, timeline_content: str = None, analysis_content: str = None) -> dict:
    """
    Update a progress note directly and return result with status.

    Args:
        note_id: ID of the note to update
        timeline_content: New timeline content
        analysis_content: New analysis content

    Returns:
        dict: {'success': bool, 'message': str, 'note': TaskNote or None}
    """
    try:
        logger.info(f"Starting update of progress note {note_id}")
        
        if not timeline_content and not analysis_content:
            return {
                'success': False,
                'message': 'At least one of timeline or analysis content must be provided',
                'note': None
            }
        
        note = await update_task_note(
            note_id=note_id,
            timeline_content=timeline_content.strip() if timeline_content else None,
            analysis_content=analysis_content.strip() if analysis_content else None
        )

        logger.info(f"Successfully updated progress note {note_id}")
        return {
            'success': True,
            'message': 'Progress note updated successfully!',
            'note': note
        }

    except Exception as e:
        error_msg = str(e)
        logger.error(f"Failed to update progress note {note_id}: {error_msg}", exc_info=True)
        return {
            'success': False,
            'message': f'Error updating note: {error_msg}',
            'note': None
        }


async def delete_progress_note_direct(note_id: int) -> dict:
    """
    Delete a progress note directly and return result with status.

    Args:
        note_id: ID of the note to delete

    Returns:
        dict: {'success': bool, 'message': str}
    """
    try:
        success = await delete_task_note(note_id)

        if success:
            logger.info(f"Successfully deleted progress note {note_id}")
            return {
                'success': True,
                'message': 'Progress note deleted successfully!'
            }
        else:
            return {
                'success': False,
                'message': 'Note not found or already deleted'
            }

    except Exception as e:
        error_msg = str(e)
        logger.error(f"Failed to delete progress note {note_id}: {error_msg}")
        return {
            'success': False,
            'message': f'Error deleting note: {error_msg}'
        }


async def create_or_update_issue_direct(task_id: int, issue_description: str, created_by: int = None) -> dict:
    """
    Create or update task issue directly and return result with status.

    Args:
        task_id: ID of the task
        issue_description: Issue description content
        created_by: User ID who created/updated the issue

    Returns:
        dict: {'success': bool, 'message': str, 'issue': TaskNote or None}
    """
    try:
        issue = await create_task_issue(
            task_id=task_id,
            issue_description=issue_description,
            created_by=created_by
        )

        logger.info(f"Successfully created/updated issue for task {task_id}")
        return {
            'success': True,
            'message': 'Issue description saved successfully!',
            'issue': issue
        }

    except Exception as e:
        error_msg = str(e)
        logger.error(
            f"Failed to create/update issue for task {task_id}: {error_msg}")
        return {
            'success': False,
            'message': f'Error saving issue: {error_msg}',
            'issue': None
        }


async def create_or_update_resolution_direct(task_id: int, resolution_notes: str, created_by: int = None) -> dict:
    """
    Create or update task resolution directly and return result with status.

    Args:
        task_id: ID of the task
        resolution_notes: Resolution notes content
        created_by: User ID who created/updated the resolution

    Returns:
        dict: {'success': bool, 'message': str, 'resolution': TaskNote or None}
    """
    try:
        resolution = await create_task_resolution(
            task_id=task_id,
            resolution_notes=resolution_notes,
            created_by=created_by
        )

        logger.info(
            f"Successfully created/updated resolution for task {task_id}")
        return {
            'success': True,
            'message': 'Resolution notes saved successfully!',
            'resolution': resolution
        }

    except Exception as e:
        error_msg = str(e)
        logger.error(
            f"Failed to create/update resolution for task {task_id}: {error_msg}")
        return {
            'success': False,
            'message': f'Error saving resolution: {error_msg}',
            'resolution': None
        }


async def get_task_notes_data_direct(task_id: int) -> dict:
    """
    Get all task notes data (progress notes, issue, resolution) directly.

    Args:
        task_id: ID of the task

    Returns:
        dict: {
            'success': bool,
            'message': str,
            'progress_notes': List[TaskNote],
            'issue': TaskNote or None,
            'resolution': TaskNote or None
        }
    """
    try:
        # Get all data concurrently
        progress_notes_task = get_task_progress_notes(task_id)
        issue_task = get_task_issue(task_id)
        resolution_task = get_task_resolution(task_id)

        progress_notes, issue, resolution = await asyncio.gather(
            progress_notes_task, issue_task, resolution_task,
            return_exceptions=True
        )

        # Handle any exceptions
        if isinstance(progress_notes, Exception):
            logger.error(
                f"Error getting progress notes for task {task_id}: {progress_notes}")
            progress_notes = []

        if isinstance(issue, Exception):
            logger.error(f"Error getting issue for task {task_id}: {issue}")
            issue = None

        if isinstance(resolution, Exception):
            logger.error(
                f"Error getting resolution for task {task_id}: {resolution}")
            resolution = None

        logger.info(
            f"Successfully retrieved task notes data for task {task_id}")
        return {
            'success': True,
            'message': 'Task notes data retrieved successfully',
            'progress_notes': progress_notes or [],
            'issue': issue,
            'resolution': resolution
        }

    except Exception as e:
        error_msg = str(e)
        logger.error(
            f"Failed to get task notes data for task {task_id}: {error_msg}")
        return {
            'success': False,
            'message': f'Error retrieving task notes: {error_msg}',
            'progress_notes': [],
            'issue': None,
            'resolution': None
        }


def run_async_operation(coro):
    """
    Improved helper function to run async operations from sync context.
    This is useful for Streamlit components that need to call async functions.

    Args:
        coro: Coroutine to run

    Returns:
        Result of the coroutine
    """
    try:
        # Check if we're in an async context
        try:
            loop = asyncio.get_running_loop()
            # We're in an async context, use thread executor
            import concurrent.futures
            import threading
            
            def run_in_thread():
                # Create a new event loop for this thread
                new_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(new_loop)
                try:
                    return new_loop.run_until_complete(coro)
                finally:
                    new_loop.close()
            
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(run_in_thread)
                return future.result(timeout=30)  # 30 second timeout
                
        except RuntimeError:
            # No running loop, we can run directly
            return asyncio.run(coro)
            
    except Exception as e:
        logger.error(f"Error in run_async_operation: {e}", exc_info=True)
        raise e


# Convenience sync wrappers for Streamlit usage
def create_progress_note_sync(task_id: int, note_date: date, timeline_content: str = None, analysis_content: str = None, created_by: int = None) -> dict:
    """Sync wrapper for create_progress_note_direct"""
    return run_async_operation(create_progress_note_direct(task_id, note_date, timeline_content, analysis_content, created_by))


def update_progress_note_sync(note_id: int, timeline_content: str = None, analysis_content: str = None) -> dict:
    """Sync wrapper for update_progress_note_direct"""
    return run_async_operation(update_progress_note_direct(note_id, timeline_content, analysis_content))


def delete_progress_note_sync(note_id: int) -> dict:
    """Sync wrapper for delete_progress_note_direct"""
    return run_async_operation(delete_progress_note_direct(note_id))


def create_or_update_issue_sync(task_id: int, issue_description: str, created_by: int = None) -> dict:
    """Sync wrapper for create_or_update_issue_direct"""
    return run_async_operation(create_or_update_issue_direct(task_id, issue_description, created_by))


def create_or_update_resolution_sync(task_id: int, resolution_notes: str, created_by: int = None) -> dict:
    """Sync wrapper for create_or_update_resolution_direct"""
    return run_async_operation(create_or_update_resolution_direct(task_id, resolution_notes, created_by))


def get_task_notes_data_sync(task_id: int) -> dict:
    """Sync wrapper for get_task_notes_data_direct"""
    return run_async_operation(get_task_notes_data_direct(task_id))