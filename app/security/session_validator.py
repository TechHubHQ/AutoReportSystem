"""
Session Validation Utility for AutomateReportSystem

Provides utilities to validate and refresh sessions during critical operations.
"""

import streamlit as st
from datetime import datetime, timedelta
from app.security.session_manager import SessionManager


class SessionValidator:
    """Utility class for session validation operations"""

    @staticmethod
    def ensure_valid_session() -> bool:
        """
        Ensure the current session is valid and refresh if needed

        Returns:
            bool: True if session is valid, False if invalid/expired
        """
        if not SessionManager.is_authenticated():
            return False

        session_token = st.session_state.get('session_token')
        if not session_token:
            return False

        # Validate session with database
        user_data = SessionManager.validate_session(session_token)
        if not user_data:
            # Session is invalid, clear it
            SessionManager._clear_streamlit_session()
            SessionManager._clear_browser_session()
            return False

        return True

    @staticmethod
    def refresh_session_if_needed() -> bool:
        """
        Refresh session if it's close to expiring (within 1 hour)

        Returns:
            bool: True if session is valid/refreshed, False if expired
        """
        if not SessionManager.is_authenticated():
            return False

        session_info = SessionManager.get_session_info()
        time_remaining = session_info.get('time_remaining', 0)

        # If less than 1 hour remaining, extend the session
        if 0 < time_remaining < 3600:  # 1 hour
            return SessionManager.extend_session()

        return time_remaining > 0

    @staticmethod
    def validate_and_refresh() -> bool:
        """
        Comprehensive session validation and refresh

        Returns:
            bool: True if session is valid, False if expired/invalid
        """
        # First ensure session is valid
        if not SessionValidator.ensure_valid_session():
            return False

        # Then refresh if needed
        return SessionValidator.refresh_session_if_needed()
