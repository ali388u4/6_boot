import uuid
from collections.abc import Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.application.interfaces import CatalogRepository, QuestionRepository, SolvingStyleRepository
from src.infrastructure.persistence.models import (
    ChapterModel,
    QuestionModel,
    SolvingStyleModel,
    SubjectModel,
    TopicModel,
    UserSessionModel,
)


class SqlAlchemyCatalogRepository(CatalogRepository):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        self._session_factory = session_factory

    async def list_subjects(self) -> Sequence[SubjectModel]:
        async with self._session_factory() as session:
            res = await session.execute(select(SubjectModel).order_by(SubjectModel.name.asc()))
            return res.scalars().all()

    async def list_chapters(self, subject_id: uuid.UUID) -> Sequence[ChapterModel]:
        async with self._session_factory() as session:
            res = await session.execute(
                select(ChapterModel).where(ChapterModel.subject_id == subject_id).order_by(ChapterModel.order_index.asc())
            )
            return res.scalars().all()

    async def list_topics(self, chapter_id: uuid.UUID) -> Sequence[TopicModel]:
        async with self._session_factory() as session:
            res = await session.execute(
                select(TopicModel).where(TopicModel.chapter_id == chapter_id).order_by(TopicModel.order_index.asc())
            )
            return res.scalars().all()


class SqlAlchemyQuestionRepository(QuestionRepository):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        self._session_factory = session_factory

    async def get_random_question(self, topic_id: uuid.UUID) -> QuestionModel | None:
        async with self._session_factory() as session:
            res = await session.execute(
                select(QuestionModel)
                .where(QuestionModel.topic_id == topic_id)
                .order_by(func.random())
                .limit(1)
            )
            return res.scalars().first()

    async def get_question(self, question_id: uuid.UUID) -> QuestionModel | None:
        async with self._session_factory() as session:
            res = await session.execute(select(QuestionModel).where(QuestionModel.id == question_id))
            return res.scalars().first()


class SqlAlchemySolvingStyleRepository(SolvingStyleRepository):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        self._session_factory = session_factory

    async def get_for_subject(self, subject_id: uuid.UUID) -> SolvingStyleModel | None:
        async with self._session_factory() as session:
            res = await session.execute(select(SolvingStyleModel).where(SolvingStyleModel.subject_id == subject_id))
            return res.scalars().first()


class SqlAlchemyUserSessionRepository:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        self._session_factory = session_factory

    async def ensure(self, telegram_user_id: int) -> UserSessionModel:
        async with self._session_factory() as session:
            res = await session.execute(
                select(UserSessionModel).where(UserSessionModel.telegram_user_id == telegram_user_id)
            )
            obj = res.scalars().first()
            if obj is None:
                obj = UserSessionModel(telegram_user_id=telegram_user_id, state_data={})
                session.add(obj)
                await session.commit()
                await session.refresh(obj)
            return obj

    async def update_selection(
        self,
        *,
        telegram_user_id: int,
        subject_id: uuid.UUID | None = None,
        chapter_id: uuid.UUID | None = None,
        topic_id: uuid.UUID | None = None,
    ) -> None:
        async with self._session_factory() as session:
            res = await session.execute(
                select(UserSessionModel).where(UserSessionModel.telegram_user_id == telegram_user_id)
            )
            obj = res.scalars().first()
            if obj is None:
                obj = UserSessionModel(telegram_user_id=telegram_user_id, state_data={})
                session.add(obj)

            if subject_id is not None:
                obj.selected_subject_id = subject_id
            if chapter_id is not None:
                obj.selected_chapter_id = chapter_id
            if topic_id is not None:
                obj.selected_topic_id = topic_id

            await session.commit()

    async def save_fsm_snapshot(self, *, telegram_user_id: int, fsm_state: str | None, state_data: dict) -> None:
        async with self._session_factory() as session:
            res = await session.execute(
                select(UserSessionModel).where(UserSessionModel.telegram_user_id == telegram_user_id)
            )
            obj = res.scalars().first()
            if obj is None:
                obj = UserSessionModel(telegram_user_id=telegram_user_id, state_data={})
                session.add(obj)

            obj.fsm_state = fsm_state
            obj.state_data = state_data or {}

            await session.commit()
