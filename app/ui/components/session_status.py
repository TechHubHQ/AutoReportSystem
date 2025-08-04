"""
Session Status Component

Displays current session information and provides session management controls.
"""

import streamlit as st
from app.security.backend_session_manager import BackendSessionManager


def show_session_status():
    """Display session status information"""
    if not BackendSessionManager.is_authenticated():
        return

    session_info = BackendSessionManager.get_session_info()
    time_remaining = session_info.get('time_remaining', 0)

    if time_remaining <= 0:
        st.error(
            "🔒 Your session has expired. Please refresh the page to log in again.")
        return

    # Format time remaining
    hours = int(time_remaining // 3600)
    minutes = int((time_remaining % 3600) // 60)

    if hours > 0:
        time_str = f"{hours}h {minutes}m"
    else:
        time_str = f"{minutes}m"

    # Show different styles based on time remaining
    if time_remaining < 1800:  # Less than 30 minutes
        st.warning(f"⚠️ Session expires in {time_str}")
        if st.button("🔄 Extend Session", key="extend_session_status"):
            if BackendSessionManager.extend_session():
                st.success("✅ Session extended by 6 hours!")
                st.rerun()
    elif time_remaining < 3600:  # Less than 1 hour
        st.info(f"ℹ️ Session expires in {time_str}")
    else:
        st.success(f"✅ Session active ({time_str} remaining)")


def show_compact_session_status():
    """Display compact session status for sidebar or header"""
    if not BackendSessionManager.is_authenticated():
        return

    session_info = BackendSessionManager.get_session_info()
    time_remaining = session_info.get('time_remaining', 0)

    # Don't show anything if session is expired - let the backend handle it
    if time_remaining <= 0:
        return

    # Format time remaining
    hours = int(time_remaining // 3600)
    minutes = int((time_remaining % 3600) // 60)

    if hours > 0:
        time_str = f"{hours}h {minutes}m"
    elif minutes > 0:
        time_str = f"{minutes}m"
    else:
        time_str = "<1m"

    # Color based on time remaining
    if time_remaining < 1800:  # Less than 30 minutes
        color = "#ff6b6b"  # Red
        icon = "⚠️"
    elif time_remaining < 3600:  # Less than 1 hour
        color = "#ffa726"  # Orange
        icon = "⏰"
    else:
        color = "#4caf50"  # Green
        icon = "✅"

    st.markdown(f"""
    <div style="
        background: {color}20;
        border: 1px solid {color}40;
        border-radius: 8px;
        padding: 0.5rem;
        text-align: center;
        font-size: 0.8rem;
        margin: 0.5rem 0;
    ">
        {icon} Session: {time_str}
    </div>
    """, unsafe_allow_html=True)

    # Show extend button if session is expiring soon
    if time_remaining < 3600:  # Less than 1 hour
        if st.button("🔄 Extend", key="extend_compact_session", use_container_width=True):
            if BackendSessionManager.extend_session():
                st.success("✅ Extended!")
                st.rerun()
