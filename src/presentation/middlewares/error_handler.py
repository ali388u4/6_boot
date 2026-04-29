import logging
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message
from aiogram.types import TelegramObject

logger = logging.getLogger(__name__)


class ErrorHandlerMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        try:
            return await handler(event, data)
        except Exception:
            logger.exception("Unhandled exception")
            try:
                if isinstance(event, Message):
                    await event.answer("حدث خطأ غير متوقع. حاول مرة أخرى لاحقاً.")
                elif isinstance(event, CallbackQuery) and event.message:
                    await event.message.answer("حدث خطأ غير متوقع. حاول مرة أخرى لاحقاً.")
            except Exception:
                logger.exception("Failed to send error message")
            raise
