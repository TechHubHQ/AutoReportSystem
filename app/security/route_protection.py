"""
Route Protection Module for AutomateReportSystem

This module provides authentication and authorization utilities
to protect routes from unauthorized access.
"""

import streamlit as st
from typing import List, Optional, Callable
from functools import wraps


class RouteProtection:
    """Handles route protection and authentication checks"""

    # Define which routes require authentication
    PROTECTED_ROUTES = {
        "dashboard",
        "settings",
        "template_designer",
        "smtp_conf",
        "job_management"
    }

    # Define public routes that don't require authentication
    PUBLIC_ROUTES = {
        "home",
        "login",
        "signup"
    }

    @staticmethod
    def is_authenticated() -> bool:
        """Check if user is currently authenticated"""
        return "user" in st.session_state and st.session_state.user is not None

    @staticmethod
    def get_current_user() -> Optional[dict]:
        """Get current authenticated user"""
        return st.session_state.get("user", None)

    @staticmethod
    def is_route_protected(route: str) -> bool:
        """Check if a route requires authentication"""
        return route in RouteProtection.PROTECTED_ROUTES

    @staticmethod
    def is_route_public(route: str) -> bool:
        """Check if a route is public"""
        return route in RouteProtection.PUBLIC_ROUTES

    @staticmethod
    def clear_session():
        """Clear user session data"""
        keys_to_keep = {"db_initialized"}
        keys_to_remove = [
            key for key in st.session_state.keys() if key not in keys_to_keep]
        for key in keys_to_remove:
            del st.session_state[key]

    @staticmethod
    def set_intended_destination(route: str):
        """Set the intended destination for post-login redirect"""
        if RouteProtection.is_route_protected(route):
            st.session_state.intended_destination = route

    @staticmethod
    def get_intended_destination() -> str:
        """Get and clear the intended destination"""
        destination = st.session_state.get("intended_destination", "dashboard")
        if "intended_destination" in st.session_state:
            del st.session_state.intended_destination
        return destination

    @staticmethod
    def redirect_to_login(route: str, go_to_page: Callable):
        """Redirect to login page with intended destination"""
        RouteProtection.set_intended_destination(route)
        st.error("🔒 Please log in to access this page.")
        st.info("👆 You will be redirected to your intended page after login.")
        go_to_page("login")

    @staticmethod
    def check_route_access(route: str, go_to_page: Callable) -> bool:
        """
        Check if user has access to the requested route

        Returns:
            bool: True if access is granted, False if redirected
        """
        # Allow access to public routes
        if RouteProtection.is_route_public(route):
            return True

        # Check authentication for protected routes
        if RouteProtection.is_route_protected(route):
            if not RouteProtection.is_authenticated():
                RouteProtection.redirect_to_login(route, go_to_page)
                return False
            return True

        # Unknown route - redirect to home
        st.error("❌ Page not found.")
        go_to_page("home")
        return False


def require_auth(func):
    """
    Decorator to protect individual functions/pages that require authentication

    Usage:
        @require_auth
        def protected_page(go_to_page):
            # Page content here
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not RouteProtection.is_authenticated():
            st.error("🔒 Authentication required to access this page.")
            st.stop()
        return func(*args, **kwargs)
    return wrapper


def session_timeout_check():
    """
    Check for session timeout and handle accordingly
    This can be extended to implement actual session timeout logic
    """
    # For now, just check if user exists
    # In the future, you could add timestamp-based session expiration
    if "user" in st.session_state:
        user = st.session_state.user
        if not user or not isinstance(user, dict):
            RouteProtection.clear_session()
            return False
    return True


def get_user_role() -> str:
    """
    Get current user's role (for future role-based access control)
    """
    user = RouteProtection.get_current_user()
    if user:
        return user.get("role", "user")
    return "anonymous"


def has_permission(permission: str) -> bool:
    """
    Check if current user has specific permission
    This is a placeholder for future role-based permissions
    """
    if not RouteProtection.is_authenticated():
        return False

    # For now, all authenticated users have all permissions
    # This can be extended with actual role-based logic
    return True
