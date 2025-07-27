import asyncio
from .scheduler import scheduler
from app.integrations.email.email_client import EmailService
from .utils.template_loader import load_template
from .utils.content_loader import load_content


async def send_w_report():
    w_report = await load_content("weekly")
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


async def send_m_report():
    m_report = await load_content("monthly")
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
