"""
Backend Session Manager for AutomateReportSystem

Pure backend session management without browser storage dependencies.
Uses only database and Streamlit session state for reliable session handling.
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


class BackendSessionManager:
    """Handles backend-only session management"""

    # Session duration: 6 hours in seconds
    SESSION_DURATION = 6 * 60 * 60  # 6 hours (21600 seconds)

    @staticmethod
    def generate_session_token() -> str:
        """Generate a unique session token"""
        return str(uuid.uuid4())

    @staticmethod
    def create_session(user_data: Dict[str, Any]) -> str:
        """Create a new backend session"""
        session_token = BackendSessionManager.generate_session_token()
        expires_at = datetime.now() + timedelta(seconds=BackendSessionManager.SESSION_DURATION)

        async def _create_session():
            try:
                db = await get_db()
                async with db:
                    # Clean up any existing sessions for this user
                    cleanup_stmt = delete(UserSession).where(
                        UserSession.user_id == user_data.get('id')
                    )
                    await db.execute(cleanup_stmt)

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
                    return True
            except Exception as e:
                print(f"Database error creating session: {e}")
                return False

        try:
            success = asyncio.run(_create_session())
            if success:
                # Store in Streamlit session state
                st.session_state.user = user_data
                st.session_state.session_token = session_token
                st.session_state.session_expires_at = expires_at
                st.session_state.session_created_at = datetime.now()

                # Store session token in URL params for persistence across refreshes
                st.query_params["session"] = session_token

                print(
                    f"✅ Session created for user {user_data.get('email', 'unknown')} - expires at {expires_at}")
                return session_token
            else:
                print("❌ Failed to create session in database")
                return None

        except Exception as e:
            print(f"❌ Failed to create session: {e}")
            st.error(f"Failed to create session: {e}")
            return None

    @staticmethod
    def validate_session(session_token: str) -> Optional[Dict[str, Any]]:
        """Validate and retrieve session data from database"""
        if not session_token:
            return None

        async def _validate_session():
            try:
                db = await get_db()
                async with db:
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
            except Exception as e:
                print(f"Database error in session validation: {e}")
                return None

        try:
            session = asyncio.run(_validate_session())
            if session:
                user_data = json.loads(session.user_data)

                # Store in Streamlit session state
                st.session_state.user = user_data
                st.session_state.session_token = session_token
                st.session_state.session_expires_at = session.expires_at
                st.session_state.session_created_at = session.created_at

                return user_data
            else:
                print(
                    f"❌ Session not found or expired: {session_token[:8]}...")
                return None

        except Exception as e:
            print(f"❌ Session validation failed: {e}")
            return None

    @staticmethod
    def restore_session() -> bool:
        """Restore session from URL parameters or existing state"""
        # First check if we already have a valid session in Streamlit state
        if BackendSessionManager.is_authenticated():
            return True

        # Check for session token in URL parameters
        session_token = st.query_params.get("session")
        if session_token:
            user_data = BackendSessionManager.validate_session(session_token)
            if user_data:
                return True
            else:
                # Invalid session, clear URL parameter
                if "session" in st.query_params:
                    del st.query_params["session"]
                BackendSessionManager.clear_session()
                return False

        return False

    @staticmethod
    def is_authenticated() -> bool:
        """Check if user is authenticated"""
        if 'user' not in st.session_state or st.session_state.user is None:
            return False

        session_token = st.session_state.get('session_token')
        expires_at = st.session_state.get('session_expires_at')

        if not session_token or not expires_at:
            return False

        # Check if session has expired
        if datetime.now() > expires_at:
            BackendSessionManager.clear_session()
            return False

        return True

    @staticmethod
    def get_current_user() -> Optional[Dict[str, Any]]:
        """Get current user data"""
        return st.session_state.get('user')

    @staticmethod
    def get_session_info() -> Dict[str, Any]:
        """Get current session information"""
        if not BackendSessionManager.is_authenticated():
            return {}

        expires_at = st.session_state.get('session_expires_at')
        created_at = st.session_state.get('session_created_at')

        if not expires_at:
            return {}

        now = datetime.now()
        time_remaining = (expires_at - now).total_seconds()

        return {
            'expires_at': expires_at,
            'created_at': created_at,
            'time_remaining': max(0, time_remaining),
            'is_valid': time_remaining > 0,
            'user': st.session_state.get('user', {})
        }

    @staticmethod
    def extend_session() -> bool:
        """Extend current session by 6 hours"""
        session_token = st.session_state.get('session_token')
        if not session_token:
            return False

        new_expires_at = datetime.now() + timedelta(seconds=BackendSessionManager.SESSION_DURATION)

        async def _extend_session():
            try:
                db = await get_db()
                async with db:
                    stmt = select(UserSession).where(
                        UserSession.session_token == session_token
                    )
                    result = await db.execute(stmt)
                    session = result.scalar_one_or_none()

                    if session:
                        session.expires_at = new_expires_at
                        session.last_accessed = datetime.now()
                        await db.commit()
                        return True
                    return False
            except Exception as e:
                print(f"Database error extending session: {e}")
                return False

        try:
            success = asyncio.run(_extend_session())
            if success:
                st.session_state.session_expires_at = new_expires_at
                print(f"✅ Session extended to {new_expires_at}")
                return True
            return False

        except Exception as e:
            print(f"❌ Failed to extend session: {e}")
            return False

    @staticmethod
    def destroy_session(session_token: str = None):
        """Destroy a session"""
        if not session_token:
            session_token = st.session_state.get('session_token')

        if session_token:
            async def _destroy_session():
                try:
                    db = await get_db()
                    async with db:
                        stmt = delete(UserSession).where(
                            UserSession.session_token == session_token
                        )
                        await db.execute(stmt)
                        await db.commit()
                except Exception as e:
                    print(f"Database error destroying session: {e}")

            try:
                asyncio.run(_destroy_session())
                print(f"✅ Session destroyed: {session_token[:8]}...")
            except Exception as e:
                print(f"❌ Failed to destroy session: {e}")

        BackendSessionManager.clear_session()

    @staticmethod
    def clear_session():
        """Clear Streamlit session data"""
        # Clear URL parameter
        if "session" in st.query_params:
            del st.query_params["session"]

        # Clear Streamlit session state (keep db_initialized)
        keys_to_keep = {'db_initialized'}
        keys_to_remove = [
            key for key in st.session_state.keys()
            if key not in keys_to_keep
        ]
        for key in keys_to_remove:
            del st.session_state[key]

    @staticmethod
    def cleanup_expired_sessions():
        """Remove expired sessions from database"""
        async def _cleanup_sessions():
            try:
                db = await get_db()
                async with db:
                    stmt = delete(UserSession).where(
                        UserSession.expires_at < datetime.now()
                    )
                    result = await db.execute(stmt)
                    await db.commit()
                    print(f"✅ Cleaned up {result.rowcount} expired sessions")
            except Exception as e:
                print(f"❌ Failed to cleanup sessions: {e}")

        try:
            asyncio.run(_cleanup_sessions())
        except Exception as e:
            print(f"❌ Session cleanup error: {e}")

    @staticmethod
    def init_session_table():
        """Initialize the user_sessions table (handled by Alembic migrations)"""
        # Table creation is now handled by Alembic migrations
        pass
