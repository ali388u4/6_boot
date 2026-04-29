import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class SubjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)


class SubjectUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=255)


class SubjectOut(BaseModel):
    id: uuid.UUID
    name: str


class ChapterCreate(BaseModel):
    subject_id: uuid.UUID
    title: str = Field(min_length=1, max_length=255)
    order_index: int = 0


class ChapterUpdate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    order_index: int = 0


class ChapterOut(BaseModel):
    id: uuid.UUID
    subject_id: uuid.UUID
    title: str
    order_index: int


class TopicCreate(BaseModel):
    chapter_id: uuid.UUID
    title: str = Field(min_length=1, max_length=255)
    order_index: int = 0


class TopicUpdate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    order_index: int = 0


class TopicOut(BaseModel):
    id: uuid.UUID
    chapter_id: uuid.UUID
    title: str
    order_index: int


class QuestionCreate(BaseModel):
    topic_id: uuid.UUID
    prompt_text: str = Field(min_length=1)
    solution_json: dict
    difficulty: int | None = None


class QuestionUpdate(BaseModel):
    prompt_text: str = Field(min_length=1)
    solution_json: dict
    difficulty: int | None = None


class QuestionOut(BaseModel):
    id: uuid.UUID
    topic_id: uuid.UUID
    prompt_text: str
    solution_json: dict
    difficulty: int | None
    created_at: datetime


class SolvingStyleUpsert(BaseModel):
    subject_id: uuid.UUID
    style_json: dict


class SolvingStyleOut(BaseModel):
    id: uuid.UUID
    subject_id: uuid.UUID
    style_json: dict
    updated_at: datetime
