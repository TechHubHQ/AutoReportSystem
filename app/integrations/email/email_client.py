import aiosmtplib
from email.mime.text import MIMEText


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
