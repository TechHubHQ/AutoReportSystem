"""
Datetime utility functions for handling timezone-aware and timezone-naive datetime objects

This module provides utilities to safely compare and manipulate datetime objects
that may have different timezone awareness.
"""

from datetime import datetime, timezone
from typing import Optional


def ensure_timezone_aware(dt: Optional[datetime]) -> Optional[datetime]:
    """
    Ensure a datetime object is timezone-aware.
    If it's naive, assume it's UTC.
    
    Args:
        dt: Datetime object that may be timezone-aware or naive
        
    Returns:
        Timezone-aware datetime object or None if input is None
    """
    if dt is None:
        return None
    
    if dt.tzinfo is None:
        # Assume naive datetime is UTC
        return dt.replace(tzinfo=timezone.utc)
    
    return dt


def ensure_timezone_naive(dt: Optional[datetime]) -> Optional[datetime]:
    """
    Ensure a datetime object is timezone-naive.
    If it's timezone-aware, convert to UTC and remove timezone info.
    
    Args:
        dt: Datetime object that may be timezone-aware or naive
        
    Returns:
        Timezone-naive datetime object or None if input is None
    """
    if dt is None:
        return None
    
    if dt.tzinfo is not None:
        # Convert to UTC and remove timezone info
        return dt.astimezone(timezone.utc).replace(tzinfo=None)
    
    return dt


def safe_datetime_compare(dt1: Optional[datetime], dt2: Optional[datetime]) -> bool:
    """
    Safely compare two datetime objects that may have different timezone awareness.
    
    Args:
        dt1: First datetime object
        dt2: Second datetime object
        
    Returns:
        True if dt1 < dt2, False otherwise
    """
    if dt1 is None or dt2 is None:
        return False
    
    # Ensure both datetimes are timezone-aware for comparison
    dt1_aware = ensure_timezone_aware(dt1)
    dt2_aware = ensure_timezone_aware(dt2)
    
    return dt1_aware < dt2_aware


def get_current_utc_datetime() -> datetime:
    """
    Get current UTC datetime that is timezone-aware.
    
    Returns:
        Current UTC datetime with timezone info
    """
    return datetime.now(timezone.utc)


def format_datetime_for_display(dt: Optional[datetime], format_str: str = "%Y-%m-%d %H:%M") -> str:
    """
    Format datetime for display, handling timezone-aware and naive datetimes.
    
    Args:
        dt: Datetime object to format
        format_str: Format string for strftime
        
    Returns:
        Formatted datetime string or "Not set" if dt is None
    """
    if dt is None:
        return "Not set"
    
    # Ensure timezone-aware for consistent formatting
    dt_aware = ensure_timezone_aware(dt)
    return dt_aware.strftime(format_str)


def is_overdue(due_date: Optional[datetime], current_time: Optional[datetime] = None) -> bool:
    """
    Check if a task is overdue by comparing due date with current time.
    
    Args:
        due_date: Task due date
        current_time: Current time (defaults to now if None)
        
    Returns:
        True if task is overdue, False otherwise
    """
    if due_date is None:
        return False
    
    if current_time is None:
        current_time = get_current_utc_datetime()
    
    return safe_datetime_compare(due_date, current_time)


def is_due_soon(due_date: Optional[datetime], days_ahead: int = 3, current_time: Optional[datetime] = None) -> bool:
    """
    Check if a task is due soon (within specified days).
    
    Args:
        due_date: Task due date
        days_ahead: Number of days to consider as "soon"
        current_time: Current time (defaults to now if None)
        
    Returns:
        True if task is due soon, False otherwise
    """
    if due_date is None:
        return False
    
    if current_time is None:
        current_time = get_current_utc_datetime()
    
    # Add days to current time for comparison
    from datetime import timedelta
    future_time = current_time + timedelta(days=days_ahead)
    
    # Task is due soon if due_date is between now and future_time
    return (safe_datetime_compare(current_time, due_date) and 
            safe_datetime_compare(due_date, future_time))


def get_due_date_status(due_date: Optional[datetime], task_status: str = "") -> str:
    """
    Get the status of a due date (overdue, due-soon, or normal).
    
    Args:
        due_date: Task due date
        task_status: Current task status
        
    Returns:
        String indicating due date status: "overdue", "due-soon", or ""
    """
    if due_date is None:
        return ""
    
    # Don't mark completed tasks as overdue
    if task_status == "completed":
        return ""
    
    current_time = get_current_utc_datetime()
    
    if is_overdue(due_date, current_time):
        return "overdue"
    elif is_due_soon(due_date, days_ahead=3, current_time=current_time):
        return "due-soon"
    
    return ""