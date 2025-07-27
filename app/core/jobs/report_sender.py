import asyncio
from .scheduler import scheduler
from app.integrations.email.email_client import EmailService
from .utils.template_loader import load_template


async def send_w_report(w_report):
    w_report_content = await load_template(w_report, "w_report.html")
    email_service = EmailService(
        email="",
        host="",
        pwd="",
        port=""
    )
    await email_service.send_email(
        to_address="",
        subject="Weekly Update",
        content=w_report_content
    )


async def send_m_report(m_report):
    m_report_content = await load_template(m_report, "m_report.html")
    email_service = EmailService(
        email="",
        host="",
        pwd="",
        port=""
    )
    await email_service.send_email(
        to_address="",
        subject="Monthly Update",
        content=m_report_content
    )


# 9:50 p.m. IST is 16:20 UTC (IST is UTC+5:30)
asyncio.run(scheduler.schedule_task(
    send_w_report,
    "weekly",
    day_of_week=4,  # Friday (Monday=0)
    hour=16,
    minute=20,
))
