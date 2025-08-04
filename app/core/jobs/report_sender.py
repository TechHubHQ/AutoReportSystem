"""
Report Sender for AutomateReportSystem

Handles sending reports using dynamically selected templates and content.
"""

from typing import List, Optional, Dict, Any
from app.integrations.email.email_client import EmailService
from app.core.jobs.utils.template_loader import load_template_by_id
from app.core.interface.smtp_interface import get_active_smtp_config


async def send_report(
    template_id: int,
    content_type: str = "all",
    user_id: Optional[int] = None,
    recipients: Optional[List[str]] = None,
    subject_override: Optional[str] = None
) -> bool:
    """
    Send a report using a template and content type

    Args:
        template_id: ID of the template to use
        content_type: Type of content to include (all, weekly, monthly, etc.)
        user_id: User ID for personalized content
        recipients: List of email addresses to send to
        subject_override: Optional subject line override

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        print(f"🚀 Starting report generation...")
        print(f"   Template ID: {template_id}")
        print(f"   Content Type: {content_type}")
        print(f"   Recipients: {len(recipients) if recipients else 0}")

        # Validate inputs
        if not template_id:
            raise ValueError("Template ID is required")

        if not recipients:
            raise ValueError("At least one recipient is required")

        # Load template and render with content
        print("📄 Loading template...")
        template_result = await load_template_by_id(template_id, user_id=user_id)

        if not template_result:
            raise ValueError(f"Failed to load template with ID {template_id}")

        # Get rendered content
        subject = subject_override or template_result['subject']
        content = template_result['content']
        template_name = template_result.get(
            'template_name', f'Template {template_id}')

        print(f"✅ Template '{template_name}' loaded successfully")

        # Get SMTP configuration
        print("📧 Getting SMTP configuration...")
        smtp_config = await get_active_smtp_config(user_id)

        if not smtp_config:
            raise ValueError("No active SMTP configuration found")

        # Initialize email service
        email_service = EmailService(
            email=smtp_config.smtp_username,
            host=smtp_config.smtp_host,
            pwd=smtp_config.smtp_password,
            port=smtp_config.smtp_port
        )

        print(f"📤 Sending emails to {len(recipients)} recipients...")

        # Send emails to all recipients
        success_count = 0
        failed_recipients = []

        for recipient in recipients:
            try:
                await email_service.send_email(
                    to_address=recipient,
                    subject=subject,
                    content=content
                )
                success_count += 1
                print(f"   ✅ Sent to {recipient}")
            except Exception as e:
                failed_recipients.append(recipient)
                print(f"   ❌ Failed to send to {recipient}: {str(e)}")

        # Report results
        if success_count > 0:
            print(
                f"🎉 Report sent successfully to {success_count}/{len(recipients)} recipients")
            if failed_recipients:
                print(f"⚠️  Failed recipients: {', '.join(failed_recipients)}")
            return True
        else:
            print(f"❌ Failed to send to all recipients")
            return False

    except Exception as e:
        print(f"❌ report sending failed: {str(e)}")
        return False


async def send_weekly_report(template_id: int, user_id: Optional[int] = None, recipients: Optional[List[str]] = None) -> bool:
    """Send weekly report using specified template"""
    return await send_report(
        template_id=template_id,
        content_type="weekly",
        user_id=user_id,
        recipients=recipients
    )


async def send_monthly_report(template_id: int, user_id: Optional[int] = None, recipients: Optional[List[str]] = None) -> bool:
    """Send monthly report using specified template"""
    return await send_report(
        template_id=template_id,
        content_type="monthly",
        user_id=user_id,
        recipients=recipients
    )


async def send_custom_report(
    template_id: int,
    content_type: str,
    user_id: Optional[int] = None,
    recipients: Optional[List[str]] = None,
    subject_override: Optional[str] = None
) -> bool:
    """Send custom report with specified parameters"""
    return await send_report(
        template_id=template_id,
        content_type=content_type,
        user_id=user_id,
        recipients=recipients,
        subject_override=subject_override
    )


# Utility functions for job configuration
def create_email_job_config(template_id: int, content_type: str, recipients: List[str], user_id: Optional[int] = None) -> Dict[str, Any]:
    """Create job configuration for email-based jobs"""
    return {
        'job_type': 'email_report',
        'template_id': template_id,
        'content_type': content_type,
        'recipients': recipients,
        'user_id': user_id
    }


def validate_job_config(config: Dict[str, Any]) -> bool:
    """Validate job configuration"""
    required_fields = ['template_id', 'recipients']
    return all(field in config and config[field] for field in required_fields)


# Legacy compatibility functions
async def send_w_report(template_id: int, recipients: List[str], user_id: Optional[int] = None):
    """Legacy weekly report function with template"""
    return await send_weekly_report(template_id, user_id, recipients)


async def send_m_report(template_id: int, recipients: List[str], user_id: Optional[int] = None):
    """Legacy monthly report function with template"""
    return await send_monthly_report(template_id, user_id, recipients)
