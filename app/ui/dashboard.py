import streamlit as st


def dashboard(go_to_page):
    user = st.session_state.get("user", {})
    username = user.get("username", "User")
    email = user.get("email", "")

    # Header with app name (left), profile icon and logout (right)
    header_col1, header_col2 = st.columns([3, 1])
    with header_col1:
        st.markdown(
            "<h2 style='margin-bottom:0;'>🚀 Automate Report System</h2>",
            unsafe_allow_html=True
        )
    with header_col2:
        profile_html = f"""
        <div style="display: flex; align-items: center; justify-content: flex-end;">
            <span style="font-size: 1.3em; margin-right: 0.5em;">👤</span>
            <span style="margin-right: 1em;">{username}</span>
        </div>
        """
        st.markdown(profile_html, unsafe_allow_html=True)
        logout_clicked = st.button(
            "🔙 Logout",
            key="dashboard_logout_btn",
            use_container_width=True
        )
        if logout_clicked:
            st.session_state.clear()
            st.session_state["page"] = "home"
            st.rerun()

    st.divider()

    st.markdown(
        f"<h3 style='text-align: center;'>📊 Welcome, {username}!</h3>",
        unsafe_allow_html=True
    )
    st.markdown(
        "<p style='text-align: center;'>You are now logged in to the Automate Report System dashboard.</p>",
        unsafe_allow_html=True
    )

    st.divider()

    col1, col2 = st.columns(2)
    with col1:
        st.info("Cheppa Kadha Anna Saturday work chestha ani")
    with col2:
        st.success("Bagundhi ila work chesthe self improvement kosam.")

    st.divider()
