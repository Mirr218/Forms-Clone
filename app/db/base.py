from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

from app.core.config import database_config

# Создаем асинхронный движок
engine = create_async_engine(str(database_config.database_url()))

# Фабрика асинхронных сессий
AsyncSessionFactory = async_sessionmaker(
    expire_on_commit=False, autoflush=False, autocommit=False, bind=engine
)


Base = declarative_base()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionFactory() as session:
        try:
            yield session
        finally:
            await session.close()


async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
