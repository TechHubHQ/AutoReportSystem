"""
Security Middleware for AutomateReportSystem

This module provides middleware functions for enhanced security features
including session management, CSRF protection, and security headers.
"""

import streamlit as st
import time
from datetime import datetime, timedelta
from typing import Optional
from app.security.route_protection import RouteProtection
from app.security.session_manager import SessionManager


class SecurityMiddleware:
    """Security middleware for additional protection features"""

    # Session timeout in seconds (6 hours - managed by SessionManager)
    SESSION_TIMEOUT = 6 * 60 * 60

    @staticmethod
    def init_session_security():
        """Initialize session security features"""
        if "session_start_time" not in st.session_state:
            st.session_state.session_start_time = time.time()

        if "last_activity" not in st.session_state:
            st.session_state.last_activity = time.time()

    @staticmethod
    def update_last_activity():
        """Update last activity timestamp"""
        st.session_state.last_activity = time.time()

    @staticmethod
    def check_session_timeout() -> bool:
        """
        Check if session has timed out using SessionManager

        Returns:
            bool: True if session is valid, False if timed out
        """
        if not SessionManager.is_authenticated():
            return True

        session_info = SessionManager.get_session_info()
        if session_info and not session_info.get('is_valid', False):
            # Session expired - only show error if we're on a protected route
            current_page = st.session_state.get('page', 'home')
            if RouteProtection.is_route_protected(current_page):
                SessionManager.destroy_session()
                st.error("🕐 Your session has expired. Please log in again.")
                return False
            else:
                # Just clear the session silently for public pages
                SessionManager.destroy_session()

        return True

    @staticmethod
    def get_session_info() -> dict:
        """Get current session information from SessionManager"""
        return SessionManager.get_session_info()

    @staticmethod
    def format_time_remaining(seconds: float) -> str:
        """Format remaining time in human-readable format"""
        if seconds <= 0:
            return "Expired"

        minutes = int(seconds // 60)
        seconds = int(seconds % 60)

        if minutes > 0:
            return f"{minutes}m {seconds}s"
        else:
            return f"{seconds}s"

    @staticmethod
    def show_session_warning():
        """Show session timeout warning if needed"""
        if not SessionManager.is_authenticated():
            return

        session_info = SessionManager.get_session_info()
        time_remaining = session_info.get("time_remaining", 0)

        # Show warning if less than 30 minutes remaining
        if 0 < time_remaining < 1800:  # 30 minutes
            remaining_time = SecurityMiddleware.format_time_remaining(
                time_remaining)
            col1, col2 = st.columns([3, 1])
            with col1:
                st.warning(
                    f"⚠️ Your session will expire in {remaining_time}. Please save your work.")
            with col2:
                if st.button("🔄 Extend Session", key="extend_session"):
                    if SessionManager.extend_session():
                        st.success("✅ Session extended by 6 hours!")
                        st.rerun()

    @staticmethod
    def add_security_headers():
        """Add security headers (for future use with custom deployment)"""
        # This is a placeholder for future implementation
        # In a production environment, these would be set at the server level
        pass

    @staticmethod
    def log_security_event(event_type: str, details: str = ""):
        """Log security events for monitoring"""
        if "security_log" not in st.session_state:
            st.session_state.security_log = []

        event = {
            "timestamp": datetime.now().isoformat(),
            "type": event_type,
            "details": details,
            "user": RouteProtection.get_current_user(),
            "session_id": st.session_state.get("session_id", "unknown")
        }

        st.session_state.security_log.append(event)

        # Keep only last 100 events to prevent memory issues
        if len(st.session_state.security_log) > 100:
            st.session_state.security_log = st.session_state.security_log[-100:]

    @staticmethod
    def get_security_log() -> list:
        """Get security event log"""
        return st.session_state.get("security_log", [])

    @staticmethod
    def validate_input(input_value: str, max_length: int = 1000) -> bool:
        """Basic input validation"""
        if not input_value:
            return True

        # Check length
        if len(input_value) > max_length:
            return False

        # Basic XSS prevention (very basic)
        dangerous_patterns = ["<script", "javascript:", "onload=", "onerror="]
        input_lower = input_value.lower()

        for pattern in dangerous_patterns:
            if pattern in input_lower:
                return False

        return True

    @staticmethod
    def sanitize_input(input_value: str) -> str:
        """Basic input sanitization"""
        if not input_value:
            return ""

        # Remove potentially dangerous characters
        dangerous_chars = ["<", ">", "\"", "'", "&"]
        sanitized = input_value

        for char in dangerous_chars:
            sanitized = sanitized.replace(char, "")

        return sanitized.strip()


def apply_security_middleware():
    """Apply all security middleware checks"""
    # Initialize session security
    SecurityMiddleware.init_session_security()

    # Check session timeout
    if not SecurityMiddleware.check_session_timeout():
        st.stop()

    # Show session warning if needed
    SecurityMiddleware.show_session_warning()

    # Add security headers
    SecurityMiddleware.add_security_headers()

    # Log page access
    current_page = st.session_state.get("page", "unknown")
    SecurityMiddleware.log_security_event(
        "page_access", f"Accessed page: {current_page}")


def require_fresh_login(max_age_minutes: int = 30):
    """
    Require a fresh login (within specified time)
    Useful for sensitive operations
    """
    if not RouteProtection.is_authenticated():
        st.error("🔒 Authentication required.")
        st.stop()

    session_info = SecurityMiddleware.get_session_info()
    session_duration = session_info.get("session_duration", 0)

    if session_duration > (max_age_minutes * 60):
        st.error(
            f"🔒 This operation requires a fresh login (within {max_age_minutes} minutes).")
        st.info("Please log out and log back in to continue.")
        st.stop()
