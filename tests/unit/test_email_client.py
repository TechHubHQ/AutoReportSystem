import pytest
from unittest.mock import patch, AsyncMock
from app.integrations.email.email_client import EmailService

@pytest.mark.asyncio
async def test_send_email_success():
    service = EmailService(
        email="sender@example.com",
        host="smtp.example.com",
        pwd="password",
        port=587
    )
    with patch("aiosmtplib.send", new_callable=AsyncMock) as mock_send:
        await service.send_email(
            to_address="receiver@example.com",
            subject="Test Subject",
            content="Test Body",
            html=False
        )
        assert mock_send.called
        args, kwargs = mock_send.call_args
        assert kwargs["hostname"] == "smtp.example.com"
        assert kwargs["port"] == 587
        assert kwargs["username"] == "sender@example.com"
        assert kwargs["password"] == "password"
        assert kwargs["start_tls"] is True
