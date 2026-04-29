from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.fsm.context import FSMContext
from aiogram.types import TelegramObject

from src.application.services.user_sessions import UserSessionService


class UserSessionMiddleware(BaseMiddleware):
    def __init__(self, *, user_session_service: UserSessionService):
        self._svc = user_session_service

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        user = data.get("event_from_user")
        if user:
            await self._svc.ensure(user.id)

        result = await handler(event, data)

        if user:
            fsm: FSMContext | None = data.get("state")
            if fsm:
                st = await fsm.get_state()
                st_data = await fsm.get_data()
                await self._svc.save_fsm_snapshot(telegram_user_id=user.id, fsm_state=st, state_data=st_data)

        return result
