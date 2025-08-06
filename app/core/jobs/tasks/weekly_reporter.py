from datetime import datetime, timedelta

from sqlalchemy import select

from app.integrations.email.template_loader import load_template
from app.core.interface.task_interface import get_weekly_tasks
from app.core.interface.smtp_interface import get_active_smtp_config
from app.core.interface.user_interface import get_user
from app.integrations.email.email_client import EmailService
from app.database.db_connector import get_db
from app.database.models import User, SMTPConf
from app.config.logging_config import get_logger

logger = get_logger(__name__)


async def generate_report(user_id):
    """Generate weekly report content for specific user"""
    user = await get_user(user_id)
    if not user:
        raise Exception(f"User {user_id} not found")

    tasks = await get_weekly_tasks(user_id)

    accomplishments = [
        task.description for task in tasks if task.category == "accomplishments"]
    in_progress = [
        task.description for task in tasks if task.category == "in progress"]

    context = {
        'recipient_name': 'Santosh',
        'accomplishments': accomplishments,
        'in_progress': in_progress,
        'sender_name': user.username,
        'sender_title': user.userrole
    }

    rendered_content = await load_template(context, 'weekly_update_template.html')
    logger.debug("Weekly report content generated")
    return rendered_content


async def send_report(to_email, user_id):
    """Send weekly report email for specific user"""
    smtp_config = await get_active_smtp_config(user_id)
    if not smtp_config:
        raise Exception(
            f"No active SMTP configuration found for user {user_id}")

    report_content = await generate_report(user_id)

    email_service = EmailService(
        email=smtp_config.sender_email,
        host=smtp_config.smtp_host,
        pwd=smtp_config.smtp_password,
        port=smtp_config.smtp_port
    )

    await email_service.send_email(
        to_address=to_email,
        subject="Weekly Progress Report",
        content=report_content,
        html=True
    )


async def send_weekly_report(to_email="santhosh.bommana@medicasapp.com"):
    """Send weekly reports only on 1st, 2nd, or 3rd Friday of the month"""
    try:
        # Check if today is 1st, 2nd, or 3rd Friday
        today = datetime.utcnow().date()

        if today.weekday() != 4:  # 4 = Friday
            logger.info("Today is not Friday. Skipping weekly report.")
            return

        # Count how many Fridays have occurred so far this month
        count = 0
        current_day = today.replace(day=1)
        while current_day <= today:
            if current_day.weekday() == 4:
                count += 1
            current_day += timedelta(days=1)

        if count > 3:
            logger.info(
                "Today is not 1st, 2nd, or 3rd Friday. Skipping weekly report.")
            return

        # Continue only if 1st, 2nd, or 3rd Friday
        db = await get_db()
        result = await db.execute(
            select(User).join(SMTPConf, User.email == SMTPConf.sender_email)
            .where(SMTPConf.is_active == "True")
        )
        users = result.scalars().all()

        for user in users:
            try:
                await send_report(to_email, user.id)
                logger.info(f"Weekly report sent for user: {user.username}")
            except Exception as e:
                logger.error(
                    f"Failed to send report for user {user.username}: {e}")
    except Exception as e:
        logger.error(f"Error sending weekly reports for all users: {e}")
        raise e
    finally:
        await db.close()
