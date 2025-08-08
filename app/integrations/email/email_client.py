import aiosmtplib
from email.mime.text import MIMEText


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

    async def send_email(self, to_address, subject, content, html=False):
        msg = MIMEText(content, 'html' if html else 'plain')
        msg['Subject'] = subject
        msg['From'] = self.from_email
        msg['To'] = to_address

        await aiosmtplib.send(
            msg,
            hostname=self.host,
            port=self.port,
            username=self.username,
            password=self.pwd,
            start_tls=True,
        )

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
