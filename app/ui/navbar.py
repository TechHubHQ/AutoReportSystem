import streamlit as st


def navbar(go_to_page, current_page="dashboard"):
    """Collapsible navbar component for authenticated pages"""

    # Initialize sidebar state
    if "sidebar_collapsed" not in st.session_state:
        st.session_state.sidebar_collapsed = False

    # Custom CSS for navbar styling
    st.markdown("""
    <style>
    .nav-header {
        background: linear-gradient(90deg, #1f4e79, #2e6da4);
        color: white;
        padding: 1rem;
        border-radius: 8px;
        margin-bottom: 1rem;
        text-align: center;
    }
    .nav-item {
        padding: 0.5rem 1rem;
        margin: 0.2rem 0;
        border-radius: 6px;
        cursor: pointer;
        transition: all 0.3s ease;
    }
    .nav-item:hover {
        background-color: #f0f2f6;
    }
    .nav-item.active {
        background-color: #e8f4fd;
        border-left: 4px solid #1f4e79;
    }
    .logout-btn {
        background-color: #dc3545;
        color: white;
        border: none;
        padding: 0.5rem 1rem;
        border-radius: 6px;
        width: 100%;
        margin-top: 2rem;
    }
    </style>
    """, unsafe_allow_html=True)

    with st.sidebar:
        # Header
        st.markdown("""
        <div class="nav-header">
            <h3>📊 ARS</h3>
            <p style="margin: 0; font-size: 0.9em;">Automate Report System</p>
        </div>
        """, unsafe_allow_html=True)

        # User info
        user = st.session_state.get("user", {})
        username = user.get("username", "User")
        st.markdown(f"**Welcome, {username}!**")
        st.divider()

        # Navigation items
        nav_items = [
            {"name": "Dashboard", "icon": "📊", "page": "dashboard"},
            {"name": "Template Designer", "icon": "🎨", "page": "template_designer"},
            {"name": "SMTP Config", "icon": "📧", "page": "smtp_conf"},
            {"name": "Settings", "icon": "⚙️", "page": "settings"},
        ]

        for item in nav_items:
            active_class = "active" if current_page == item["page"] else ""

            if st.button(
                f"{item['icon']} {item['name']}",
                key=f"nav_{item['page']}",
                use_container_width=True,
                type="primary" if current_page == item["page"] else "secondary"
            ):
                go_to_page(item["page"])

        st.divider()

        # Logout button
        if st.button("🚪 Logout", use_container_width=True, type="secondary"):
            # Clear session state
            for key in list(st.session_state.keys()):
                if key not in ["db_initialized"]:
                    del st.session_state[key]
            go_to_page("home")
