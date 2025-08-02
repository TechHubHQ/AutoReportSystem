"""
Persistent Session Manager for AutomateReportSystem

Provides robust session management with persistent storage
that survives page refreshes and browser restarts.
"""

import streamlit as st
import uuid
import json
import asyncio
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from app.database.db_connector import get_db
from app.database.models import UserSession, User
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession


class SessionManager:
    """Handles persistent session management"""

    # Session duration: 6 hours in seconds
    SESSION_DURATION = 6 * 60 * 60  # 6 hours

    @staticmethod
    def generate_session_token() -> str:
        """Generate a unique session token"""
        return str(uuid.uuid4())

    @staticmethod
    def create_session(user_data: Dict[str, Any]) -> str:
        """Create a new persistent session"""
        session_token = SessionManager.generate_session_token()
        expires_at = datetime.now() + timedelta(seconds=SessionManager.SESSION_DURATION)

        async def _create_session():
            async with get_db() as db:
                # Create new session
                new_session = UserSession(
                    session_token=session_token,
                    user_id=user_data.get('id'),
                    user_data=json.dumps(user_data),
                    expires_at=expires_at,
                    created_at=datetime.now(),
                    last_accessed=datetime.now()
                )
                db.add(new_session)
                await db.commit()

        try:
            asyncio.run(_create_session())

            # Store in Streamlit session
            st.session_state.user = user_data
            st.session_state.session_token = session_token
            st.session_state.session_expires_at = expires_at

            # Store in browser localStorage
            SessionManager._store_session_in_browser(session_token)

            return session_token

        except Exception as e:
            st.error(f"Failed to create session: {e}")
            return None

    @staticmethod
    def validate_session(session_token: str) -> Optional[Dict[str, Any]]:
        """Validate and retrieve session data"""
        if not session_token:
            return None

        async def _validate_session():
            async with get_db() as db:
                # Find valid session
                stmt = select(UserSession).where(
                    UserSession.session_token == session_token,
                    UserSession.expires_at > datetime.now()
                )
                result = await db.execute(stmt)
                session = result.scalar_one_or_none()

                if session:
                    # Update last accessed time
                    session.last_accessed = datetime.now()
                    await db.commit()
                    return session
                return None

        try:
            session = asyncio.run(_validate_session())
            if session:
                user_data = json.loads(session.user_data)
                
                # Store in Streamlit session
                st.session_state.user = user_data
                st.session_state.session_token = session_token
                st.session_state.session_expires_at = session.expires_at
                
                return user_data
            return None

        except Exception as e:
            st.error(f"Session validation failed: {e}")
            return None

    @staticmethod
    def destroy_session(session_token: str = None):
        """Destroy a session"""
        if not session_token:
            session_token = st.session_state.get('session_token')

        if session_token:
            async def _destroy_session():
                async with get_db() as db:
                    stmt = delete(UserSession).where(UserSession.session_token == session_token)
                    await db.execute(stmt)
                    await db.commit()

            try:
                asyncio.run(_destroy_session())
            except Exception as e:
                st.error(f"Failed to destroy session: {e}")

        # Clear Streamlit session
        SessionManager._clear_streamlit_session()

        # Clear browser storage
        SessionManager._clear_browser_session()

    @staticmethod
    def cleanup_expired_sessions():
        """Remove expired sessions from database"""
        async def _cleanup_sessions():
            async with get_db() as db:
                stmt = delete(UserSession).where(UserSession.expires_at < datetime.now())
                await db.execute(stmt)
                await db.commit()

        try:
            asyncio.run(_cleanup_sessions())
        except Exception as e:
            st.error(f"Failed to cleanup sessions: {e}")

    @staticmethod
    def get_session_info() -> Dict[str, Any]:
        """Get current session information"""
        if not SessionManager.is_authenticated():
            return {}

        expires_at = st.session_state.get('session_expires_at')
        if not expires_at:
            return {}

        now = datetime.now()
        time_remaining = (expires_at - now).total_seconds()

        return {
            'expires_at': expires_at,
            'time_remaining': max(0, time_remaining),
            'is_valid': time_remaining > 0,
            'user': st.session_state.get('user', {})
        }

    @staticmethod
    def is_authenticated() -> bool:
        """Check if user is authenticated"""
        return 'user' in st.session_state and st.session_state.user is not None

    @staticmethod
    def get_current_user() -> Optional[Dict[str, Any]]:
        """Get current user data"""
        return st.session_state.get('user')

    @staticmethod
    def extend_session():
        """Extend current session by 6 hours"""
        session_token = st.session_state.get('session_token')
        if not session_token:
            return False

        new_expires_at = datetime.now() + timedelta(seconds=SessionManager.SESSION_DURATION)

        async def _extend_session():
            async with get_db() as db:
                stmt = select(UserSession).where(UserSession.session_token == session_token)
                result = await db.execute(stmt)
                session = result.scalar_one_or_none()
                
                if session:
                    session.expires_at = new_expires_at
                    session.last_accessed = datetime.now()
                    await db.commit()
                    return True
                return False

        try:
            success = asyncio.run(_extend_session())
            if success:
                st.session_state.session_expires_at = new_expires_at
            return success

        except Exception as e:
            st.error(f"Failed to extend session: {e}")
            return False

    @staticmethod
    def restore_session_from_browser():
        """Attempt to restore session from browser storage"""
        # Check if there's a session token in query params (from browser storage)
        session_token = st.query_params.get('restore_session')

        if session_token:
            # Validate the session token
            user_data = SessionManager.validate_session(session_token)
            if user_data:
                # Clear the query parameter
                del st.query_params['restore_session']
                return True
            else:
                # Invalid session, clear query parameter
                del st.query_params['restore_session']
                return False

        # If no session in Streamlit but we haven't checked browser storage yet
        if 'browser_session_checked' not in st.session_state:
            st.session_state.browser_session_checked = True
            # Show JavaScript to check localStorage and reload with token if found
            js_code = """
            <script>
                const token = localStorage.getItem('ars_session_token');
                if (token && !window.location.search.includes('restore_session')) {
                    const url = new URL(window.location);
                    url.searchParams.set('restore_session', token);
                    window.location.href = url.toString();
                }
            </script>
            """
            st.components.v1.html(js_code, height=0)
            return False

        return False

    @staticmethod
    def _store_session_in_browser(session_token: str):
        """Store session token in browser localStorage"""
        js_code = f"""
        <script>
            localStorage.setItem('ars_session_token', '{session_token}');
        </script>
        """
        st.components.v1.html(js_code, height=0)

    @staticmethod
    def _clear_browser_session():
        """Clear session from browser localStorage"""
        js_code = """
        <script>
            localStorage.removeItem('ars_session_token');
        </script>
        """
        st.components.v1.html(js_code, height=0)

    @staticmethod
    def _clear_streamlit_session():
        """Clear Streamlit session data"""
        keys_to_keep = {'db_initialized'}
        keys_to_remove = [
            key for key in st.session_state.keys()
            if key not in keys_to_keep
        ]
        for key in keys_to_remove:
            del st.session_state[key]

    @staticmethod
    def init_session_table():
        """Initialize the user_sessions table (handled by Alembic migrations)"""
        # Table creation is now handled by Alembic migrations
        # This method is kept for backward compatibility
        pass
