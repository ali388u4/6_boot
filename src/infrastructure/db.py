from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from src.infrastructure.settings import Settings


def create_engine(settings: Settings) -> AsyncEngine:
    return create_async_engine(settings.database_dsn, pool_pre_ping=True)


def create_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


async def session_scope(session_factory: async_sessionmaker[AsyncSession]) -> AsyncIterator[AsyncSession]:
    async with session_factory() as session:
        try:
            yield session
        finally:
            await session.close()
