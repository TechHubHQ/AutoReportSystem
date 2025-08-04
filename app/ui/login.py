import asyncio
import streamlit as st
from app.core.interface.user_interface import authenticate_user
from app.ui.components.loader import LoaderContext
from app.security.route_protection import RouteProtection
from app.security.backend_session_manager import BackendSessionManager


def login(navigate):
    st.markdown("""
    <style>
    .stForm {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 20px;
        box-shadow: 0 15px 35px rgba(0,0,0,0.1);
        border: none;
    }
    .stTextInput > div > div > input {
        background: rgba(255,255,255,0.9);
        border: none;
        border-radius: 10px;
        padding: 0.75rem;
    }
    .stButton > button {
        background: linear-gradient(45deg, #FF6B6B, #4ECDC4);
        color: white;
        border: none;
        border-radius: 10px;
        font-weight: 600;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown(
            '<h1 style="text-align: center; color: #333; margin-bottom: 2rem;">🔐 Welcome Back</h1>', unsafe_allow_html=True)

        with st.form("login_form", clear_on_submit=False):
            st.markdown(
                '<p style="text-align: center; color: white; font-size: 1.1rem; margin-bottom: 1.5rem;">Sign in to access your dashboard</p>', unsafe_allow_html=True)

            email = st.text_input(
                "📧 Email Address", placeholder="Enter your email")
            password = st.text_input(
                "🔒 Password", type="password", placeholder="Enter your password")

            st.markdown("<br>", unsafe_allow_html=True)
            form_col1, form_col2 = st.columns(2)
            with form_col1:
                submitted = st.form_submit_button(
                    "🚀 Sign In", use_container_width=True)
            with form_col2:
                back_clicked = st.form_submit_button(
                    "← Back to Home", use_container_width=True)
            if 'submitted' in locals() and submitted:
                if email and password:
                    with LoaderContext("🔐 Authenticating...", "inline"):
                        try:
                            user = asyncio.run(
                                authenticate_user(email, password))
                            if user:
                                st.success(f"✅ Welcome {user.email}!")
                                user_data = {
                                    "id": user.id,
                                    "email": user.email,
                                    "username": user.username
                                }
                                # Create persistent session
                                BackendSessionManager.create_session(user_data)
                                # Redirect to intended destination or dashboard
                                intended_destination = RouteProtection.get_intended_destination()
                                navigate(intended_destination)
                            else:
                                st.error("❌ Invalid email or password")
                        except Exception as e:
                            st.error(f"❌ An error occurred: {e}")
                else:
                    st.error("⚠️ Please fill in all fields")
            if 'back_clicked' in locals() and back_clicked:
                navigate("home")
