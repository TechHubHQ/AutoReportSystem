import streamlit as st
import asyncio
from app.database.db_connector import init_db
from app.ui.login import login
from app.ui.signup import signup
from app.ui.dashboard import dashboard

st.set_page_config(page_title="Automate Report System", layout="wide")

# Initialize DB only once
if "db_initialized" not in st.session_state:
    asyncio.run(init_db())
    st.session_state.db_initialized = True

# Page state manager
if "page" not in st.session_state:
    st.session_state.page = "home"

# Page router


def go_to_page(page_name):
    st.session_state.page = page_name
    st.rerun()


# Show selected page
if st.session_state.page == "home":
    st.markdown("<h1 style='text-align: center;'>🏠 Automate Report System</h1>",
                unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'>Welcome to the <b>Automate Report System</b>. Choose an option below to proceed.</p>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        pass
    with col2:
        st.markdown("### 🔐 Login")
        if st.button("Login", use_container_width=True):
            go_to_page("login")
        st.markdown("### 📝 Sign Up")
        if st.button("Sign Up", use_container_width=True):
            go_to_page("signup")
    with col3:
        pass

elif st.session_state.page == "login":
    login(go_to_page)

elif st.session_state.page == "signup":
    signup(go_to_page)

elif st.session_state.page == "dashboard":
    dashboard(go_to_page)
