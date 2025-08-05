from app.database.db_connector import get_db
from app.core.services.encryption_service import EncryptionService
from app.database.models import SMTPConf
from sqlalchemy import select
from typing import Optional

async def setup_smtp(smtp_host, smtp_port, smtp_username, smtp_pwd, sender_email):
    try:
        db = await get_db()
        smtp_pwd = EncryptionService.encrypt(smtp_pwd)
        new_smtp_conf = SMTPConf(
            smtp_host=smtp_host,
            smtp_port=smtp_port,
            smtp_username=smtp_username,
            smtp_password=smtp_pwd,
            sender_email=sender_email
        )
        db.add(new_smtp_conf)
        await db.commit()
        await db.refresh(new_smtp_conf)
        return new_smtp_conf
    except Exception as e:
        print(f"Error creating new smtp configuration {e}")
        raise e
    finally:
        await db.close()


async def get_active_smtp_config(user_id: Optional[int] = None) -> Optional[SMTPConf]:
    """Get active SMTP configuration for a user or the first active one"""
    try:
        db = await get_db()

        if user_id:
            # Try to get user-specific SMTP config
            result = await db.execute(
                select(SMTPConf).where(
                    SMTPConf.sender_email.in_(
                        select(SMTPConf.sender_email).join(
                            SMTPConf.user
                        ).where(SMTPConf.user.has(id=user_id))
                    ),
                    SMTPConf.is_active == "True"
                )
            )
            smtp_conf = result.scalar_one_or_none()
            if smtp_conf:
                # Decrypt password
                smtp_conf.smtp_password = EncryptionService.decrypt(
                    smtp_conf.smtp_password)
                return smtp_conf

        # Fallback to any active SMTP config
        result = await db.execute(
            select(SMTPConf).where(SMTPConf.is_active == "True").limit(1)
        )
        smtp_conf = result.scalar_one_or_none()
        if smtp_conf:
            # Decrypt password
            smtp_conf.smtp_password = EncryptionService.decrypt(
                smtp_conf.smtp_password)
            return smtp_conf

        return smtp_conf

    except Exception as e:
        print(f"Error getting active SMTP configuration: {e}")
        return None
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


async def get_all_smtp_configs(user_email: str) -> list[SMTPConf]:
    """Get all SMTP configurations for a user"""
    try:
        db = await get_db()
        result = await db.execute(
            select(SMTPConf).where(SMTPConf.sender_email == user_email)
        )
        configs = result.scalars().all()
        # Decrypt passwords for display
        for config in configs:
            config.smtp_password = EncryptionService.decrypt(
                config.smtp_password)
        return configs
    except Exception as e:
        print(f"Error retrieving all SMTP configurations: {e}")
        return []
    finally:
        await db.close()


async def update_smtp_conf(config_id, smtp_host=None, smtp_port=None, smtp_username=None, smtp_pwd=None):
    try:
        db = await get_db()
        smtp_conf = await db.get(SMTPConf, config_id)
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
        await db.commit()
        await db.refresh(smtp_conf)
        return smtp_conf
    except Exception as e:
        print(f"Error updating smtp conf {e}")
        raise e
    finally:
        await db.close()
