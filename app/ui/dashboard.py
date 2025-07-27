import streamlit as st
from app.ui.navbar import navbar


def dashboard(go_to_page):
    """Dashboard page with navbar"""
    navbar(go_to_page, "dashboard")
    
    user = st.session_state.get("user", {})
    username = user.get("username", "User")
    
    st.markdown("# 📊 Dashboard")
    st.markdown(f"Welcome back, **{username}**! Here's your system overview.")
    
    st.divider()
    
    # Quick stats
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Reports", "24", "↗️ 12%")
    with col2:
        st.metric("Active Templates", "8", "↗️ 2")
    with col3:
        st.metric("Scheduled Tasks", "15", "→ 0%")
    with col4:
        st.metric("Success Rate", "98.5%", "↗️ 1.2%")
    
    st.divider()
    
    # Recent activity and quick actions
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("📈 Recent Activity")
        st.info("✅ Monthly Sales Report - Completed (2 hours ago)")
        st.info("⏳ Weekly Analytics - In Progress")
        st.success("✅ Daily Summary - Completed (1 day ago)")
        st.warning("⚠️ Quarterly Review - Scheduled for tomorrow")
    
    with col2:
        st.subheader("🚀 Quick Actions")
        if st.button("📊 Generate Report", use_container_width=True):
            st.success("Report generation started!")
        if st.button("🎨 Create Template", use_container_width=True):
            go_to_page("template_designer")
        if st.button("⚙️ System Settings", use_container_width=True):
            go_to_page("settings")
