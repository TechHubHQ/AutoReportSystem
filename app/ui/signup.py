import asyncio
import streamlit as st
from app.core.interface.user_interface import create_user


def signup(navigate):
    st.markdown("<h2 style='text-align: center;'>📝 Sign Up</h2>",
                unsafe_allow_html=True)

    if "user" in st.session_state:
        st.success("You're already logged in.")
        return

    with st.container():
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            with st.form("signup_form", border=True):
                username = st.text_input("Username")
                email = st.text_input("Email")
                password = st.text_input("Password", type="password")
                form_col1, form_col2 = st.columns(2)
                with form_col1:
                    submitted = st.form_submit_button(
                        "Sign Up", use_container_width=True)
                with form_col2:
                    back_clicked = st.form_submit_button(
                        "← Back to Home", use_container_width=True)

            async def handle_signup():
                return await create_user(username, email, password)

            if 'submitted' in locals() and submitted:
                try:
                    user = asyncio.run(handle_signup())
                    if user:
                        st.success(f"Welcome {user.email}!")
                        st.session_state.user = {
                            "id": user.id,
                            "username": user.username,
                            "email": user.email
                        }
                        navigate("dashboard")
                    else:
                        st.error("Could not create user.")
                except Exception as e:
                    st.error(f"An error occurred: {e}")
            if 'back_clicked' in locals() and back_clicked:
                navigate("home")
