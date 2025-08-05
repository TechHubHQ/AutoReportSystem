import aiosmtplib
from email.mime.text import MIMEText
from app.core.interface.template_interface import get_template
from app.integrations.email.template_loader import load_template_from_string


class EmailService:
    def __init__(self, email, host, pwd, port):
        self.email = email
        self.host = host
        self.pwd = pwd
        self.port = port

    async def send_email(self, to_address, subject, content, html=False):
        msg = MIMEText(content, 'html' if html else 'plain')
        msg['Subject'] = subject
        msg['From'] = self.email
        msg['To'] = to_address

        await aiosmtplib.send(
            msg,
            hostname=self.host,
            port=self.port,
            username=self.email,
            password=self.pwd,
            start_tls=True,
        )

    async def send_template_email(self, to_address, template_id, user_id=None):
        """Send email using a template with content"""
        try:
            # Get template
            template = await get_template(template_id)
            if not template:
                raise ValueError(f"Template with ID {template_id} not found")

            # Process template with content
            rendered = await load_template_from_string(
                template.html_content,
                template.subject,
                user_id
            )

            # Send email
            await self.send_email(
                to_address=to_address,
                subject=rendered['subject'],
                content=rendered['content'],
                html=True
            )

            return True
        except Exception as e:
            print(f"Error sending template email: {e}")
            raise e

# Example Usage
# import asyncio
#
# async def main():
#     email_service = EmailService(
#         email="your_email@example.com",
#         host="smtp.example.com",
#         pwd="your_password",
#         port=587
#     )
#     await email_service.send_email(
#         to_address="recipient@example.com",
#         subject="Test Email",
#         content="<h1>Hello, this is a test email!</h1>",
#         html=True
#     )
#
# # To run the example:
# # asyncio.run(main())
