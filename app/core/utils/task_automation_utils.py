"""
Utility functions for task automation features.

This module provides helper functions for automatic task categorization
and related automation features.
"""

from typing import Optional, Dict, Any
from datetime import datetime
from app.config.logging_config import get_logger

logger = get_logger(__name__)


def log_automatic_category_change(task_id: int, old_category: str, new_category: str,
                                  trigger_status: str, user_id: Optional[int] = None):
    """
    Log automatic category changes for audit and notification purposes.

    Args:
        task_id: ID of the task that was changed
        old_category: Previous category
        new_category: New category
        trigger_status: The status change that triggered the category change
        user_id: ID of the user who triggered the change
    """
    logger.info(
        f"Automatic category change - Task {task_id}: "
        f"'{old_category}' → '{new_category}' (triggered by status: '{trigger_status}', user: {user_id})"
    )


def should_auto_categorize_to_accomplishments(current_status: str, new_status: str) -> bool:
    """
    Determine if a task should be automatically moved to accomplishments category.

    Args:
        current_status: Current task status
        new_status: New task status being set

    Returns:
        True if task should be moved to accomplishments
    """
    return new_status == "completed" and current_status != "completed"


def should_auto_categorize_to_in_progress(current_status: str, new_status: str) -> bool:
    """
    Determine if a task should be automatically moved to in progress category.

    Args:
        current_status: Current task status
        new_status: New task status being set

    Returns:
        True if task should be moved to in progress
    """
    return (new_status is not None and
            new_status != "completed" and
            current_status == "completed")


def get_automatic_category_for_status(status: str, current_category: str) -> Optional[str]:
    """
    Get the automatic category that should be set for a given status.

    Args:
        status: The task status
        current_category: Current category of the task

    Returns:
        The category that should be automatically set, or None if no change needed
    """
    if status == "completed":
        return "accomplishments"
    elif status in ["todo", "inprogress", "pending"] and current_category == "accomplishments":
        return "in progress"
    return None


def create_task_automation_summary(task_changes: Dict[str, Any]) -> str:
    """
    Create a human-readable summary of automatic task changes.

    Args:
        task_changes: Dictionary containing the changes made to the task

    Returns:
        A formatted string describing the automatic changes
    """
    summary_parts = []

    if task_changes.get('auto_category_change'):
        old_cat = task_changes.get('old_category', 'unknown')
        new_cat = task_changes.get('new_category', 'unknown')
        trigger = task_changes.get('trigger_status', 'unknown')

        summary_parts.append(
            f"Category automatically changed from '{old_cat}' to '{new_cat}' "
            f"when status was set to '{trigger}'"
        )

    return "; ".join(summary_parts) if summary_parts else "No automatic changes applied"


class TaskAutomationNotifier:
    """
    Simple notification system for task automation events.

    This can be extended to send emails, create system notifications,
    or integrate with external systems when tasks are automatically categorized.
    """

    @staticmethod
    def notify_category_change(task_id: int, task_title: str, old_category: str,
                               new_category: str, user_id: Optional[int] = None):
        """
        Notify about an automatic category change.

        This is a placeholder that can be extended to send actual notifications.
        """
        message = (
            f"Task '{task_title}' (ID: {task_id}) was automatically moved "
            f"from '{old_category}' to '{new_category}' category"
        )

        # For now, just log the notification
        # In the future, this could send emails, push notifications, etc.
        logger.info(f"NOTIFICATION: {message}")

        # Store notification in session state for UI display (if available)
        try:
            import streamlit as st
            if 'automation_notifications' not in st.session_state:
                st.session_state.automation_notifications = []

            st.session_state.automation_notifications.append({
                'timestamp': datetime.now(),
                'message': message,
                'type': 'category_change',
                'task_id': task_id
            })

            # Keep only the last 10 notifications
            if len(st.session_state.automation_notifications) > 10:
                st.session_state.automation_notifications = st.session_state.automation_notifications[-10:]

        except ImportError:
            # Streamlit not available, skip session state storage
            pass

    @staticmethod
    def get_recent_notifications() -> list:
        """
        Get recent automation notifications for display in UI.

        Returns:
            List of recent notification dictionaries
        """
        try:
            import streamlit as st
            return st.session_state.get('automation_notifications', [])
        except ImportError:
            return []


# Example usage and configuration
AUTOMATION_CONFIG = {
    'enable_auto_categorization': True,
    'enable_notifications': True,
    'log_all_changes': True,
    'notification_retention_count': 10
}


def is_automation_enabled(feature: str) -> bool:
    """
    Check if a specific automation feature is enabled.

    Args:
        feature: Name of the automation feature

    Returns:
        True if the feature is enabled
    """
    return AUTOMATION_CONFIG.get(feature, False)
