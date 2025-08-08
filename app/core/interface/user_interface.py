from sqlalchemy import select
from app.database.models import User
from app.database.db_connector import get_db
from app.security.auth.auth_handler import hash_password, verify_password
from app.config.logging_config import get_logger

logger = get_logger(__name__)


async def user_exists(email: str, db) -> bool:
    try:
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        return user is not None
    except Exception as e:
        logger.error(f"Error checking if user exists: {e}")
        raise e


async def create_user(username: str, email: str, password: str, userrole: str = "Software Engineer"):
    db = await get_db()
    try:
        if await user_exists(email, db):  # Pass db here
            raise Exception("User with this email already exists.")

        password = hash_password(password)
        new_user = User(username=username, email=email,
                        password=password, userrole=userrole)
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)
        return new_user
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        raise e
    finally:
        await db.close()


async def get_user(user_id: int):
    try:
        db = await get_db()
        user = await db.get(User, user_id)
        return user
    except Exception as e:
        logger.error(f"Error retrieving user: {e}")
        raise e
    finally:
        await db.close()


async def update_user(user_id: int, username: str = None, email: str = None, password: str = None):
    try:
        db = await get_db()
        user = await db.get(User, user_id)
        if not user:
            return None
        if username:
            user.username = username
        if email:
            user.email = email
        if password:
            user.password = hash_password(password)
        await db.commit()
        await db.refresh(user)
        return user
    except Exception as e:
        logger.error(f"Error updating user: {e}")
        raise e
    finally:
        await db.close()


async def authenticate_user(email: str, plain_password: str):
    try:
        db = await get_db()
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        if user and verify_password(plain_password, user.password):
            return user
        return None
    except Exception as e:
        logger.error(f"Error authenticating user: {e}")
        raise e
    finally:
        await db.close()
