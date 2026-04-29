import uuid
from collections.abc import Sequence
from typing import Protocol

from src.infrastructure.persistence.models import ChapterModel, QuestionModel, SolvingStyleModel, SubjectModel, TopicModel


class CatalogRepository(Protocol):
    async def list_subjects(self) -> Sequence[SubjectModel]: ...

    async def list_chapters(self, subject_id: uuid.UUID) -> Sequence[ChapterModel]: ...

    async def list_topics(self, chapter_id: uuid.UUID) -> Sequence[TopicModel]: ...


class QuestionRepository(Protocol):
    async def get_random_question(self, topic_id: uuid.UUID) -> QuestionModel | None: ...

    async def get_question(self, question_id: uuid.UUID) -> QuestionModel | None: ...


class SolvingStyleRepository(Protocol):
    async def get_for_subject(self, subject_id: uuid.UUID) -> SolvingStyleModel | None: ...
