import streamlit as st

def dashboard(go_to_page):
    user = st.session_state.get("user", {})
    username = user.get("username", "User")

    st.markdown(f"<h2 style='text-align: center;'>📊 Welcome, {username}!</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'>You are now logged in to the Automate Report System dashboard.</p>", unsafe_allow_html=True)

    st.divider()

    col1, col2 = st.columns(2)
    with col1:
        st.info("🔧 Dashboard Section 1 — Customize this area.")
    with col2:
        st.success("📑 Dashboard Section 2 — Add your analytics or reports here.")

    st.divider()
    st.button(
    "🔙 Logout",
    use_container_width=True,
    on_click=lambda: (
        st.session_state.clear(),
        st.session_state.__setitem__("page", "home")
    )
)

