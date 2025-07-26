import asyncio
import streamlit as st
from app.core.interface.user_interface import authenticate_user

st.title("Login Page")

with st.form("login_form"):
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    submitted = st.form_submit_button("Login")


if submitted:
    try:
        user = asyncio.run(authenticate_user(email, password))
        if user:
            st.success(f"Welcome {user.email}!")
        else:
            st.error("Invalid email or password")
    except Exception as e:
        st.error(f"An error occurred: {e}")
