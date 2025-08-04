import streamlit as st
from app.security.route_protection import RouteProtection
from app.security.session_manager import SessionManager
from app.ui.security_dashboard import show_security_status
from app.ui.components.session_status import show_compact_session_status


def navbar(go_to_page, current_page="dashboard"):
    """Collapsible navbar component for authenticated pages"""

    # Initialize sidebar state
    if "sidebar_collapsed" not in st.session_state:
        st.session_state.sidebar_collapsed = False

    # Custom CSS for enhanced navbar styling
    st.markdown("""
    <style>
    .nav-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 15px;
        margin-bottom: 1.5rem;
        text-align: center;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    .nav-header h3 {
        margin: 0;
        font-size: 1.8rem;
        font-weight: 700;
    }
    .nav-header p {
        margin: 0.5rem 0 0 0;
        font-size: 0.9rem;
        opacity: 0.9;
    }
    .user-welcome {
        background: rgba(102, 126, 234, 0.1);
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 1rem;
        text-align: center;
        border: 1px solid rgba(102, 126, 234, 0.2);
    }
    .stButton > button {
        border-radius: 10px;
        font-weight: 600;
        transition: all 0.3s ease;
        border: none;
    }
    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
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

        # Enhanced user info
        user = SessionManager.get_current_user() or {}
        username = user.get("username", "User")

        st.markdown(f"""
        <div class="user-welcome">
            <strong>👋 Welcome, {username}!</strong>
        </div>
        """, unsafe_allow_html=True)

        # Show compact session status
        show_compact_session_status()

        # Navigation items
        nav_items = [
            {"name": "Dashboard", "icon": "📊", "page": "dashboard"},
            {"name": "Template Designer", "icon": "🎨", "page": "template_designer"},
            {"name": "Job Management", "icon": "⚙️", "page": "job_management"},
            {"name": "SMTP Config", "icon": "📧", "page": "smtp_conf"},
            {"name": "Settings", "icon": "🔧", "page": "settings"},
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

        # Show security status
        show_security_status()

        st.divider()

        # Logout button
        if st.button("🚪 Logout", use_container_width=True, type="secondary"):
            RouteProtection.logout()
            st.success("👋 Successfully logged out!")
            go_to_page("home")


def show_navbar(go_to_page):
    """Simple navbar for dashboard pages"""
    navbar(go_to_page, "dashboard")
