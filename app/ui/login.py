import asyncio
import streamlit as st
from app.core.interface.user_interface import authenticate_user


def login(navigate):
    st.markdown("<h2 style='text-align: center;'>🔐 Login</h2>",
                unsafe_allow_html=True)

    with st.container():
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            with st.form("login_form", border=True):
                email = st.text_input("Email")
                password = st.text_input("Password", type="password")
                form_col1, form_col2 = st.columns(2)
                with form_col1:
                    submitted = st.form_submit_button(
                        "Login", use_container_width=True)
                with form_col2:
                    back_clicked = st.form_submit_button(
                        "← Back to Home", use_container_width=True)
            if 'submitted' in locals() and submitted:
                try:
                    user = asyncio.run(authenticate_user(email, password))
                    if user:
                        st.success(f"Welcome {user.email}!")
                        st.session_state.user = {
                            "id": user.id,
                            "email": user.email,
                            "username": user.username
                        }
                        navigate("dashboard")
                    else:
                        st.error("Invalid email or password")
                except Exception as e:
                    st.error(f"An error occurred: {e}")
            if 'back_clicked' in locals() and back_clicked:
                navigate("home")
