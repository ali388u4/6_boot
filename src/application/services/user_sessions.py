import uuid

from src.infrastructure.persistence.models import UserSessionModel


class UserSessionService:
    def __init__(self, repo):
        self._repo = repo

    async def ensure(self, telegram_user_id: int) -> UserSessionModel:
        return await self._repo.ensure(telegram_user_id)

    async def update_selection(
        self,
        *,
        telegram_user_id: int,
        subject_id: uuid.UUID | None = None,
        chapter_id: uuid.UUID | None = None,
        topic_id: uuid.UUID | None = None,
    ) -> None:
        await self._repo.update_selection(
            telegram_user_id=telegram_user_id,
            subject_id=subject_id,
            chapter_id=chapter_id,
            topic_id=topic_id,
        )

    async def save_fsm_snapshot(self, *, telegram_user_id: int, fsm_state: str | None, state_data: dict) -> None:
        await self._repo.save_fsm_snapshot(telegram_user_id=telegram_user_id, fsm_state=fsm_state, state_data=state_data)
