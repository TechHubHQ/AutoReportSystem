from app.integrations.email.email_client import EmailService
from .utils.template_loader import load_template
from .utils.content_loader import load_content


async def send_w_report():
    print("Initiating weekly report transmission protocol...")
    w_report = await load_content("weekly")
    print("Weekly report content successfully retrieved.")
    w_report_content = await load_template(w_report, "w_report.html")
    print("Weekly report template rendered and merged with content.")
    email_service = EmailService(
        email="",
        host="",
        pwd="",
        port=""
    )
    print("Email service initialized. Preparing to dispatch weekly update.")
    await email_service.send_email(
        to_address="",
        subject="Weekly Update",
        content=w_report_content
    )
    print("Weekly report email has been dispatched successfully.")


async def send_m_report():
    print("Initiating monthly report dispatch sequence...")
    m_report = await load_content("monthly")
    print("Monthly report content acquisition complete.")
    m_report_content = await load_template(m_report, "m_report.html")
    print("Monthly report content compiled with template.")
    email_service = EmailService(
        email="",
        host="",
        pwd="",
        port=""
    )
    print("Email service online. Initiating transmission of monthly update.")
    await email_service.send_email(
        to_address="",
        subject="Monthly Update",
        content=m_report_content
    )
    print("Monthly report email dispatched successfully. Operation complete.")
