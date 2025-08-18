"""
UI component for displaying task automation notifications.

This component shows recent automatic task categorization changes
and other automation events to keep users informed.
"""

import streamlit as st
from datetime import datetime, timedelta
from app.core.utils.task_automation_utils import TaskAutomationNotifier


def show_automation_notifications():
    """
    Display recent automation notifications in the UI.

    This function creates a collapsible section showing recent
    automatic task categorization changes and other automation events.
    """
    notifications = TaskAutomationNotifier.get_recent_notifications()

    if not notifications:
        return

    # Filter notifications from the last 24 hours for the main display
    recent_notifications = [
        n for n in notifications
        if n['timestamp'] > datetime.now() - timedelta(hours=24)
    ]

    if not recent_notifications:
        return

    with st.expander(f"🤖 Recent Automation ({len(recent_notifications)} events)", expanded=False):
        st.markdown("""
        <style>
        .automation-notification {
            background: linear-gradient(90deg, #e3f2fd 0%, #f3e5f5 100%);
            border-left: 4px solid #2196f3;
            padding: 0.75rem;
            margin: 0.5rem 0;
            border-radius: 0 8px 8px 0;
            font-size: 0.9rem;
        }
        .automation-timestamp {
            color: #666;
            font-size: 0.8rem;
            margin-top: 0.25rem;
        }
        </style>
        """, unsafe_allow_html=True)

        for notification in reversed(recent_notifications[-5:]):  # Show last 5
            time_str = notification['timestamp'].strftime("%H:%M")

            st.markdown(f"""
            <div class="automation-notification">
                <div>🔄 {notification['message']}</div>
                <div class="automation-timestamp">⏰ {time_str}</div>
            </div>
            """, unsafe_allow_html=True)

        if len(recent_notifications) > 5:
            st.caption(f"... and {len(recent_notifications) - 5} more events")


def show_automation_summary_card():
    """
    Display a summary card of automation activity.

    This shows a compact overview of recent automation activity
    that can be displayed in the main dashboard.
    """
    notifications = TaskAutomationNotifier.get_recent_notifications()

    if not notifications:
        return

    # Count different types of automation events
    today_notifications = [
        n for n in notifications
        if n['timestamp'].date() == datetime.now().date()
    ]

    category_changes = len(
        [n for n in today_notifications if n['type'] == 'category_change'])

    if category_changes > 0:
        st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 1rem;
            border-radius: 10px;
            text-align: center;
            margin: 1rem 0;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        ">
            <h4 style="margin: 0; color: white;">🤖 Automation Active</h4>
            <p style="margin: 0.5rem 0 0 0; opacity: 0.9;">
                {category_changes} task{'s' if category_changes != 1 else ''} automatically organized today
            </p>
        </div>
        """, unsafe_allow_html=True)


def clear_automation_notifications():
    """
    Clear all automation notifications.

    This function can be called to reset the notification history.
    """
    if 'automation_notifications' in st.session_state:
        st.session_state.automation_notifications = []


def show_automation_settings():
    """
    Display automation settings and controls.

    This allows users to configure automation behavior.
    """
    st.subheader("🤖 Task Automation Settings")

    # Initialize automation settings in session state
    if 'automation_settings' not in st.session_state:
        st.session_state.automation_settings = {
            'auto_categorize_completed': True,
            'show_notifications': True,
            'notification_duration_hours': 24
        }

    settings = st.session_state.automation_settings

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Automatic Categorization**")
        settings['auto_categorize_completed'] = st.checkbox(
            "Auto-move completed tasks to accomplishments",
            value=settings['auto_categorize_completed'],
            help="When enabled, tasks marked as completed will automatically move to the accomplishments category"
        )

    with col2:
        st.markdown("**Notifications**")
        settings['show_notifications'] = st.checkbox(
            "Show automation notifications",
            value=settings['show_notifications'],
            help="Display notifications when tasks are automatically categorized"
        )

        if settings['show_notifications']:
            settings['notification_duration_hours'] = st.selectbox(
                "Show notifications for",
                options=[1, 6, 12, 24, 48],
                index=[1, 6, 12, 24, 48].index(
                    settings['notification_duration_hours']),
                format_func=lambda x: f"{x} hour{'s' if x != 1 else ''}",
                help="How long to display automation notifications"
            )

    # Save settings
    st.session_state.automation_settings = settings

    # Clear notifications button
    if st.button("🗑️ Clear Notification History"):
        clear_automation_notifications()
        st.success("Notification history cleared!")
        st.rerun()

    # Show current automation status
    notifications = TaskAutomationNotifier.get_recent_notifications()
    if notifications:
        st.info(f"📊 {len(notifications)} automation events in history")
    else:
        st.info("📊 No automation events recorded yet")


def get_automation_stats():
    """
    Get statistics about automation activity.

    Returns:
        Dictionary with automation statistics
    """
    notifications = TaskAutomationNotifier.get_recent_notifications()

    if not notifications:
        return {
            'total_events': 0,
            'today_events': 0,
            'category_changes': 0,
            'last_event': None
        }

    today = datetime.now().date()
    today_notifications = [
        n for n in notifications if n['timestamp'].date() == today]
    category_changes = [
        n for n in notifications if n['type'] == 'category_change']

    return {
        'total_events': len(notifications),
        'today_events': len(today_notifications),
        'category_changes': len(category_changes),
        'last_event': max(notifications, key=lambda x: x['timestamp'])['timestamp'] if notifications else None
    }
