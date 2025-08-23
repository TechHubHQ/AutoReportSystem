import aiosmtplib
from email.mime.text import MIMEText
from app.config.logging_config import get_logger

logger = get_logger(__name__)


class EmailService:
    def __init__(self, from_email, host, pwd, port, username=None):
        """Email service wrapper.
        - from_email: address used in the From header
        - username: SMTP login username (defaults to from_email if not provided)
        """
        self.from_email = from_email
        self.username = username or from_email
        self.host = host
        self.pwd = pwd
        self.port = port
        
        logger.info(f"EmailService initialized: host={host}, port={port}, from={from_email}, username={self.username}")

    async def send_email(self, to_address, subject, content, html=False):
        try:
            logger.info(f"Attempting to send email to {to_address} with subject: {subject}")
            
            msg = MIMEText(content, 'html' if html else 'plain')
            msg['Subject'] = subject
            msg['From'] = self.from_email
            msg['To'] = to_address
            
            logger.debug(f"Email message created. Content length: {len(content)} chars")
            
            await aiosmtplib.send(
                msg,
                hostname=self.host,
                port=self.port,
                username=self.username,
                password=self.pwd,
                start_tls=True,
            )
            
            logger.info(f"Email sent successfully to {to_address}")
            
        except Exception as e:
            logger.error(f"Failed to send email to {to_address}: {str(e)}")
            logger.error(f"SMTP config: host={self.host}, port={self.port}, username={self.username}")
            raise e

# Example Usage
# import asyncio
#
# async def main():
#     email_service = EmailService(
#         from_email="your_email@example.com",
#         host="smtp.example.com",
#         pwd="your_password",
#         port=587,
#         username="smtp_login_username"
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
