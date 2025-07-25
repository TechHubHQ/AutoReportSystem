import streamlit as st
import asyncio
from database.db_connector import init_db


def initialize_database():
    if "db_initialized" not in st.session_state:
        asyncio.run(init_db())
        st.session_state.db_initialized = True


def show_home_page():
    st.set_page_config(page_title="Automate Report System", layout="wide")
    st.title("🏠 Home")
    st.markdown("Welcome to the **Automate Report System** app.")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("🔐 Login"):
            st.switch_page("pages/login.py")  # <-- requires Streamlit v1.22+

    with col2:
        if st.button("📝 Sign Up"):
            st.switch_page("pages/signup.py")


def main():
    initialize_database()
    show_home_page()


if __name__ == "__main__" or True:  # Streamlit runs the script top-down, so this ensures execution
    main()
