from app.integrations.email.template_loader import load_template
from app.core.interface.template_interface import get_template_by_name
from app.core.interface.task_interface import get_weekly_tasks
from app.core.interface.smtp_interface import get_active_smtp_config
from app.core.interface.user_interface import get_user
from app.integrations.email.email_client import EmailService
from app.database.db_connector import get_db
from app.database.models import User, SMTPConf
from sqlalchemy import select


async def generate_report(user_id):
    """Generate weekly report content for specific user"""
    # Get user info
    user = await get_user(user_id)
    if not user:
        raise Exception(f"User {user_id} not found")

    # Get weekly tasks
    tasks = await get_weekly_tasks(user_id)

    # Categorize tasks
    accomplishments = [
        task.description for task in tasks if task.category == "accomplishments"]
    in_progress = [
        task.description for task in tasks if task.category == "in progress"]

    # Template context with dynamic sender info
    context = {
        'recipient_name': 'Santosh',
        'accomplishments': accomplishments,
        'in_progress': in_progress,
        'sender_name': user.username,
        'sender_title': user.userrole
    }

    # Load and render template
    rendered_content = await load_template(context, 'weekly_update_template.html')
    print(rendered_content)
    return rendered_content


async def send_weekly_report(to_email, user_id):
    """Send weekly report email for specific user"""
    # Get SMTP config
    smtp_config = await get_active_smtp_config(user_id)
    if not smtp_config:
        raise Exception(
            f"No active SMTP configuration found for user {user_id}")

    # Generate report content
    report_content = await generate_report(user_id)

    # Create email service
    email_service = EmailService(
        email=smtp_config.sender_email,
        host=smtp_config.smtp_host,
        pwd=smtp_config.smtp_password,
        port=smtp_config.smtp_port
    )

    # Send email
    await email_service.send_email(
        to_address=to_email,
        subject="Weekly Progress Report",
        content=report_content,
        html=True
    )


async def send_all_weeklies(to_email="santhosh.bommana@medicasapp.com"):
    """Send weekly reports for all users with SMTP config"""
    try:
        db = await get_db()
        result = await db.execute(
            select(User).join(SMTPConf, User.email == SMTPConf.sender_email)
            .where(SMTPConf.is_active == "True")
        )
        users = result.scalars().all()
        for user in users:
            try:
                await send_weekly_report("kalyankanuri497@gmail.com", user.id)
                print(f"Weekly report sent for user: {user.username}")
            except Exception as e:
                print(f"Failed to send report for user {user.username}: {e}")
    except Exception as e:
        print(f"Error sending weekly reports for all users: {e}")
        raise e
    finally:
        await db.close()
