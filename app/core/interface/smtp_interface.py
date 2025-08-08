from app.database.db_connector import get_db
from app.core.services.encryption_service import EncryptionService
from app.database.models import SMTPConf, User
from sqlalchemy import select
from typing import Optional
from app.config.logging_config import get_logger

logger = get_logger(__name__)


async def setup_smtp(smtp_host, smtp_port, smtp_username, smtp_pwd, sender_email):
    """Create a new SMTP configuration for the specific user (by sender_email).

    - Ensures the sender_email belongs to an existing user.
    - Deactivates any existing SMTP configs for that user to keep only one active.
    - Stores the new config as active for that user.
    """
    db = None
    try:
        # Validate inputs
        if not all([smtp_host, smtp_port, smtp_username, smtp_pwd, sender_email]):
            raise ValueError("All SMTP configuration fields are required")

        if not isinstance(smtp_pwd, str) or not smtp_pwd.strip():
            raise ValueError("SMTP password must be a non-empty string")

        db = await get_db()

        # Ensure the sender_email maps to a valid user
        user_result = await db.execute(select(User).where(User.email == sender_email))
        user = user_result.scalar_one_or_none()
        if not user:
            raise ValueError("Invalid sender email: no matching user found")

        # Encrypt password
        try:
            encrypted_pwd = EncryptionService.encrypt(smtp_pwd)
        except Exception as e:
            logger.error(f"Error encrypting SMTP password: {e}")
            raise ValueError(f"Failed to encrypt password: {e}")

        # Deactivate existing configs for this user (keep history but only one active)
        existing_result = await db.execute(
            select(SMTPConf).where(SMTPConf.sender_email == sender_email)
        )
        existing_configs = existing_result.scalars().all()
        for cfg in existing_configs:
            if cfg.is_active == "True":
                cfg.is_active = "False"

        # Create and activate new configuration for this user
        new_smtp_conf = SMTPConf(
            smtp_host=smtp_host,
            smtp_port=smtp_port,
            smtp_username=smtp_username,
            smtp_password=encrypted_pwd,
            sender_email=sender_email,
            is_active="True",
        )
        db.add(new_smtp_conf)
        await db.commit()
        await db.refresh(new_smtp_conf)
        return new_smtp_conf
    except Exception as e:
        logger.error(f"Error creating new smtp configuration: {e}")
        if db is not None:
            try:
                await db.rollback()
            except Exception:
                pass
        if "encrypt" in str(e).lower():
            raise ValueError(f"Encryption error: {e}")
        raise e
    finally:
        if db is not None:
            await db.close()


async def get_active_smtp_config(user_id: Optional[int] = None) -> Optional[SMTPConf]:
    """Get active SMTP configuration for the given user only.

    Security note: Do NOT fall back to another user's active config.
    Return None when the user has no active configuration.
    """
    try:
        db = await get_db()

        if not user_id:
            return None

        # User-specific active SMTP config
        result = await db.execute(
            select(SMTPConf)
            .join(User, SMTPConf.sender_email == User.email)
            .where(User.id == user_id, SMTPConf.is_active == "True")
            .limit(1)
        )
        smtp_conf = result.scalar_one_or_none()
        if smtp_conf:
            # Decrypt password for use/display
            smtp_conf.smtp_password = EncryptionService.decrypt(
                smtp_conf.smtp_password)
        return smtp_conf

    except Exception as e:
        logger.error(f"Error getting active SMTP configuration: {e}")
        return None
    finally:
        await db.close()


async def get_smtp_conf(user_id) -> SMTPConf:
    try:
        db = await get_db()
        smtp_conf = await db.get(SMTPConf, user_id)
        return smtp_conf
    except Exception as e:
        logger.error(f"Error retrieving smtp configuration {e}")
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
        logger.error(f"Error retrieving all SMTP configurations: {e}")
        return []
    finally:
        await db.close()


async def update_smtp_conf(config_id, smtp_host=None, smtp_port=None, smtp_username=None, smtp_pwd=None):
    try:
        db = await get_db()
        smtp_conf = await db.get(SMTPConf, config_id)
        if not smtp_conf:
            raise ValueError(
                f"SMTP configuration with ID {config_id} not found")

        if smtp_host:
            smtp_conf.smtp_host = smtp_host
        if smtp_port:
            smtp_conf.smtp_port = smtp_port
        if smtp_username:
            smtp_conf.smtp_username = smtp_username
        if smtp_pwd:
            if not isinstance(smtp_pwd, str) or not smtp_pwd.strip():
                raise ValueError("SMTP password must be a non-empty string")

            try:
                smtp_conf.smtp_password = EncryptionService.encrypt(smtp_pwd)
            except Exception as e:
                logger.error(f"Error encrypting SMTP password: {e}")
                raise ValueError(f"Failed to encrypt password: {e}")

        await db.commit()
        await db.refresh(smtp_conf)
        return smtp_conf
    except Exception as e:
        logger.error(f"Error updating smtp configuration: {e}")
        if "encrypt" in str(e).lower():
            raise ValueError(f"Encryption error: {e}")
        raise e
    finally:
        await db.close()


async def delete_smtp_conf(config_id: int, user_email: str) -> bool:
    """Delete an SMTP configuration if it belongs to the given user.

    Returns True if deleted. Raises if not found or unauthorized.
    """
    db = await get_db()
    try:
        smtp_conf = await db.get(SMTPConf, config_id)
        if not smtp_conf:
            raise ValueError(f"SMTP configuration with ID {config_id} not found")

        if smtp_conf.sender_email != user_email:
            raise PermissionError("Not authorized to delete this SMTP configuration")

        await db.delete(smtp_conf)
        await db.commit()
        return True
    except Exception as e:
        logger.error(f"Error deleting smtp configuration {config_id}: {e}")
        try:
            await db.rollback()
        except Exception:
            pass
        raise e
    finally:
        await db.close()
