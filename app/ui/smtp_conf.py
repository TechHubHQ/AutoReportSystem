import streamlit as st
import asyncio
from app.ui.navbar import navbar
from app.core.interface.smtp_interface import setup_smtp, get_smtp_conf, update_smtp_conf, get_active_smtp_config, get_all_smtp_configs, delete_smtp_conf
from app.integrations.email.email_client import EmailService
from app.ui.components.loader import LoaderContext
from app.core.services.encryption_service import EncryptionService


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
    user_id = user.get("id")

    # Display current SMTP configuration
    st.markdown("### 📋 Current SMTP Configuration")
    try:
        current_config = asyncio.run(get_active_smtp_config(user_id))
        if current_config:
            col1, col2, col3 = st.columns(3)
            with col1:
                st.info(f"**Host:** {current_config.smtp_host}")
                st.info(f"**Port:** {current_config.smtp_port}")
            with col2:
                st.info(f"**Username:** {current_config.smtp_username}")
                st.info(
                    f"**Status:** {'🟢 Active' if current_config.is_active == 'True' else '🔴 Inactive'}")
            with col3:
                st.info(f"**Sender:** {current_config.sender_email}")
                masked_pwd = '*' * \
                    len(current_config.smtp_password) if current_config.smtp_password else 'Not set'
                st.info(f"**Password:** {masked_pwd}")

            # Delete active configuration button
            if st.button("🗑️ Delete Active Configuration", key="delete_active_config"):
                try:
                    with LoaderContext("Deleting SMTP configuration...", "inline"):
                        asyncio.run(delete_smtp_conf(current_config.id, user_email))
                    st.success("✅ SMTP configuration deleted successfully!")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error deleting configuration: {str(e)}")
        else:
            st.warning(
                "⚠️ No active SMTP configuration found for your account. Please set up your email server below.")
    except Exception as e:
        st.error(f"❌ Error loading current configuration: {str(e)}")

    # Show all configurations if user has multiple
    if st.button("📋 View All Configurations"):
        st.session_state.show_all_configs = not st.session_state.get(
            "show_all_configs", False)

    if st.session_state.get("show_all_configs", False):
        try:
            all_configs = asyncio.run(get_all_smtp_configs(user_email))
            if all_configs:
                st.markdown("#### All SMTP Configurations (Your Account)")
                for i, config in enumerate(all_configs):
                    with st.expander(f"Config {i+1}: {config.smtp_host} ({'Active' if config.is_active == 'True' else 'Inactive'})"):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.write(f"**Host:** {config.smtp_host}")
                            st.write(f"**Port:** {config.smtp_port}")
                            st.write(f"**Username:** {config.smtp_username}")
                        with col2:
                            st.write(f"**Sender:** {config.sender_email}")
                            st.write(
                                f"**Status:** {'Active' if config.is_active == 'True' else 'Inactive'}")
                            masked_pwd = '*' * 8 if config.smtp_password else 'Not set'
                            st.write(f"**Password:** {masked_pwd}")

                        # Delete button for each configuration
                        if st.button("🗑️ Delete This Configuration", key=f"delete_config_{config.id}"):
                            try:
                                with LoaderContext("Deleting SMTP configuration...", "inline"):
                                    asyncio.run(delete_smtp_conf(config.id, user_email))
                                st.success("✅ Configuration deleted")
                                st.rerun()
                            except Exception as e:
                                st.error(f"❌ Error deleting configuration: {str(e)}")
            else:
                st.info("No additional configurations found for your account.")
        except Exception as e:
            st.error(f"Error loading configurations: {str(e)}")

    st.markdown("---")

    # Pre-fill form with current config if available
    default_host = current_config.smtp_host if 'current_config' in locals() and current_config else ""
    default_port = current_config.smtp_port if 'current_config' in locals() and current_config else 587
    default_username = current_config.smtp_username if 'current_config' in locals() and current_config else ""

    with st.form("smtp_form"):
        st.markdown("### 🔧 Server Configuration")

        col1, col2 = st.columns(2)

        with col1:
            smtp_host = st.text_input(
                "🌐 SMTP Host *",
                value=default_host,
                placeholder="smtp.gmail.com",
                help="Your email provider's SMTP server address"
            )
            smtp_username = st.text_input(
                "👤 Username *",
                value=default_username,
                placeholder="your-email@domain.com",
                help="Your email address or username"
            )

        with col2:
            smtp_port = st.number_input(
                "🔌 Port *",
                min_value=1,
                max_value=65535,
                value=default_port,
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
            if 'current_config' in locals() and current_config:
                save_config = st.form_submit_button(
                    "🔄 Update Configuration",
                    type="primary",
                    use_container_width=True
                )
            else:
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
    if 'test_connection' in locals() and test_connection:
        if smtp_host and smtp_username and smtp_password:
            with LoaderContext("🔍 Testing SMTP connection...", "inline"):
                try:
                    email_service = EmailService(
                        from_email=smtp_username,
                        host=smtp_host,
                        pwd=smtp_password,
                        port=smtp_port,
                        username=smtp_username
                    )
                    st.success("✅ Connection test successful!")
                except Exception as e:
                    st.error(f"❌ Connection failed: {str(e)}")
        else:
            st.error("⚠️ Please fill in all required fields")

    if 'save_config' in locals() and save_config:
        if smtp_host and smtp_username and smtp_password:
            action_text = "Updating" if ('current_config' in locals() and current_config) else "Saving"
            with LoaderContext(f"💾 {action_text} SMTP configuration...", "inline"):
                try:
                    # Debug information
                    st.write("🔍 Debug Info:")
                    st.write(f"- Host: {smtp_host}")
                    st.write(f"- Port: {smtp_port}")
                    st.write(f"- Username: {smtp_username}")
                    st.write(f"- Password length: {len(smtp_password) if smtp_password else 0}")
                    st.write(f"- User email: {user_email}")
                    
                    if 'current_config' in locals() and current_config:
                        # Update existing configuration
                        asyncio.run(update_smtp_conf(
                            current_config.id, smtp_host, smtp_port, smtp_username, smtp_password
                        ))
                        st.success(
                            "✅ SMTP configuration updated successfully!")
                    else:
                        # Create new configuration
                        asyncio.run(setup_smtp(smtp_host, smtp_port,
                                    smtp_username, smtp_password, user_email))
                        st.success("✅ SMTP configuration saved successfully!")
                    st.info("📧 You can now send automated email reports")
                    st.rerun()  # Refresh to show updated config
                except Exception as e:
                    st.error(f"❌ Error {action_text.lower()} configuration: {str(e)}")
                    st.error(f"🔍 Detailed error: {type(e).__name__}: {e}")
                    
                    # Additional debugging for encryption errors
                    if "encrypt" in str(e).lower() or "none" in str(e).lower():
                        st.error("🔐 This appears to be an encryption-related error.")
                        st.info("💡 Possible solutions:")
                        st.info("1. Check if FERNET_KEY is set in your .env file")
                        st.info("2. Restart the application to reload environment variables")
                        st.info("3. Ensure the password field is not empty")
        else:
            st.error("⚠️ Please fill in all required fields")
            if not smtp_password:
                st.error("🔒 Password field appears to be empty")

    if 'clear_form' in locals() and clear_form:
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
