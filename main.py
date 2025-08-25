import streamlit as st
import asyncio
import datetime
import os
from app.core.jobs.scheduler import ensure_scheduler_running
from app.security.backend_session_manager import BackendSessionManager
from app.security.middleware import apply_security_middleware
from app.security.route_protection import RouteProtection
from app.ui.smtp_conf import smtp_conf
from app.ui.template_designer import template_designer
from app.ui.user_settings import settings
from app.ui.dashboard import dashboard
from app.ui.jobs_dashboard import jobs_dashboard
from app.ui.job_email_config import job_email_config
from app.ui.system_monitor import system_monitor
from app.ui.signup import signup
from app.ui.login import login
from app.database.db_connector import init_db
from app.database.migrations import run_migrations
from app.config.logging_config import setup_logging, get_logger, log_to_console_and_file

# Initialize enhanced logging
print("🚀 Initializing AutoReportSystem...")
print(f"📁 Working directory: {os.getcwd()}")
print("📋 Setting up enhanced logging...")

setup_logging()
logger = get_logger(__name__)

# Force initial log to console and file
log_to_console_and_file("🚀 AutoReportSystem starting up...", "INFO")
log_to_console_and_file(f"📁 Working directory: {os.getcwd()}", "INFO")
log_to_console_and_file("📋 Enhanced logging system activated", "INFO")
log_to_console_and_file(
    "🔧 Using enhanced session-independent scheduler", "INFO")

st.set_page_config(
    page_title="Auto Report System",
    page_icon="ars.ico",
    layout="wide",
    initial_sidebar_state="expanded",
)


# Initialize DB and session system only once
if "db_initialized" not in st.session_state:
    log_to_console_and_file(
        "🗄️ Initializing database and session system...", "INFO")
    run_migrations()
    asyncio.run(init_db())
    BackendSessionManager.init_session_table()
    BackendSessionManager.cleanup_expired_sessions()
    st.session_state.db_initialized = True
    log_to_console_and_file(
        "✅ Database and session system initialized", "INFO")

# Initialize scheduler immediately on first load
if "scheduler_initialized" not in st.session_state:
    log_to_console_and_file("="*80, "INFO")
    log_to_console_and_file(
        "🚀 APPLICATION STARTUP - INITIALIZING ENHANCED SCHEDULER", "INFO")
    log_to_console_and_file("="*80, "INFO")

    logger.info("="*80)
    logger.info("🚀 APPLICATION STARTUP - INITIALIZING ENHANCED SCHEDULER")
    logger.info("="*80)
    logger.info(
        f"📅 Application startup time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(
        f"🌐 Streamlit session ID: {st.session_state.get('session_id', 'unknown')}")
    logger.info(f"🔧 Starting enhanced scheduler initialization...")

    log_to_console_and_file(
        f"📅 Application startup time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", "INFO")
    log_to_console_and_file(
        f"🔧 Starting enhanced scheduler initialization...", "INFO")
    log_to_console_and_file(
        "💡 This scheduler can start without database sessions", "INFO")

    # Start scheduler and wait for proper initialization
    log_to_console_and_file("⏳ Starting scheduler thread...", "INFO")
    scheduler_started = ensure_scheduler_running()

    # Give the scheduler more time to fully initialize
    import time
    time.sleep(3)

    # Check scheduler status after initialization
    from app.core.jobs.scheduler import is_scheduler_running
    scheduler_running = is_scheduler_running()

    if scheduler_started and scheduler_running:
        logger.info(
            "✅ Enhanced scheduler initialization completed successfully")
        logger.info("🎯 Background job processing is now active")
        log_to_console_and_file(
            "✅ Enhanced scheduler initialization completed successfully", "INFO")
        log_to_console_and_file(
            "🎯 Background job processing is now active", "INFO")
        log_to_console_and_file(
            "📋 Jobs will establish database connections only when they execute", "INFO")
        log_to_console_and_file(
            "📋 Check logs/scheduler.log for detailed scheduler information", "INFO")
    else:
        logger.error("❌ Enhanced scheduler initialization failed")
        logger.error("⚠️  Background jobs will not be processed")
        log_to_console_and_file(
            "❌ Enhanced scheduler initialization failed", "ERROR")
        log_to_console_and_file(
            "⚠️  Background jobs will not be processed", "ERROR")
        log_to_console_and_file(
            f"🔍 Debug: scheduler_started={scheduler_started}, scheduler_running={scheduler_running}", "ERROR")

    st.session_state.scheduler_initialized = True
    logger.info("="*80)
    log_to_console_and_file("="*80, "INFO")
else:
    # Ensure scheduler is still running on subsequent page loads
    logger.debug("🔄 Checking enhanced scheduler status on page reload...")
    from app.core.jobs.scheduler import is_scheduler_running
    scheduler_running = is_scheduler_running()
    if scheduler_running:
        logger.debug("✅ Enhanced scheduler is running properly")
    else:
        logger.warning(
            "⚠️  Enhanced scheduler check failed - attempting restart")
        log_to_console_and_file(
            "⚠️  Enhanced scheduler check failed - attempting restart", "WARNING")

# Always attempt to restore session from URL parameters or existing state
BackendSessionManager.restore_session()


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
        <h1 class="home-title">🏠 Auto Report System</h1>
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
    dashboard(go_to_page)

elif st.session_state.page == "jobs":
    # This route is protected by RouteProtection.check_route_access()
    jobs_dashboard(go_to_page)

elif st.session_state.page == "settings":
    # This route is protected by RouteProtection.check_route_access()
    settings(go_to_page)

elif st.session_state.page == "template_designer":
    # This route is protected by RouteProtection.check_route_access()
    template_designer(go_to_page)

elif st.session_state.page == "smtp_conf":
    # This route is protected by RouteProtection.check_route_access()
    smtp_conf(go_to_page)

elif st.session_state.page == "job_email_config":
    # This route is protected by RouteProtection.check_route_access()
    job_email_config(go_to_page)

elif st.session_state.page == "system_monitor":
    # This route is protected by RouteProtection.check_route_access()
    system_monitor(go_to_page)

else:
    # Unknown page - redirect to home
    st.error("❌ Page not found. Redirecting to home...")
    go_to_page("home")
