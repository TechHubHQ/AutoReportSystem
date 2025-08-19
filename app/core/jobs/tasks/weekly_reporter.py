from datetime import datetime, timedelta

from sqlalchemy import select

from app.integrations.email.template_loader import load_template
from app.core.interface.task_interface import get_weekly_tasks, get_tasks_for_weekly_report
from app.core.interface.smtp_interface import get_active_smtp_config
from app.core.interface.user_interface import get_user
from app.integrations.email.email_client import EmailService
from app.database.db_connector import get_db
from app.database.models import User, SMTPConf
from app.config.logging_config import get_logger
from app.core.utils.datetime_utils import is_last_friday, get_date_in_timezone
from app.core.interface.job_tracking_interface import JobExecutionTracker

logger = get_logger(__name__)


async def generate_report(user_id):
    """Generate weekly report content for specific user"""
    user = await get_user(user_id)
    if not user:
        raise Exception(f"User {user_id} not found")

    # Use enhanced function that includes status change tracking
    try:
        task_data = await get_tasks_for_weekly_report(user_id)
        accomplishments = task_data['accomplishments']
        in_progress = task_data['in_progress']
        status_changed_tasks = task_data['status_changed_tasks']

        logger.info(
            f"Weekly report for user {user_id}: {len(accomplishments)} accomplishments, {len(in_progress)} in progress, {len(status_changed_tasks)} status changes")
    except Exception as e:
        logger.warning(
            f"Enhanced weekly report failed for user {user_id}, falling back to basic: {e}")
        # Fallback to basic method if enhanced fails
        tasks = await get_weekly_tasks(user_id)
        accomplishments = [
            task for task in tasks if task.category == "accomplishments"]
        in_progress = [
            task for task in tasks if task.category == "in progress"]

    # If both accomplishments and in_progress are empty, do not generate a report
    if not accomplishments and not in_progress:
        logger.info(
            f"No accomplishments or in progress tasks for user {user_id}. Skipping report generation.")
        return None

    # Week/year for header
    week_num = datetime.now().isocalendar().week
    year_num = datetime.now().year

    context = {
        'recipient_name': 'Santosh',
        'accomplishments': accomplishments,
        'in_progress': in_progress,
        'sender_name': user.username,
        'sender_title': user.userrole,
        'week': week_num,
        'year': year_num,
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

    # If report_content is None, do not send the email
    if report_content is None:
        logger.info(
            f"Weekly report not sent to {to_email} for user {user_id} as there are no accomplishments or in progress tasks.")
        return

    email_service = EmailService(
        from_email=smtp_config.sender_email,
        host=smtp_config.smtp_host,
        pwd=smtp_config.smtp_password,
        port=smtp_config.smtp_port,
        username=smtp_config.smtp_username
    )

    await email_service.send_email(
        to_address=to_email,
        subject="Weekly Progress Report",
        content=report_content,
        html=True
    )


async def send_weekly_report(to_email="santhosh.bommana@medicasapp.com", force=False, job_id=None):
    """Send weekly reports on every Friday except the last Friday of the month (IST)."""
    # Use provided job_id or default to 'weekly_reporter'
    actual_job_id = job_id if job_id else 'weekly_reporter'

    # Use the new job tracking system
    async with JobExecutionTracker(
        job_name=actual_job_id,
        trigger_type="scheduled" if not force else "manual"
    ) as tracker:

        await tracker.log("INFO", "Starting weekly report execution")

        execution_result = {
            'job_id': actual_job_id,
            'status': 'success',
            'message': '',
            'details': [],
            'users_processed': 0,
            'emails_sent': 0,
            'errors': [],
            'execution_time': datetime.now(),
            'forced': force
        }

        db = None
        try:
            # Determine today's date in IST
            today_ist = get_date_in_timezone('Asia/Kolkata')
            execution_result['details'].append(
                f"Execution started at {today_ist.strftime('%Y-%m-%d %H:%M:%S')} IST")

            await tracker.log("INFO", f"Execution started at {today_ist.strftime('%Y-%m-%d %H:%M:%S')} IST")

            if not force and today_ist.weekday() != 4:  # 4 = Friday
                execution_result['status'] = 'skipped'
                execution_result['message'] = "Today is not Friday (IST). Weekly report skipped."
                execution_result['details'].append(
                    f"Current day: {today_ist.strftime('%A')}")
                await tracker.log("INFO", execution_result['message'])
                logger.info(execution_result['message'])
                await tracker.set_result_data(execution_result)
                return execution_result

            # Skip if today is the last Friday (monthly report day)
            if not force and is_last_friday(today_ist):
                execution_result['status'] = 'skipped'
                execution_result['message'] = "Today is the last Friday (IST). Weekly report skipped; monthly will run."
                execution_result['details'].append(
                    "Last Friday of month detected")
                await tracker.log("INFO", execution_result['message'])
                logger.info(execution_result['message'])
                await tracker.set_result_data(execution_result)
                return execution_result

            if force:
                execution_result['details'].append(
                    "⚡ FORCED EXECUTION - Schedule checks bypassed")
                await tracker.log("WARNING", "FORCED EXECUTION - Schedule checks bypassed")

            # Continue for weekly report
            db = await get_db()
            result = await db.execute(
                select(User).join(SMTPConf, User.email == SMTPConf.sender_email)
                .where(SMTPConf.is_active == "True")
            )
            users = result.scalars().all()
            execution_result['users_processed'] = len(users)
            execution_result['details'].append(
                f"Found {len(users)} users with active SMTP configurations")

            await tracker.log("INFO", f"Found {len(users)} users with active SMTP configurations")

            for user in users:
                try:
                    await tracker.log("INFO", f"Sending report for user: {user.username}")
                    await send_report(to_email, user.id)
                    execution_result['emails_sent'] += 1
                    execution_result['details'].append(
                        f"✅ Report sent for user: {user.username}")
                    await tracker.log("INFO", f"✅ Report sent for user: {user.username}")
                    logger.info(
                        f"Weekly report sent for user: {user.username}")
                except Exception as e:
                    error_msg = f"Failed to send report for user {user.username}: {str(e)}"
                    execution_result['errors'].append(error_msg)
                    execution_result['details'].append(f"❌ {error_msg}")
                    await tracker.log("ERROR", error_msg)
                    logger.error(error_msg)

            if execution_result['errors']:
                execution_result['status'] = 'partial_success'
                execution_result['message'] = f"Weekly reports completed with {len(execution_result['errors'])} errors. {execution_result['emails_sent']} emails sent successfully."
            else:
                execution_result[
                    'message'] = f"Weekly reports sent successfully to {execution_result['emails_sent']} recipients."

            await tracker.log("INFO", execution_result['message'])

        except Exception as e:
            execution_result['status'] = 'error'
            execution_result['message'] = f"Error sending weekly reports: {str(e)}"
            execution_result['errors'].append(str(e))
            execution_result['details'].append(f"❌ Critical error: {str(e)}")
            await tracker.log("ERROR", f"Critical error: {str(e)}")
            logger.error(f"Error sending weekly reports for all users: {e}")
            raise  # Re-raise to trigger failure in tracker
        finally:
            if db is not None:
                await db.close()

            execution_result['details'].append(
                f"Execution completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

            # Store result data in the tracker
            await tracker.set_result_data(execution_result)

            # Store result in global storage for UI display (backward compatibility)
            from app.core.jobs.job_results_store import store_job_result
            store_job_result(actual_job_id, execution_result)

            # Also store under the base job ID for UI consistency
            if actual_job_id != 'weekly_reporter':
                store_job_result('weekly_reporter', execution_result)

            await tracker.log("INFO", "Weekly report execution completed")

            return execution_result
