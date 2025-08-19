"""
Utility functions for determining task colors based on due dates and status
"""
from datetime import datetime, timezone, timedelta
from typing import Tuple, Optional


def get_due_date_color(due_date: Optional[datetime]) -> Tuple[str, str]:
    """
    Get color and description based on due date

    Returns:
        Tuple of (color_class, description)
        - Red: Due today or overdue
        - Orange: Due within 1 day
        - Green: Due in more than 2 days
        - Blue: No due date
    """
    if not due_date:
        return "due-none", "No due date"

    # Ensure due_date is timezone aware
    if due_date.tzinfo is None:
        due_date = due_date.replace(tzinfo=timezone.utc)

    now = datetime.now(timezone.utc)
    today = now.date()
    due_date_only = due_date.date()

    days_until_due = (due_date_only - today).days

    if days_until_due < 0:
        return "due-overdue", f"Overdue by {abs(days_until_due)} day(s)"
    elif days_until_due == 0:
        return "due-today", "Due today"
    elif days_until_due == 1:
        return "due-tomorrow", "Due tomorrow"
    elif days_until_due <= 2:
        return "due-soon", f"Due in {days_until_due} day(s)"
    else:
        return "due-later", f"Due in {days_until_due} day(s)"


def get_status_color(status: str) -> Tuple[str, str]:
    """
    Get color and description based on task status

    Status meanings:
    - todo: Tasks to be started (Blue)
    - inprogress: Tasks currently being worked on (Purple)
    - pending: Tasks on hold/waiting for something (Orange/Yellow)
    - completed: Finished tasks (Green)

    Returns:
        Tuple of (color_class, description)
    """
    status_colors = {
        "todo": ("status-todo", "To Do"),
        "inprogress": ("status-inprogress", "In Progress"),
        "pending": ("status-pending", "On Hold"),  # Pending = On Hold
        "completed": ("status-completed", "Completed")
    }

    return status_colors.get(status, ("status-unknown", "Unknown"))


def get_priority_color(priority: str) -> Tuple[str, str]:
    """
    Get color and description based on task priority

    Returns:
        Tuple of (color_class, description)
    """
    priority_colors = {
        "low": ("priority-low", "Low Priority"),
        "medium": ("priority-medium", "Medium Priority"),
        "high": ("priority-high", "High Priority"),
        "urgent": ("priority-urgent", "Urgent Priority")
    }

    return priority_colors.get(priority, ("priority-medium", "Medium Priority"))


def get_combined_task_color(due_date: Optional[datetime], status: str, priority: str) -> dict:
    """
    Get combined color information for a task based on due date, status, and priority

    New Color Scheme Rules:
    - TODO tasks: Green+Blue (far away), Orange+Blue (2 days), Red+Blue (overdue)
    - IN PROGRESS tasks: Green+Purple (far away), Orange+Purple (2 days), Red+Purple (overdue)
    - PENDING tasks: Always Orange double border
    - COMPLETED tasks: Always green (no change)

    Returns:
        Dictionary with color classes and descriptions
    """
    due_color, due_desc = get_due_date_color(due_date)
    status_color, status_desc = get_status_color(status)
    priority_color, priority_desc = get_priority_color(priority)

    # Determine combined color based on new scheme
    if status == "completed":
        # Completed tasks are always green
        primary_color = "status-completed"
        combined_class = "status-completed"
        due_color = "due-completed"
        due_desc = "Completed"
    elif status == "pending":
        # Pending tasks always have orange double border
        primary_color = "status-pending"
        combined_class = "status-pending"
    else:
        # For TODO and IN PROGRESS, combine due date urgency with status
        if due_color == "due-overdue":
            # Red + Blue (TODO) or Red + Purple (IN PROGRESS)
            if status == "todo":
                combined_class = "due-overdue status-todo"
            else:  # inprogress
                combined_class = "due-overdue status-inprogress"
        elif due_color in ["due-today", "due-tomorrow"]:
            # Orange + Blue (TODO) or Orange + Purple (IN PROGRESS)
            if status == "todo":
                combined_class = "due-urgent status-todo"
            else:  # inprogress
                combined_class = "due-urgent status-inprogress"
        else:
            # Green + Blue (TODO) or Green + Purple (IN PROGRESS) for far away dates
            if status == "todo":
                combined_class = "due-safe status-todo"
            else:  # inprogress
                combined_class = "due-safe status-inprogress"

        primary_color = combined_class

    return {
        "due_color": due_color,
        "due_description": due_desc,
        "status_color": status_color,
        "status_description": status_desc,
        "priority_color": priority_color,
        "priority_description": priority_desc,
        "primary_color": primary_color,
        "all_classes": combined_class if 'combined_class' in locals() else f"{due_color} {status_color} {priority_color}"
    }


def format_date_display(date_obj: Optional[datetime], include_time: bool = False) -> str:
    """
    Format datetime for display in UI

    Args:
        date_obj: DateTime object to format
        include_time: Whether to include time in the display

    Returns:
        Formatted date string
    """
    if not date_obj:
        return "Not set"

    # Ensure timezone awareness
    if date_obj.tzinfo is None:
        date_obj = date_obj.replace(tzinfo=timezone.utc)

    if include_time:
        return date_obj.strftime("%Y-%m-%d %H:%M")
    else:
        return date_obj.strftime("%Y-%m-%d")


def get_days_until_due(due_date: Optional[datetime]) -> Optional[int]:
    """
    Get number of days until due date

    Returns:
        Number of days (negative if overdue, None if no due date)
    """
    if not due_date:
        return None

    # Ensure due_date is timezone aware
    if due_date.tzinfo is None:
        due_date = due_date.replace(tzinfo=timezone.utc)

    now = datetime.now(timezone.utc)
    today = now.date()
    due_date_only = due_date.date()

    return (due_date_only - today).days


def get_completion_date_display(task_status: str, updated_at: Optional[datetime]) -> str:
    """
    Get completion date display for completed tasks

    Args:
        task_status: Current task status
        updated_at: Last updated timestamp (used as completion date for completed tasks)

    Returns:
        Formatted completion date string or empty string for non-completed tasks
    """
    if task_status != "completed" or not updated_at:
        return ""

    # Ensure timezone awareness
    if updated_at.tzinfo is None:
        updated_at = updated_at.replace(tzinfo=timezone.utc)

    return f"Completed: {format_date_display(updated_at)}"
