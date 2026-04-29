from collections.abc import AsyncGenerator

from fastapi import Depends, Header, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.infrastructure.settings import Settings


def get_settings(request: Request) -> Settings:
    return request.app.state.settings


def get_session_factory(request: Request) -> async_sessionmaker[AsyncSession]:
    return request.app.state.session_factory


async def get_db_session(
    session_factory: async_sessionmaker[AsyncSession] = Depends(get_session_factory),
) -> AsyncGenerator[AsyncSession, None]:
    async with session_factory() as session:
        yield session


def admin_auth(
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
    settings: Settings = Depends(get_settings),
) -> None:
    if settings.admin_api_key is None:
        raise HTTPException(status_code=403, detail="Admin API disabled")
    if not x_api_key or x_api_key != settings.admin_api_key:
        raise HTTPException(status_code=401, detail="Unauthorized")
