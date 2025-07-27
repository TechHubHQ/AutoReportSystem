import streamlit as st
import asyncio
from app.ui.navbar import navbar
from app.core.interface.smtp_interface import setup_smtp, get_smtp_conf, update_smtp_conf
from app.integrations.email.email_client import EmailService


def smtp_conf(go_to_page):
    """SMTP configuration page with navbar"""
    navbar(go_to_page, "smtp_conf")

    st.markdown("# 📧 SMTP Configuration")
    st.markdown(
        "Configure your email server settings for sending automated reports.")

    st.divider()

    # Get current user
    user = st.session_state.get("user", {})
    user_email = user.get("email", "")

    with st.form("smtp_form"):
        st.subheader("🔧 Server Configuration")

        col1, col2 = st.columns(2)

        with col1:
            smtp_host = st.text_input(
                "SMTP Host *",
                placeholder="smtp.gmail.com",
                help="Your email provider's SMTP server address"
            )
            smtp_username = st.text_input(
                "Username *",
                placeholder="your-email@domain.com",
                help="Your email address or username"
            )

        with col2:
            smtp_port = st.number_input(
                "Port *",
                min_value=1,
                max_value=65535,
                value=587,
                help="Common ports: 587 (TLS), 465 (SSL), 25 (unsecured)"
            )
            smtp_password = st.text_input(
                "Password *",
                type="password",
                help="Your email password or app-specific password"
            )

        st.divider()

        # Common SMTP presets
        st.subheader("📨 Quick Setup")
        st.markdown("Select a common email provider:")

        col3, col4, col5, col6 = st.columns(4)

        with col3:
            if st.form_submit_button("📧 Gmail", use_container_width=True):
                st.session_state.preset_host = "smtp.gmail.com"
                st.session_state.preset_port = 587

        with col4:
            if st.form_submit_button("📧 Outlook", use_container_width=True):
                st.session_state.preset_host = "smtp-mail.outlook.com"
                st.session_state.preset_port = 587

        st.divider()

        # Form submission
        col7, col8, col9 = st.columns([1, 1, 1])

        with col7:
            test_connection = st.form_submit_button(
                "🔍 Test Connection",
                use_container_width=True
            )

        with col8:
            save_config = st.form_submit_button(
                "💾 Save Configuration",
                type="primary",
                use_container_width=True
            )

        with col9:
            clear_form = st.form_submit_button(
                "🗑️ Clear Form",
                use_container_width=True
            )

    # Handle form submissions
    if test_connection:
        if smtp_host and smtp_username and smtp_password:
            with st.spinner("Testing connection..."):
                try:
                    email_service = EmailService(
                        smtp_username, smtp_host, smtp_password, smtp_port)
                    st.success("✅ Connection test successful!")
                except Exception as e:
                    st.error(f"❌ Connection failed: {str(e)}")
        else:
            st.error("⚠️ Please fill in all required fields")

    if save_config:
        if smtp_host and smtp_username and smtp_password:
            try:
                asyncio.run(setup_smtp(smtp_host, smtp_port,
                            smtp_username, smtp_password))
                st.success("✅ SMTP configuration saved successfully!")
                st.info("📧 You can now send automated email reports")
            except Exception as e:
                st.error(f"❌ Error saving configuration: {str(e)}")
        else:
            st.error("⚠️ Please fill in all required fields")

    if clear_form:
        st.rerun()

    # Apply presets if selected
    if "preset_host" in st.session_state:
        st.rerun()
