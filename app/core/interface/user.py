from database.models import User
from database.db_connector import get_db
from security.auth.auth_handler import hash_password,verify_password
from sqlalchemy import select


async def create_user(username: str, email: str, password: str):
    try:
        db = await get_db()
        password = hash_password(password)
        new_user = User(username=username, email=email, password=password)
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)
        return new_user
    except Exception as e:
        print(f"Error creating user: {e}")
        raise e
    finally:
        await db.close()

async def get_user(user_id: int):
    try:
        db = await get_db()
        user = await db.get(User, user_id)
        return user
    except Exception as e:
        print(f"Error retrieving user: {e}")
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
        print(f"Error updating user: {e}")
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
        print(f"Error authenticating user: {e}")
        raise e
    finally:
        await db.close()