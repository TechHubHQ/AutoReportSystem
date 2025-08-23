"""Job Email Configuration UI."""

import streamlit as st
import asyncio
from app.ui.navbar import navbar
from app.core.interface.job_email_config_interface import (
    create_job_email_config,
    get_job_email_config,
    get_all_job_email_configs,
    update_job_email_config,
    delete_job_email_config,
    get_available_job_types,
    get_email_config_schema
)
from app.ui.components.loader import LoaderContext


def apply_email_config_css():
    """Apply custom CSS for email configuration page."""
    st.markdown("""
    <style>
    .email-config-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 3rem 2rem;
        border-radius: 20px;
        margin-bottom: 2rem;
        text-align: center;
        box-shadow: 0 15px 35px rgba(0,0,0,0.1);
    }
    
    .config-card {
        background: linear-gradient(145deg, #ffffff 0%, #f8f9fa 100%);
        padding: 2rem;
        border-radius: 16px;
        box-shadow: 0 8px 32px rgba(0,0,0,0.1);
        border: 1px solid rgba(255,255,255,0.2);
        margin-bottom: 1.5rem;
        transition: all 0.3s ease;
    }
    
    .config-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 15px 40px rgba(0,0,0,0.15);
    }
    
    .job-type-badge {
        display: inline-block;
        padding: 0.5rem 1rem;
        border-radius: 25px;
        font-size: 0.9rem;
        font-weight: 600;
        margin: 0.5rem 0.5rem 0.5rem 0;
    }
    
    .weekly-badge {
        background: rgba(76, 175, 80, 0.1);
        color: #4CAF50;
        border: 1px solid rgba(76, 175, 80, 0.3);
    }
    
    .monthly-badge {
        background: rgba(33, 150, 243, 0.1);
        color: #2196F3;
        border: 1px solid rgba(33, 150, 243, 0.3);
    }
    
    .lifecycle-badge {
        background: rgba(255, 152, 0, 0.1);
        color: #ff9800;
        border: 1px solid rgba(255, 152, 0, 0.3);
    }
    
    .status-enabled {
        color: #4CAF50;
        font-weight: 600;
    }
    
    .status-disabled {
        color: #f44336;
        font-weight: 600;
    }
    
    .form-section {
        background: rgba(102, 126, 234, 0.05);
        padding: 2rem;
        border-radius: 15px;
        border: 1px solid rgba(102, 126, 234, 0.1);
        margin-bottom: 2rem;
    }
    
    /* Modal styles */
    .modal-overlay {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0, 0, 0, 0.5);
        z-index: 1000;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    
    .modal-content {
        background: white;
        border-radius: 20px;
        padding: 2rem;
        max-width: 800px;
        width: 90%;
        max-height: 90vh;
        overflow-y: auto;
        box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
        position: relative;
    }
    
    .modal-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 2rem;
        padding-bottom: 1rem;
        border-bottom: 2px solid #f0f0f0;
    }
    
    .modal-title {
        font-size: 1.5rem;
        font-weight: 600;
        color: #333;
        margin: 0;
    }
    
    .modal-close {
        background: none;
        border: none;
        font-size: 1.5rem;
        cursor: pointer;
        color: #666;
        padding: 0.5rem;
        border-radius: 50%;
        transition: all 0.3s ease;
    }
    
    .modal-close:hover {
        background: #f0f0f0;
        color: #333;
    }
    </style>
    """, unsafe_allow_html=True)


def render_job_type_badge(job_id: str) -> str:
    """Render a badge for the job type."""
    badge_classes = {
        "weekly_reporter": "weekly-badge",
        "monthly_reporter": "monthly-badge",
        "task_lifecycle_manager": "lifecycle-badge"
    }

    badge_icons = {
        "weekly_reporter": "📅",
        "monthly_reporter": "📊",
        "task_lifecycle_manager": "🔄"
    }

    badge_class = badge_classes.get(job_id, "weekly-badge")
    badge_icon = badge_icons.get(job_id, "📧")
    display_name = job_id.replace("_", " ").title()

    return f'<span class="job-type-badge {badge_class}">{badge_icon} {display_name}</span>'


@st.dialog("Edit Email Configuration")
def edit_config_modal(job_id: str, config):
    """Modal dialog for editing email configuration."""
    user = st.session_state.get("user", {})
    user_id = user.get("id")
    
    if not user_id:
        st.error("❌ User not found in session")
        return
    
    # Get job info
    job_types = get_available_job_types()
    job_info = next((jt for jt in job_types if jt["id"] == job_id), {"name": job_id})
    
    st.markdown(f"**Editing configuration for:** {job_info['name']}")
    
    with st.form("edit_email_config_modal"):
        col1, col2 = st.columns(2)
        
        with col1:
            enabled = st.checkbox(
                "✅ Enable Email Notifications",
                value=config.enabled,
                help="Enable or disable email notifications for this job"
            )
            
            recipient = st.text_input(
                "📧 Recipient Email *",
                value=config.recipient,
                placeholder="recipient@example.com",
                help="Email address to send reports to"
            )
            
            recipient_name = st.text_input(
                "👤 Recipient Name",
                value=config.recipient_name or "",
                placeholder="John Doe",
                help="Name of the recipient for personalization"
            )
        
        with col2:
            subject = st.text_input(
                "📝 Email Subject *",
                value=config.subject,
                help="Subject line for the email"
            )
            
            template = st.text_input(
                "📄 Template File",
                value=config.template or "",
                help="Email template file name (optional)"
            )
            
            max_retries = st.number_input(
                "🔄 Max Retries",
                min_value=0,
                max_value=10,
                value=config.max_retries,
                help="Maximum number of retry attempts for failed sends"
            )
        
        st.markdown("#### ⚙️ Advanced Settings")
        
        adv_col1, adv_col2 = st.columns(2)
        
        with adv_col1:
            send_empty_reports = st.checkbox(
                "📭 Send Empty Reports",
                value=config.send_empty_reports,
                help="Send reports even when no data is available"
            )
            
            html_format = st.checkbox(
                "🎨 HTML Format",
                value=config.html_format,
                help="Send emails in HTML format"
            )
        
        with adv_col2:
            retry_failed_sends = st.checkbox(
                "🔄 Retry Failed Sends",
                value=config.retry_failed_sends,
                help="Automatically retry failed email sends"
            )
        
        # Form buttons
        col1, col2, col3 = st.columns(3)
        
        with col1:
            submit_button = st.form_submit_button("💾 Update Configuration", type="primary")
        
        with col2:
            cancel_button = st.form_submit_button("❌ Cancel")
        
        with col3:
            if st.form_submit_button("🗑️ Delete", type="secondary"):
                if st.session_state.get(f"confirm_delete_modal_{job_id}", False):
                    try:
                        asyncio.run(delete_job_email_config(job_id, user_id))
                        st.success("✅ Configuration deleted successfully!")
                        st.session_state[f"confirm_delete_modal_{job_id}"] = False
                        st.session_state[f"show_edit_modal_{job_id}"] = False
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Error deleting configuration: {str(e)}")
                else:
                    st.session_state[f"confirm_delete_modal_{job_id}"] = True
                    st.warning("⚠️ Click again to confirm deletion")
    
    # Handle form submission
    if submit_button:
        if not recipient or not subject:
            st.error("⚠️ Please fill in all required fields (marked with *)")
            return
        
        try:
            with LoaderContext("Updating email configuration...", "inline"):
                asyncio.run(update_job_email_config(
                    job_id,
                    user_id,
                    enabled=enabled,
                    recipient=recipient,
                    subject=subject,
                    template=template or None,
                    recipient_name=recipient_name or None,
                    send_empty_reports=send_empty_reports,
                    html_format=html_format,
                    retry_failed_sends=retry_failed_sends,
                    max_retries=max_retries
                ))
                st.success("✅ Email configuration updated successfully!")
                st.session_state[f"show_edit_modal_{job_id}"] = False
                st.rerun()
        
        except Exception as e:
            st.error(f"❌ Error updating configuration: {str(e)}")
    
    if cancel_button:
        st.session_state[f"show_edit_modal_{job_id}"] = False
        st.rerun()


async def render_existing_configs():
    """Render existing email configurations."""
    user = st.session_state.get("user", {})
    user_id = user.get("id")

    if not user_id:
        st.error("❌ User not found in session")
        return

    st.markdown("### 📋 Current Email Configurations")

    with LoaderContext("Loading email configurations...", "inline"):
        configs = await get_all_job_email_configs(user_id)

    if not configs:
        st.markdown("""
        <div style="text-align: center; padding: 3rem 2rem; 
                   background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%); 
                   border-radius: 20px; margin: 2rem 0; border: 2px dashed #dee2e6;">
            <div style="font-size: 3rem; margin-bottom: 1rem;">📧</div>
            <h3 style="color: #666; margin-bottom: 1rem;">No Email Configurations Yet</h3>
            <p style="color: #888; margin-bottom: 2rem; font-size: 1.1rem;">
                Configure email settings for your automated jobs below.
            </p>
        </div>
        """, unsafe_allow_html=True)
        return

    # Group configs by job type
    job_types = get_available_job_types()
    job_type_map = {jt["id"]: jt for jt in job_types}

    for config in configs:
        job_info = job_type_map.get(config.job_id, {
            "name": config.job_id.replace("_", " ").title(),
            "description": "Custom job configuration"
        })

        status_class = "status-enabled" if config.enabled else "status-disabled"
        status_text = "✅ Enabled" if config.enabled else "❌ Disabled"

        st.markdown(f"""
        <div class="config-card">
            <div style="display: flex; justify-content: between; align-items: center; margin-bottom: 1rem;">
                <div>
                    {render_job_type_badge(config.job_id)}
                    <span class="{status_class}" style="margin-left: 1rem;">{status_text}</span>
                </div>
            </div>
            <h4 style="margin: 0.5rem 0; color: #333;">{job_info['name']}</h4>
            <p style="color: #666; margin-bottom: 1rem;">{job_info['description']}</p>
        """, unsafe_allow_html=True)

        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown(f"""
            <div style="background: #f8f9fa; padding: 1rem; border-radius: 8px;">
                <strong>📧 Recipient</strong><br>
                <span style="color: #666;">{config.recipient}</span>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            st.markdown(f"""
            <div style="background: #f8f9fa; padding: 1rem; border-radius: 8px;">
                <strong>📝 Subject</strong><br>
                <span style="color: #666;">{config.subject}</span>
            </div>
            """, unsafe_allow_html=True)

        with col3:
            st.markdown(f"""
            <div style="background: #f8f9fa; padding: 1rem; border-radius: 8px;">
                <strong>👤 Recipient Name</strong><br>
                <span style="color: #666;">{config.recipient_name or 'Not set'}</span>
            </div>
            """, unsafe_allow_html=True)

        # Action buttons
        action_col1, action_col2, action_col3 = st.columns([1, 1, 2])

        with action_col1:
            if st.button("✏️ Edit", key=f"edit_{config.id}"):
                st.session_state[f"show_edit_modal_{config.job_id}"] = True
                st.rerun()

        with action_col2:
            if st.button("🗑️ Delete", key=f"delete_{config.id}"):
                if st.session_state.get(f"confirm_delete_{config.id}", False):
                    try:
                        with LoaderContext("Deleting configuration...", "inline"):
                            await delete_job_email_config(config.job_id, user_id)
                        st.success("✅ Configuration deleted successfully!")
                        st.session_state[f"confirm_delete_{config.id}"] = False
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Error deleting configuration: {str(e)}")
                else:
                    st.session_state[f"confirm_delete_{config.id}"] = True
                    st.warning("⚠️ Click again to confirm deletion")

        st.markdown("</div>", unsafe_allow_html=True)


async def render_config_form():
    """Render the email configuration form for new configurations."""
    user = st.session_state.get("user", {})
    user_id = user.get("id")

    if not user_id:
        st.error("❌ User not found in session")
        return

    st.markdown("### ➕ Add New Email Configuration")

    with st.form("email_config_form"):
        st.markdown('<div class="form-section">', unsafe_allow_html=True)

        # Job selection
        job_types = get_available_job_types()
        job_options = {
            jt["id"]: f"{jt['name']} - {jt['description']}" for jt in job_types}

        # Filter out jobs that already have configurations
        existing_configs = await get_all_job_email_configs(user_id)
        existing_job_ids = {config.job_id for config in existing_configs}
        available_jobs = {
            k: v for k, v in job_options.items() if k not in existing_job_ids}

        if not available_jobs:
            st.warning(
                "⚠️ All available job types already have email configurations.")
            st.markdown("</div>", unsafe_allow_html=True)
            return

        selected_job_id = st.selectbox(
            "📋 Select Job Type",
            options=list(available_jobs.keys()),
            format_func=lambda x: available_jobs[x],
            help="Choose which job you want to configure email settings for"
        )

        st.markdown("#### 📧 Email Settings")

        col1, col2 = st.columns(2)

        with col1:
            enabled = st.checkbox(
                "✅ Enable Email Notifications",
                value=True,
                help="Enable or disable email notifications for this job"
            )

            recipient = st.text_input(
                "📧 Recipient Email *",
                value="",
                placeholder="recipient@example.com",
                help="Email address to send reports to"
            )

            recipient_name = st.text_input(
                "👤 Recipient Name",
                value="",
                placeholder="John Doe",
                help="Name of the recipient for personalization"
            )

        with col2:
            subject = st.text_input(
                "📝 Email Subject *",
                value=f"{selected_job_id.replace('_', ' ').title()} Report",
                help="Subject line for the email"
            )

            template = st.text_input(
                "📄 Template File",
                value=f"{selected_job_id}_template.html",
                help="Email template file name (optional)"
            )

            max_retries = st.number_input(
                "🔄 Max Retries",
                min_value=0,
                max_value=10,
                value=3,
                help="Maximum number of retry attempts for failed sends"
            )

        st.markdown("#### ⚙️ Advanced Settings")

        adv_col1, adv_col2 = st.columns(2)

        with adv_col1:
            send_empty_reports = st.checkbox(
                "📭 Send Empty Reports",
                value=False,
                help="Send reports even when no data is available"
            )

            html_format = st.checkbox(
                "🎨 HTML Format",
                value=True,
                help="Send emails in HTML format"
            )

        with adv_col2:
            retry_failed_sends = st.checkbox(
                "🔄 Retry Failed Sends",
                value=True,
                help="Automatically retry failed email sends"
            )

        st.markdown("</div>", unsafe_allow_html=True)

        # Form buttons
        button_col1, button_col2, button_col3 = st.columns([1, 1, 1])

        with button_col1:
            submit_button = st.form_submit_button(
                "➕ Create Configuration", type="primary")

        with button_col2:
            cancel_button = st.form_submit_button("❌ Cancel")

        with button_col3:
            clear_button = st.form_submit_button("🗑️ Clear Form")

    # Handle form submission
    if submit_button:
        if not recipient or not subject:
            st.error("⚠️ Please fill in all required fields (marked with *)")
            return

        try:
            with LoaderContext("Creating email configuration...", "inline"):
                await create_job_email_config(
                    selected_job_id,
                    user_id,
                    recipient,
                    subject,
                    template or None,
                    recipient_name or None,
                    enabled,
                    send_empty_reports,
                    html_format,
                    retry_failed_sends,
                    max_retries
                )
                st.success("✅ Email configuration created successfully!")
                st.rerun()

        except Exception as e:
            st.error(f"❌ Error creating configuration: {str(e)}")

    if cancel_button:
        st.rerun()

    if clear_button:
        st.rerun()


def job_email_config(go_to_page):
    """Main job email configuration page."""
    apply_email_config_css()

    navbar(go_to_page, "job_email_config")

    # Header
    st.markdown("""
    <div class="email-config-header">
        <h1 style="margin: 0; font-size: 2.5rem;">📧 Job Email Configuration</h1>
        <p style="margin: 0.5rem 0 0 0; font-size: 1.1rem; opacity: 0.9;">
            Configure email settings for automated job notifications and reports
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Check if user is logged in
    user = st.session_state.get("user", {})
    if not user:
        st.error("❌ Please log in to access email configuration settings")
        return

    # Check for modal display
    user_id = user.get("id")
    modal_job_id = None
    for key in st.session_state:
        if key.startswith("show_edit_modal_") and st.session_state[key]:
            modal_job_id = key.replace("show_edit_modal_", "")
            break
    
    if modal_job_id:
        # Get the configuration for the modal
        try:
            config = asyncio.run(get_job_email_config(modal_job_id, user_id))
            if config:
                edit_config_modal(modal_job_id, config)
        except Exception as e:
            st.error(f"❌ Error loading configuration: {str(e)}")
            st.session_state[f"show_edit_modal_{modal_job_id}"] = False

    # Main content
    tab1, tab2 = st.tabs(["📋 Current Configurations", "➕ Add Configuration"])

    with tab1:
        asyncio.run(render_existing_configs())

    with tab2:
        asyncio.run(render_config_form())


if __name__ == "__main__":
    job_email_config(lambda x: None)
