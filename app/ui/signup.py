import asyncio
import streamlit as st
from app.core.interface.user_interface import create_user

def signup(navigate):
    st.markdown("<h2 style='text-align: center;'>📝 Sign Up</h2>", unsafe_allow_html=True)

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
                submitted = st.form_submit_button("Sign Up")

            async def handle_signup():
                return await create_user(username, email, password)

            if submitted:
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

        st.button("← Back to Home", on_click=lambda: navigate("home"), use_container_width=True)
