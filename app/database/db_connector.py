from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession
from .models import engine

async_session = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

async def get_db() -> AsyncSession:
    return async_session()  
