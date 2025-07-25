import streamlit as st

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
