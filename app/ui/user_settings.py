import streamlit as st
from app.ui.navbar import navbar


def settings(go_to_page):
    """Settings page with navbar"""
    navbar(go_to_page, "settings")

    st.markdown("# ⚙️ Settings")
    st.markdown("Configure your system preferences and account settings.")

    st.divider()

    # Account Settings
    st.subheader("👤 Account Settings")
    user = st.session_state.get("user", {})

    col1, col2 = st.columns(2)
    with col1:
        st.text_input("Username", value=user.get(
            "username", ""), disabled=True)
        st.text_input("Email", value=user.get("email", ""), disabled=True)

    with col2:
        st.selectbox("Theme", ["Light", "Dark", "Auto"])
        st.selectbox("Language", ["English", "Spanish", "French"])

    st.divider()

    # Notification Settings
    st.subheader("🔔 Notifications")
    st.checkbox("Email notifications", value=True)
    st.checkbox("Report completion alerts", value=True)
    st.checkbox("System maintenance updates", value=False)

    st.divider()

    # System Settings
    st.subheader("🔧 System Settings")
    st.selectbox("Default report format", ["PDF", "Excel", "CSV"])
    st.number_input("Auto-save interval (minutes)",
                    min_value=1, max_value=60, value=5)

    if st.button("💾 Save Settings", type="primary"):
        st.success("Settings saved successfully!")
