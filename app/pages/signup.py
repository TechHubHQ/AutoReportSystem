import asyncio
import streamlit as st
from core.interface.user import create_user

st.title("Sign Up Page")

# Check if user is already signed in
if "user" in st.session_state:
    st.switch_page("dashboard.py")  # Streamlit >=1.22: switch to a new page
    st.stop()

with st.form("signup_form"):
    username = st.text_input("Username")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    submitted = st.form_submit_button("Sign Up")

# Async wrapper


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
            st.experimental_rerun()
        else:
            st.error("Could not create user.")
    except Exception as e:
        st.error(f"An error occurred: {e}")
