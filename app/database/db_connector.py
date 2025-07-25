from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession
from .models import engine, Base

async_session = async_sessionmaker(
    bind=engine, class_=AsyncSession, expire_on_commit=False)


async def get_db() -> AsyncSession:
    return async_session()


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
