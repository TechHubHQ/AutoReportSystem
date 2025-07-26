from app.database.db_connector import get_db
from app.core.services.encryption_service import EncryptionService
from app.database.models import SMTPConf


async def setup_smtp(smtp_host, smtp_port, smtp_username, smtp_pwd):
    try:
        db = await get_db()
        smtp_pwd = EncryptionService.encrypt(smtp_pwd)
        new_smtp_conf = SMTPConf(
            smtp_host=smtp_host,
            smtp_port=smtp_port,
            smtp_username=smtp_username,
            smtp_password=smtp_pwd
        )
        db.add(new_smtp_conf)
        db.commit()
        db.refresh(new_smtp_conf)
        return new_smtp_conf
    except Exception as e:
        print(f"Error creating new smtp configuration {e}")
        raise e
    finally:
        await db.close()


async def get_smtp_conf(user_id) -> SMTPConf:
    try:
        db = await get_db()
        smtp_conf = await db.get(SMTPConf, user_id)
        return smtp_conf
    except Exception as e:
        print(f"Error retrieving smtp configuration {e}")
        raise e
    finally:
        await db.close()


async def update_smtp_conf(user_id, smtp_host=None, smtp_port=None, smtp_username=None, smtp_pwd=None):
    try:
        db = await get_db()
        smtp_conf = await get_smtp_conf(user_id)
        if not smtp_conf:
            return None
        if smtp_host:
            smtp_conf.smtp_host = smtp_host
        if smtp_port:
            smtp_conf.smtp_port = smtp_port
        if smtp_username:
            smtp_conf.smtp_username = smtp_username
        if smtp_pwd:
            smtp_conf.smtp_password = EncryptionService.encrypt(smtp_pwd)
    except Exception as e:
        print(f"Error updating smtp conf {e}")
    finally:
        await db.close()
