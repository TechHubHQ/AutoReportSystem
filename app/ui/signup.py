import asyncio
import streamlit as st
from app.core.interface.user_interface import create_user
from app.ui.components.loader import LoaderContext


def signup(navigate):
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

    if "user" in st.session_state:
        st.success("🎉 You're already logged in!")
        return

    st.markdown("<br>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown(
            '<h1 style="text-align: center; color: #333; margin-bottom: 2rem;">🎆 Join Us Today</h1>', unsafe_allow_html=True)

        with st.form("signup_form", clear_on_submit=False):
            st.markdown('<p style="text-align: center; color: white; font-size: 1.1rem; margin-bottom: 1.5rem;">Create your account to get started</p>', unsafe_allow_html=True)

            username = st.text_input(
                "👤 Username", placeholder="Choose a username")
            email = st.text_input(
                "📧 Email Address", placeholder="Enter your email")
            password = st.text_input(
                "🔒 Password", type="password", placeholder="Create a secure password")
            userrole = st.text_input(
                "🧑‍💼 Role", placeholder="e.g. Software Engineer")

            st.markdown("<br>", unsafe_allow_html=True)
            form_col1, form_col2 = st.columns(2)
            with form_col1:
                submitted = st.form_submit_button(
                    "🎉 Create Account", use_container_width=True)
            with form_col2:
                back_clicked = st.form_submit_button(
                    "← Back to Home", use_container_width=True)

            async def handle_signup():
                return await create_user(username, email, password, userrole)

            if 'submitted' in locals() and submitted:
                if username and email and password:
                    with LoaderContext("🎆 Creating account...", "inline"):
                        try:
                            user = asyncio.run(handle_signup())
                            if user:
                                st.success(f"✅ Welcome {user.email}!")
                                user_data = {
                                    "id": user.id,
                                    "username": user.username,
                                    "email": user.email
                                }
                                st.session_state.user = user_data
                                navigate("dashboard")
                            else:
                                st.error("❌ Could not create user.")
                        except Exception as e:
                            st.error(f"❌ An error occurred: {e}")
                else:
                    st.error("⚠️ Please fill in all fields")
            if 'back_clicked' in locals() and back_clicked:
                navigate("home")
