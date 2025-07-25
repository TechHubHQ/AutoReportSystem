import asyncio
from services.encryption_service import EncryptionService
from database.models import SMTPConf

async def setup_smtp(smtp_host, smtp_port, smtp_username, smtp_pwd):
    smtp_pwd = EncryptionService.decrypt(smtp_pwd)

    
