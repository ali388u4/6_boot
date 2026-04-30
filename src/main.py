from contextlib import asynccontextmanager
import logging
import os

from fastapi import FastAPI

from src.infrastructure.logging import setup_logging
from src.infrastructure.settings import Settings
from src.infrastructure.db import create_engine, create_session_factory
from src.infrastructure.redis_client import create_redis
from src.presentation.bot_app import create_bot_app
from src.presentation.api.admin import router as admin_router
from src.presentation.webhook import build_webhook_router


logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = Settings()
    setup_logging(settings)
    app.state.settings = settings

    engine = create_engine(settings)
    session_factory = create_session_factory(engine)
    app.state.db_engine = engine
    app.state.session_factory = session_factory

    redis = create_redis(settings)
    app.state.redis = redis

    bot, dp = create_bot_app(settings=settings, session_factory=session_factory, redis=redis)
    app.state.bot = bot
    app.state.dp = dp

    webhook_base_url = settings.webhook_base_url.strip()
    webhook_enabled = bool(webhook_base_url) and webhook_base_url.startswith("https://") and ("=" not in webhook_base_url)
    app.state.webhook_enabled = webhook_enabled
    if webhook_enabled:
        try:
            await bot.set_webhook(url=settings.webhook_url)
        except Exception:
            logger.exception("Failed to set Telegram webhook url=%s", settings.webhook_url)
            app.state.webhook_enabled = False
    else:
        logger.warning(
            "Webhook is disabled (invalid/missing base url). webhook_base_url=%r webhook_url=%r",
            webhook_base_url,
            settings.webhook_url,
        )

    yield

    if getattr(app.state, "webhook_enabled", False):
        await bot.delete_webhook(drop_pending_updates=False)
    await bot.session.close()
    await redis.aclose()
    await engine.dispose()


def create_app() -> FastAPI:
    app = FastAPI(lifespan=lifespan)
    webhook_path = os.getenv("WEBHOOK_PATH", "/telegram/webhook")
    app.include_router(build_webhook_router(webhook_path))
    app.include_router(admin_router)

    @app.get("/health")
    async def health():
        return {"status": "ok"}

    return app


app = create_app()
