import logging

from aiogram import Bot, Dispatcher
from aiogram.types import Update
from fastapi import APIRouter, Request

logger = logging.getLogger(__name__)


def build_webhook_router(webhook_path: str = "/telegram/webhook") -> APIRouter:
    router = APIRouter()

    @router.post(webhook_path)
    async def telegram_webhook(request: Request):
        bot: Bot = request.app.state.bot
        dp: Dispatcher = request.app.state.dp

        raw = await request.body()
        update = Update.model_validate_json(raw)

        await dp.feed_update(bot, update)
        return {"ok": True}

    return router
