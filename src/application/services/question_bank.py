import uuid

from src.application.interfaces import CatalogRepository, QuestionRepository


class QuestionBankService:
    def __init__(self, catalog_repo: CatalogRepository, question_repo: QuestionRepository):
        self._catalog_repo = catalog_repo
        self._question_repo = question_repo

    async def list_subjects(self):
        return await self._catalog_repo.list_subjects()

    async def list_chapters(self, subject_id: uuid.UUID):
        return await self._catalog_repo.list_chapters(subject_id)

    async def list_topics(self, chapter_id: uuid.UUID):
        return await self._catalog_repo.list_topics(chapter_id)

    async def get_random_question(self, topic_id: uuid.UUID):
        return await self._question_repo.get_random_question(topic_id)
