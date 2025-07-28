import streamlit as st
from app.ui.navbar import navbar
from app.ui.security_dashboard import security_dashboard


def settings(go_to_page):
    """Settings page with navbar"""
    st.markdown("""
    <style>
    .settings-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        color: white;
        text-align: center;
    }
    .settings-card {
        background: white;
        padding: 1.5rem;
        border-radius: 15px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        margin-bottom: 1.5rem;
    }
    </style>
    """, unsafe_allow_html=True)

    navbar(go_to_page, "settings")

    st.markdown("""
    <div class="settings-header">
        <h1 style="margin: 0; font-size: 2.5rem;">⚙️ Settings</h1>
        <p style="margin: 0.5rem 0 0 0; font-size: 1.1rem; opacity: 0.9;">Configure your system preferences and account settings</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="settings-card">', unsafe_allow_html=True)
    st.markdown("### 👤 Account Settings")
    user = st.session_state.get("user", {})
    col1, col2 = st.columns(2)
    with col1:
        st.text_input("👤 Username", value=user.get(
            "username", ""), disabled=True)
        st.text_input("📧 Email", value=user.get("email", ""), disabled=True)
    with col2:
        st.selectbox("🎨 Theme", ["Light", "Dark", "Auto"])
        st.selectbox("🌍 Language", ["English", "Spanish", "French"])
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="settings-card">', unsafe_allow_html=True)
    st.markdown("### 🔔 Notifications")
    st.checkbox("📧 Email notifications", value=True)
    st.checkbox("📈 Report completion alerts", value=True)
    st.checkbox("🔧 System maintenance updates", value=False)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="settings-card">', unsafe_allow_html=True)
    st.markdown("### 🔧 System Settings")
    st.selectbox("📄 Default report format", ["PDF", "Excel", "CSV"])
    st.number_input("⏰ Auto-save interval (minutes)",
                    min_value=1, max_value=60, value=5)
    st.markdown('</div>', unsafe_allow_html=True)

    if st.button("💾 Save Settings", type="primary", use_container_width=True):
        st.success("🎉 Settings saved successfully!")
    st.markdown('</div>', unsafe_allow_html=True)

    # Add security dashboard
    st.markdown('<div class="settings-card">', unsafe_allow_html=True)
    security_dashboard()
    st.markdown('</div>', unsafe_allow_html=True)
