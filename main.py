import streamlit as st
import asyncio
from app.database.db_connector import init_db
from app.ui.login import login
from app.ui.signup import signup
from app.ui.dashboard import dashboard
from app.ui.user_settings import settings
from app.ui.template_designer import template_designer
from app.ui.smtp_conf import smtp_conf
from app.security.route_protection import RouteProtection
from app.security.middleware import apply_security_middleware
from app.security.backend_session_manager import BackendSessionManager
from app.security.session_validator import SessionValidator
from app.core.jobs.scheduler import run_scheduler
from app.core.interface.task_interface import get_weekly_tasks

st.set_page_config(page_title="Automate Report System", layout="wide")


# Initialize DB and session system only once
if "db_initialized" not in st.session_state:
    asyncio.run(init_db())
    BackendSessionManager.init_session_table()
    BackendSessionManager.cleanup_expired_sessions()
    run_scheduler()
    st.session_state.db_initialized = True

# Always attempt to restore session from URL parameters or existing state
# This ensures sessions persist through page refreshes
BackendSessionManager.restore_session()

# Validate and refresh session if needed (but don't be too aggressive)
if BackendSessionManager.is_authenticated():
    # Only validate if we're on a protected route
    current_page = st.session_state.get('page', 'home')
    if RouteProtection.is_route_protected(current_page):
        SessionValidator.validate_and_refresh()


# Apply security middleware
apply_security_middleware()


# Page router with URL update and security
def go_to_page(page_name):
    """Navigate to a page with proper security checks"""
    st.session_state.page = page_name
    st.query_params["page"] = page_name
    st.rerun()


# Enhanced page state manager with security
query_params = st.query_params
requested_page = query_params.get("page", None)

# Determine the target page
if requested_page:
    target_page = requested_page
elif "page" not in st.session_state:
    # Default page logic
    if RouteProtection.is_authenticated():
        target_page = "dashboard"
    else:
        target_page = "home"
else:
    target_page = st.session_state.page

# Security check for route access
if not RouteProtection.check_route_access(target_page, go_to_page):
    st.stop()  # Stop execution if access is denied

# Set the current page after security check
st.session_state.page = target_page


# Show selected page based on routing
if st.session_state.page == "home":
    # Custom CSS for enhanced home page styling
    st.markdown("""
    <style>
    .home-container {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 3rem 2rem;
        border-radius: 20px;
        text-align: center;
        color: white;
        margin: 2rem 0;
        box-shadow: 0 15px 35px rgba(0,0,0,0.1);
    }
    .home-title {
        font-size: 3.5rem;
        font-weight: 800;
        margin-bottom: 1rem;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    }
    .home-subtitle {
        font-size: 1.3rem;
        margin-bottom: 2rem;
        opacity: 0.9;
    }
    .feature-card {
        background: white;
        padding: 2rem;
        border-radius: 15px;
        box-shadow: 0 8px 25px rgba(0,0,0,0.1);
        margin: 1rem;
        text-align: center;
        transition: transform 0.3s ease;
    }
    .feature-card:hover {
        transform: translateY(-5px);
    }
    .feature-icon {
        font-size: 3rem;
        margin-bottom: 1rem;
    }
    .cta-button {
        background: linear-gradient(45deg, #FF6B6B, #4ECDC4);
        color: white;
        border: none;
        border-radius: 15px;
        padding: 1rem 2rem;
        font-size: 1.1rem;
        font-weight: 600;
        margin: 0.5rem;
        transition: all 0.3s ease;
    }
    .cta-button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 20px rgba(0,0,0,0.2);
    }
    .security-notice {
        background: rgba(76, 175, 80, 0.1);
        border: 1px solid rgba(76, 175, 80, 0.3);
        border-radius: 10px;
        padding: 1rem;
        margin: 1rem 0;
        text-align: center;
    }
    </style>
    """, unsafe_allow_html=True)

    # Enhanced home page layout
    st.markdown("""
    <div class="home-container">
        <h1 class="home-title">🏠 Automate Report System</h1>
        <p class="home-subtitle">Streamline your reporting workflow with intelligent automation</p>
    </div>
    """, unsafe_allow_html=True)

    # Security notice for authenticated users
    if RouteProtection.is_authenticated():
        user = RouteProtection.get_current_user()
        st.markdown(f"""
        <div class="security-notice">
            <h4 style="color: #4CAF50; margin: 0;">🔒 Welcome back, {user.get('username', 'User')}!</h4>
            <p style="margin: 0.5rem 0 0 0; color: #666;">You are securely logged in. Access your dashboard to continue.</p>
        </div>
        """, unsafe_allow_html=True)

        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            if st.button("📊 Go to Dashboard", use_container_width=True, type="primary"):
                go_to_page("dashboard")

    # Feature highlights
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""
        <div class="feature-card">
            <div class="feature-icon">📈</div>
            <h3 style="color: #333;">Smart Reports</h3>
            <p style="color: #666;">Generate reports automatically with customizable templates</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class="feature-card">
            <div class="feature-icon">⏰</div>
            <h3 style="color: #333;">Scheduled Tasks</h3>
            <p style="color: #666;">Set up automated report generation and delivery on your schedule</p>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown("""
        <div class="feature-card">
            <div class="feature-icon">📧</div>
            <h3 style="color: #333;">Email Integration</h3>
            <p style="color: #666;">Seamlessly deliver reports to stakeholders via email</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br><br>", unsafe_allow_html=True)

    # Call-to-action buttons (only show if not authenticated)
    if not RouteProtection.is_authenticated():
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown(
                "<h2 style='text-align: center; color: #333;'>Get Started Today</h2>", unsafe_allow_html=True)

            button_col1, button_col2 = st.columns(2)
            with button_col1:
                if st.button("🚀 Sign In", use_container_width=True, type="primary"):
                    go_to_page("login")
            with button_col2:
                if st.button("🎆 Create Account", use_container_width=True):
                    go_to_page("signup")

elif st.session_state.page == "login":
    login(go_to_page)

elif st.session_state.page == "signup":
    signup(go_to_page)

elif st.session_state.page == "dashboard":
    # This route is protected by RouteProtection.check_route_access()
    dashboard()

elif st.session_state.page == "settings":
    # This route is protected by RouteProtection.check_route_access()
    settings(go_to_page)

elif st.session_state.page == "template_designer":
    # This route is protected by RouteProtection.check_route_access()
    template_designer(go_to_page)

elif st.session_state.page == "smtp_conf":
    # This route is protected by RouteProtection.check_route_access()
    smtp_conf(go_to_page)

else:
    # Unknown page - redirect to home
    st.error("❌ Page not found. Redirecting to home...")
    go_to_page("home")


asyncio.run(get_weekly_tasks(2))
