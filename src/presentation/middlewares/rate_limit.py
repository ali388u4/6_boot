import time
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from redis.asyncio import Redis


class RateLimitMiddleware(BaseMiddleware):
    def __init__(self, *, redis: Redis, limit_per_minute: int):
        self._redis = redis
        self._limit = limit_per_minute

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        user = data.get("event_from_user")
        if not user:
            return await handler(event, data)

        now = int(time.time())
        window = now // 60
        key = f"rl:{user.id}:{window}"

        count = await self._redis.incr(key)
        if count == 1:
            await self._redis.expire(key, 70)

        if count > self._limit:
            message = data.get("event_update").message if data.get("event_update") else None
            if message:
                await message.answer("تجاوزت الحد المسموح للطلبات. حاول بعد دقيقة.")
            return None

        return await handler(event, data)
