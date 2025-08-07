"""
Route Protection Module for AutomateReportSystem

This module provides authentication and authorization utilities
to protect routes from unauthorized access.
"""

import streamlit as st
from typing import List, Optional, Callable
from functools import wraps
from app.security.backend_session_manager import BackendSessionManager


class RouteProtection:
    """Handles route protection and authentication checks"""

    # Define which routes require authentication
    PROTECTED_ROUTES = {
        "dashboard",
        "settings",
        "template_designer",
        "smtp_conf",
        "jobs",
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
        return BackendSessionManager.is_authenticated()

    @staticmethod
    def get_current_user() -> Optional[dict]:
        """Get current authenticated user"""
        return BackendSessionManager.get_current_user()

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
        BackendSessionManager.destroy_session()

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
    def logout():
        """Logout user and clear session"""
        BackendSessionManager.destroy_session()

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
