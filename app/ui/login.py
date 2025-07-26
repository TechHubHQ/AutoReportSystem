import asyncio
import streamlit as st
from app.core.interface.user_interface import authenticate_user

def login(navigate):
    st.markdown("<h2 style='text-align: center;'>🔐 Login</h2>", unsafe_allow_html=True)

    with st.container():
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            with st.form("login_form", border=True):
                email = st.text_input("Email")
                password = st.text_input("Password", type="password")
                submitted = st.form_submit_button("Login")

            if submitted:
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

        st.button("← Back to Home", on_click=lambda: navigate("home"), use_container_width=True)
