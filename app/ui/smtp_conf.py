import streamlit as st
import asyncio
from app.ui.navbar import navbar
from app.core.interface.smtp_interface import setup_smtp, get_smtp_conf, update_smtp_conf
from app.integrations.email.email_client import EmailService
from app.ui.components.loader import LoaderContext


def smtp_conf(go_to_page):
    """SMTP configuration page with navbar"""
    st.markdown("""
    <style>
    .smtp-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        color: white;
        text-align: center;
    }
    .smtp-card {
        background: white;
        padding: 1.5rem;
        border-radius: 15px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        margin-bottom: 1rem;
    }
    .stForm {
        background: rgba(102, 126, 234, 0.05);
        padding: 2rem;
        border-radius: 15px;
        border: 1px solid rgba(102, 126, 234, 0.1);
    }
    </style>
    """, unsafe_allow_html=True)

    navbar(go_to_page, "smtp_conf")

    st.markdown("""
    <div class="smtp-header">
        <h1 style="margin: 0; font-size: 2.5rem;">📧 SMTP Configuration</h1>
        <p style="margin: 0.5rem 0 0 0; font-size: 1.1rem; opacity: 0.9;">Configure your email server settings for sending automated reports</p>
    </div>
    """, unsafe_allow_html=True)

    # Get current user
    user = st.session_state.get("user", {})
    user_email = user.get("email", "")

    with st.form("smtp_form"):
        st.markdown("### 🔧 Server Configuration")

        col1, col2 = st.columns(2)

        with col1:
            smtp_host = st.text_input(
                "🌐 SMTP Host *",
                placeholder="smtp.gmail.com",
                help="Your email provider's SMTP server address"
            )
            smtp_username = st.text_input(
                "👤 Username *",
                placeholder="your-email@domain.com",
                help="Your email address or username"
            )

        with col2:
            smtp_port = st.number_input(
                "🔌 Port *",
                min_value=1,
                max_value=65535,
                value=587,
                help="Common ports: 587 (TLS), 465 (SSL), 25 (unsecured)"
            )
            smtp_password = st.text_input(
                "🔒 Password *",
                type="password",
                help="Your email password or app-specific password"
            )

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("### 🔑 App Password Instructions")
        st.markdown("Click on your email provider for setup instructions:")

        col3, col4 = st.columns(2)

        with col3:
            if st.form_submit_button("📧 Gmail Setup", use_container_width=True):
                st.session_state.show_gmail_instructions = True

        with col4:
            if st.form_submit_button("📧 Outlook Setup", use_container_width=True):
                st.session_state.show_outlook_instructions = True

        st.markdown("<br>", unsafe_allow_html=True)

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
            with LoaderContext("🔍 Testing SMTP connection...", "inline"):
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
            with LoaderContext("💾 Saving SMTP configuration...", "inline"):
                try:
                    asyncio.run(setup_smtp(smtp_host, smtp_port,
                                smtp_username, smtp_password, user_email))
                    st.success("✅ SMTP configuration saved successfully!")
                    st.info("📧 You can now send automated email reports")
                except Exception as e:
                    st.error(f"❌ Error saving configuration: {str(e)}")
        else:
            st.error("⚠️ Please fill in all required fields")

    if clear_form:
        st.rerun()

    # Show Gmail instructions if requested
    if st.session_state.get("show_gmail_instructions", False):
        st.markdown("### 📧 Gmail App Password Setup")
        with st.container():
            st.markdown("""
            <div style="background: #f8f9fa; padding: 1.5rem; border-radius: 10px; border-left: 4px solid #4285f4; max-height: 400px; overflow-y: auto;">
                <h4 style="color: #4285f4; margin-top: 0;">Gmail App Password Setup:</h4>
                <ol style="line-height: 1.6;">
                    <li><strong>Visit App Passwords:</strong>
                        <ul>
                            <li>Go to <a href="https://myaccount.google.com/apppasswords" target="_blank" style="color: #4285f4;">myaccount.google.com/apppasswords</a></li>
                            <li>Sign in to your Google account if prompted</li>
                        </ul>
                    </li>
                    <li><strong>Create App Password:</strong>
                        <ul>
                            <li>Enter "Automate Report System" in the app name field</li>
                            <li>Click "Create" to generate a 16-character password</li>
                        </ul>
                    </li>
                    <li><strong>Configure SMTP:</strong>
                        <ul>
                            <li>Copy the generated app password</li>
                            <li>Use it in the password field above (not your regular Gmail password)</li>
                        </ul>
                    </li>
                </ol>
                <p><strong>Gmail SMTP Settings:</strong></p>
                <ul>
                    <li>Host: smtp.gmail.com</li>
                    <li>Port: 587</li>
                    <li>Username: your-email@gmail.com</li>
                    <li>Password: [16-character app password]</li>
                </ul>
                <p style="margin-bottom: 0; color: #666;"><em>Note: 2-Factor Authentication must be enabled on your Google account to use app passwords.</em></p>
            </div>
            """, unsafe_allow_html=True)
        if st.button("❌ Close Instructions"):
            st.session_state.show_gmail_instructions = False
            st.rerun()

    # Show Outlook instructions if requested
    if st.session_state.get("show_outlook_instructions", False):
        st.markdown("### 📧 Outlook App Password Setup")
        with st.container():
            st.markdown("""
            <div style="background: #f8f9fa; padding: 1.5rem; border-radius: 10px; border-left: 4px solid #0078d4; max-height: 400px; overflow-y: auto;">
                <h4 style="color: #0078d4; margin-top: 0;">How to Generate Outlook App Password:</h4>
                <ol style="line-height: 1.6;">
                    <li><strong>Enable 2-Factor Authentication:</strong>
                        <ul>
                            <li>Sign in to your Microsoft account</li>
                            <li>Go to Security > Advanced security options</li>
                            <li>Turn on two-step verification if not enabled</li>
                        </ul>
                    </li>
                    <li><strong>Generate App Password:</strong>
                        <ul>
                            <li>In Security settings, find "App passwords"</li>
                            <li>Click "Create a new app password"</li>
                            <li>Enter "Automate Report System" as the name</li>
                            <li>Click "Next" to generate</li>
                        </ul>
                    </li>
                    <li><strong>Use the Generated Password:</strong>
                        <ul>
                            <li>Copy the generated password</li>
                            <li>Use this password in the SMTP configuration above</li>
                            <li>Use your full Outlook email as username</li>
                        </ul>
                    </li>
                </ol>
                <p><strong>SMTP Settings for Outlook:</strong></p>
                <ul>
                    <li>Host: smtp-mail.outlook.com</li>
                    <li>Port: 587 (TLS)</li>
                    <li>Username: your-email@outlook.com</li>
                    <li>Password: [Generated App Password]</li>
                </ul>
                <p style="margin-bottom: 0;"><a href="https://support.microsoft.com/en-us/account-billing/manage-app-passwords-for-two-step-verification-d6dc8c6d-4bf7-4851-ad95-6d07799387e9" target="_blank" style="color: #0078d4; text-decoration: none;">🔗 Official Outlook App Password Guide</a></p>
            </div>
            """, unsafe_allow_html=True)
        if st.button("❌ Close Instructions", key="close_outlook"):
            st.session_state.show_outlook_instructions = False
            st.rerun()
