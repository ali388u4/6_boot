import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.persistence.models import (
    ChapterModel,
    QuestionModel,
    SolvingStyleModel,
    SubjectModel,
    TopicModel,
)
from src.presentation.api.deps import admin_auth, get_db_session
from src.presentation.api.schemas import (
    ChapterCreate,
    ChapterOut,
    ChapterUpdate,
    QuestionCreate,
    QuestionOut,
    QuestionUpdate,
    SolvingStyleOut,
    SolvingStyleUpsert,
    SubjectCreate,
    SubjectOut,
    SubjectUpdate,
    TopicCreate,
    TopicOut,
    TopicUpdate,
)

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(admin_auth)])


@router.post("/subjects", response_model=SubjectOut)
async def create_subject(payload: SubjectCreate, session: AsyncSession = Depends(get_db_session)):
    obj = SubjectModel(name=payload.name)
    session.add(obj)
    await session.commit()
    await session.refresh(obj)
    return SubjectOut(id=obj.id, name=obj.name)


@router.put("/subjects/{subject_id}", response_model=SubjectOut)
async def update_subject(subject_id: uuid.UUID, payload: SubjectUpdate, session: AsyncSession = Depends(get_db_session)):
    res = await session.execute(select(SubjectModel).where(SubjectModel.id == subject_id))
    obj = res.scalars().first()
    if obj is None:
        raise HTTPException(status_code=404, detail="Subject not found")
    obj.name = payload.name
    await session.commit()
    await session.refresh(obj)
    return SubjectOut(id=obj.id, name=obj.name)


@router.delete("/subjects/{subject_id}")
async def delete_subject(subject_id: uuid.UUID, session: AsyncSession = Depends(get_db_session)):
    res = await session.execute(select(SubjectModel).where(SubjectModel.id == subject_id))
    obj = res.scalars().first()
    if obj is not None:
        await session.delete(obj)
        await session.commit()
    return {"ok": True}


@router.get("/subjects", response_model=list[SubjectOut])
async def list_subjects(session: AsyncSession = Depends(get_db_session)):
    res = await session.execute(select(SubjectModel).order_by(SubjectModel.name.asc()))
    items = res.scalars().all()
    return [SubjectOut(id=x.id, name=x.name) for x in items]


@router.post("/chapters", response_model=ChapterOut)
async def create_chapter(payload: ChapterCreate, session: AsyncSession = Depends(get_db_session)):
    obj = ChapterModel(subject_id=payload.subject_id, title=payload.title, order_index=payload.order_index)
    session.add(obj)
    await session.commit()
    await session.refresh(obj)
    return ChapterOut(id=obj.id, subject_id=obj.subject_id, title=obj.title, order_index=obj.order_index)


@router.put("/chapters/{chapter_id}", response_model=ChapterOut)
async def update_chapter(chapter_id: uuid.UUID, payload: ChapterUpdate, session: AsyncSession = Depends(get_db_session)):
    res = await session.execute(select(ChapterModel).where(ChapterModel.id == chapter_id))
    obj = res.scalars().first()
    if obj is None:
        raise HTTPException(status_code=404, detail="Chapter not found")
    obj.title = payload.title
    obj.order_index = payload.order_index
    await session.commit()
    await session.refresh(obj)
    return ChapterOut(id=obj.id, subject_id=obj.subject_id, title=obj.title, order_index=obj.order_index)


@router.delete("/chapters/{chapter_id}")
async def delete_chapter(chapter_id: uuid.UUID, session: AsyncSession = Depends(get_db_session)):
    res = await session.execute(select(ChapterModel).where(ChapterModel.id == chapter_id))
    obj = res.scalars().first()
    if obj is not None:
        await session.delete(obj)
        await session.commit()
    return {"ok": True}


@router.get("/chapters", response_model=list[ChapterOut])
async def list_chapters(subject_id: uuid.UUID, session: AsyncSession = Depends(get_db_session)):
    res = await session.execute(
        select(ChapterModel).where(ChapterModel.subject_id == subject_id).order_by(ChapterModel.order_index.asc())
    )
    items = res.scalars().all()
    return [ChapterOut(id=x.id, subject_id=x.subject_id, title=x.title, order_index=x.order_index) for x in items]


@router.post("/topics", response_model=TopicOut)
async def create_topic(payload: TopicCreate, session: AsyncSession = Depends(get_db_session)):
    obj = TopicModel(chapter_id=payload.chapter_id, title=payload.title, order_index=payload.order_index)
    session.add(obj)
    await session.commit()
    await session.refresh(obj)
    return TopicOut(id=obj.id, chapter_id=obj.chapter_id, title=obj.title, order_index=obj.order_index)


@router.put("/topics/{topic_id}", response_model=TopicOut)
async def update_topic(topic_id: uuid.UUID, payload: TopicUpdate, session: AsyncSession = Depends(get_db_session)):
    res = await session.execute(select(TopicModel).where(TopicModel.id == topic_id))
    obj = res.scalars().first()
    if obj is None:
        raise HTTPException(status_code=404, detail="Topic not found")
    obj.title = payload.title
    obj.order_index = payload.order_index
    await session.commit()
    await session.refresh(obj)
    return TopicOut(id=obj.id, chapter_id=obj.chapter_id, title=obj.title, order_index=obj.order_index)


@router.delete("/topics/{topic_id}")
async def delete_topic(topic_id: uuid.UUID, session: AsyncSession = Depends(get_db_session)):
    res = await session.execute(select(TopicModel).where(TopicModel.id == topic_id))
    obj = res.scalars().first()
    if obj is not None:
        await session.delete(obj)
        await session.commit()
    return {"ok": True}


@router.get("/topics", response_model=list[TopicOut])
async def list_topics(chapter_id: uuid.UUID, session: AsyncSession = Depends(get_db_session)):
    res = await session.execute(
        select(TopicModel).where(TopicModel.chapter_id == chapter_id).order_by(TopicModel.order_index.asc())
    )
    items = res.scalars().all()
    return [TopicOut(id=x.id, chapter_id=x.chapter_id, title=x.title, order_index=x.order_index) for x in items]


@router.post("/questions", response_model=QuestionOut)
async def create_question(payload: QuestionCreate, session: AsyncSession = Depends(get_db_session)):
    obj = QuestionModel(
        topic_id=payload.topic_id,
        prompt_text=payload.prompt_text,
        solution_json=payload.solution_json,
        difficulty=payload.difficulty,
    )
    session.add(obj)
    await session.commit()
    await session.refresh(obj)
    return QuestionOut(
        id=obj.id,
        topic_id=obj.topic_id,
        prompt_text=obj.prompt_text,
        solution_json=obj.solution_json,
        difficulty=obj.difficulty,
        created_at=obj.created_at,
    )


@router.put("/questions/{question_id}", response_model=QuestionOut)
async def update_question(question_id: uuid.UUID, payload: QuestionUpdate, session: AsyncSession = Depends(get_db_session)):
    res = await session.execute(select(QuestionModel).where(QuestionModel.id == question_id))
    obj = res.scalars().first()
    if obj is None:
        raise HTTPException(status_code=404, detail="Question not found")
    obj.prompt_text = payload.prompt_text
    obj.solution_json = payload.solution_json
    obj.difficulty = payload.difficulty
    await session.commit()
    await session.refresh(obj)
    return QuestionOut(
        id=obj.id,
        topic_id=obj.topic_id,
        prompt_text=obj.prompt_text,
        solution_json=obj.solution_json,
        difficulty=obj.difficulty,
        created_at=obj.created_at,
    )


@router.delete("/questions/{question_id}")
async def delete_question(question_id: uuid.UUID, session: AsyncSession = Depends(get_db_session)):
    res = await session.execute(select(QuestionModel).where(QuestionModel.id == question_id))
    obj = res.scalars().first()
    if obj is not None:
        await session.delete(obj)
        await session.commit()
    return {"ok": True}


@router.get("/questions", response_model=list[QuestionOut])
async def list_questions(topic_id: uuid.UUID, session: AsyncSession = Depends(get_db_session)):
    res = await session.execute(select(QuestionModel).where(QuestionModel.topic_id == topic_id))
    items = res.scalars().all()
    return [
        QuestionOut(
            id=x.id,
            topic_id=x.topic_id,
            prompt_text=x.prompt_text,
            solution_json=x.solution_json,
            difficulty=x.difficulty,
            created_at=x.created_at,
        )
        for x in items
    ]


@router.put("/solving-styles", response_model=SolvingStyleOut)
async def upsert_solving_style(payload: SolvingStyleUpsert, session: AsyncSession = Depends(get_db_session)):
    res = await session.execute(select(SolvingStyleModel).where(SolvingStyleModel.subject_id == payload.subject_id))
    obj = res.scalars().first()

    if obj is None:
        obj = SolvingStyleModel(subject_id=payload.subject_id, style_json=payload.style_json)
        session.add(obj)
    else:
        obj.style_json = payload.style_json

    await session.commit()
    await session.refresh(obj)

    return SolvingStyleOut(id=obj.id, subject_id=obj.subject_id, style_json=obj.style_json, updated_at=obj.updated_at)
