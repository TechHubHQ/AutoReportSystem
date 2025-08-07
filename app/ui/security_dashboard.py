"""
Security Dashboard Component

Provides security information and controls for users
"""

import streamlit as st
from datetime import datetime
from app.security.route_protection import RouteProtection
from app.security.middleware import SecurityMiddleware


def security_dashboard():
    """Display security dashboard with session info and security controls"""

    if not RouteProtection.is_authenticated():
        st.error("🔒 Authentication required to view security dashboard.")
        return

    st.markdown("### 🔒 Security Dashboard")

    # Current user info
    user = RouteProtection.get_current_user()
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### 👤 Current Session")
        st.info(f"**User:** {user.get('username', 'Unknown')}")
        st.info(f"**Email:** {user.get('email', 'Unknown')}")
        st.info(f"**User ID:** {user.get('id', 'Unknown')}")

    with col2:
        st.markdown("#### ⏰ Session Information")
        session_info = SecurityMiddleware.get_session_info()

        if session_info:
            time_remaining = session_info.get("time_remaining", 0)
            created_at = session_info.get("created_at")

            # Calculate session duration if created_at is available
            if created_at:
                from datetime import datetime
                session_duration = (
                    datetime.now() - created_at).total_seconds()
                duration_minutes = int(session_duration // 60)
                duration_seconds = int(session_duration % 60)
                st.info(
                    f"**Session Duration:** {duration_minutes}m {duration_seconds}s")

            st.info(
                f"**Time Until Timeout:** {SecurityMiddleware.format_time_remaining(time_remaining)}")

            # Session status
            if time_remaining > 300:  # More than 5 minutes
                st.success("✅ Session Active")
            elif time_remaining > 0:
                st.warning("⚠️ Session Expiring Soon")
            else:
                st.error("❌ Session Expired")

    st.markdown("---")

    # Security actions
    st.markdown("#### 🛡️ Security Actions")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("🔄 Refresh Session", use_container_width=True):
            SecurityMiddleware.update_last_activity()
            st.success("✅ Session refreshed!")
            st.rerun()

    with col2:
        if st.button("📊 View Security Log", use_container_width=True):
            st.session_state.show_security_log = True

    with col3:
        if st.button("🚪 Force Logout", use_container_width=True, type="secondary"):
            RouteProtection.clear_session()
            st.success("👋 Logged out successfully!")
            st.rerun()

    # Security log viewer
    if st.session_state.get("show_security_log", False):
        st.markdown("---")
        st.markdown("#### 📋 Security Event Log")

        security_log = SecurityMiddleware.get_security_log()

        if security_log:
            # Show last 10 events
            recent_events = security_log[-10:]

            for event in reversed(recent_events):
                timestamp = datetime.fromisoformat(
                    event["timestamp"]).strftime("%Y-%m-%d %H:%M:%S")
                event_type = event["type"]
                details = event["details"]

                # Color code by event type
                if event_type == "page_access":
                    st.info(f"**{timestamp}** - 📄 {event_type}: {details}")
                elif event_type == "login":
                    st.success(f"**{timestamp}** - 🔐 {event_type}: {details}")
                elif event_type == "logout":
                    st.warning(f"**{timestamp}** - 🚪 {event_type}: {details}")
                else:
                    st.write(f"**{timestamp}** - {event_type}: {details}")
        else:
            st.info("No security events recorded.")

        if st.button("❌ Close Log"):
            st.session_state.show_security_log = False
            st.rerun()

    st.markdown("---")

    # Security tips
    st.markdown("#### 💡 Security Tips")

    tips = [
        "🔒 Always log out when using shared computers",
        "⏰ Your session will automatically expire after 30 minutes of inactivity",
        "🔄 Refresh your session regularly during long work periods",
        "🚫 Never share your login credentials with others",
        "📱 Use strong, unique passwords for your account"
    ]

    for tip in tips:
        st.markdown(f"- {tip}")


def show_security_status():
    """Show a compact security status indicator"""
    if not RouteProtection.is_authenticated():
        return

    session_info = SecurityMiddleware.get_session_info()
    time_remaining = session_info.get("time_remaining", 0)

    if time_remaining > 300:  # More than 5 minutes
        st.sidebar.success("🔒 Session Secure")
    elif time_remaining > 0:
        remaining = SecurityMiddleware.format_time_remaining(
            time_remaining)
        st.sidebar.warning(f"⚠️ Session expires in {remaining}")
    else:
        st.sidebar.error("❌ Session Expired")


def require_password_confirmation(action_name: str = "this action") -> bool:
    """
    Require password confirmation for sensitive actions

    Returns:
        bool: True if password is confirmed, False otherwise
    """
    if not RouteProtection.is_authenticated():
        return False

    st.markdown(f"#### 🔐 Confirm Password for {action_name}")
    st.warning("⚠️ This action requires password confirmation for security.")

    with st.form("password_confirmation"):
        password = st.text_input("Enter your password:", type="password")
        submitted = st.form_submit_button("Confirm")

        if submitted:
            if password:
                # Here you would verify the password against the database
                # For now, we'll just simulate the check
                user = RouteProtection.get_current_user()

                # Import the authentication function
                try:
                    import asyncio
                    from app.core.interface.user_interface import authenticate_user

                    auth_result = asyncio.run(
                        authenticate_user(user.get("email"), password))
                    if auth_result:
                        st.success("✅ Password confirmed!")
                        SecurityMiddleware.log_security_event(
                            "password_confirmation", f"Confirmed for: {action_name}")
                        return True
                    else:
                        st.error("❌ Invalid password!")
                        SecurityMiddleware.log_security_event(
                            "failed_password_confirmation", f"Failed for: {action_name}")
                        return False
                except Exception as e:
                    st.error(f"❌ Error verifying password: {e}")
                    return False
            else:
                st.error("⚠️ Please enter your password.")
                return False

    return False
