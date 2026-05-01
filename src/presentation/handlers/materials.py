import uuid

from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, ReplyKeyboardMarkup
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.infrastructure.persistence.models import ChapterFileModel, ChapterModel, SubjectModel
from src.infrastructure.settings import Settings
from src.presentation.handlers.keyboards import build_chapters_kb, build_subjects_kb
from src.presentation.handlers.states import AdminStates

router = Router()


def _chapter_menu() -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardBuilder()
    kb.button(text="اعطني سؤال")
    kb.adjust(1)
    return kb.as_markup(resize_keyboard=True)


def _is_admin(*, message: Message | CallbackQuery, settings: Settings) -> bool:
    user = message.from_user
    if not user:
        return False
    if settings.admin_id is None:
        return False
    return user.id == settings.admin_id


@router.message(CommandStart())
async def start(message: Message, state: FSMContext, question_bank_service):
    await state.clear()
    subjects = await question_bank_service.list_subjects()
    if not subjects:
        await message.answer("لا توجد مواد مضافة بعد.")
        return
    await message.answer("اختر المادة:", reply_markup=build_subjects_kb(subjects, prefix="mat"))


@router.callback_query(F.data.startswith("mat:subject:"))
async def choose_subject(callback: CallbackQuery, state: FSMContext, question_bank_service):
    subject_id = uuid.UUID(callback.data.split(":")[-1])
    await state.update_data(current_subject_id=str(subject_id))
    chapters = await question_bank_service.list_chapters(subject_id)
    if not chapters:
        await callback.message.answer("لا توجد فصول لهذه المادة.")
        await callback.answer()
        return
    await callback.message.answer("اختر الفصل:", reply_markup=build_chapters_kb(chapters, prefix="mat"))
    await callback.answer()


@router.callback_query(F.data.startswith("mat:chapter:"))
async def open_chapter(callback: CallbackQuery, state: FSMContext, session_factory: async_sessionmaker[AsyncSession]):
    chapter_id = uuid.UUID(callback.data.split(":")[-1])
    await state.update_data(current_chapter_id=str(chapter_id))

    try:
        async with session_factory() as session:
            res = await session.execute(select(ChapterFileModel).where(ChapterFileModel.chapter_id == chapter_id))
            files = res.scalars().all()
    except Exception:
        await callback.message.answer("حدث خطأ أثناء قراءة ملفات الفصل")
        return

    if not files:
        await callback.message.answer("لا توجد ملفات لهذا الفصل.")
        await callback.answer()
        return

    for f in files:
        name = f.file_name or ""
        if f.file_type == "photo":
            await callback.message.answer_photo(photo=f.telegram_file_id, caption=name or None)
        else:
            await callback.message.answer_document(document=f.telegram_file_id, caption=name or None)

    await callback.message.answer("اختر:", reply_markup=_chapter_menu())

    await callback.answer()


@router.message(
    (F.text == "اعطني سؤال")
    | (F.text == "سؤال")
    | (F.text == "اسئلة")
    | (F.text == "اختبرني")
    | (F.text == "اختبار")
    | (F.text == "اشرح")
)
async def chapter_ai_entry(
    message: Message,
    state: FSMContext,
    session_factory: async_sessionmaker[AsyncSession],
    ai_solver_service,
):
    await message.answer("جاري التحضير...")
    data = await state.get_data()
    chapter_id_str = data.get("current_chapter_id")
    if not chapter_id_str:
        await message.answer("اختر المادة ثم الفصل أولاً من /start")
        return

    try:
        chapter_id = uuid.UUID(chapter_id_str)
    except ValueError:
        await message.answer("اختر المادة ثم الفصل أولاً من /start")
        return

    async with session_factory() as session:
        res = await session.execute(select(ChapterFileModel).where(ChapterFileModel.chapter_id == chapter_id))
        files = res.scalars().all()

    if not files:
        await message.answer("هذا الفصل لا يحتوي ملفات بعد")
        return

    try:
        intent = (message.text or "").strip()
        text = await ai_solver_service.build_chapter_context(bot=message.bot, files=files)
        if not text.strip():
            await message.answer("لم أستطع قراءة محتوى الملفات لهذا الفصل")
            return

        out = await ai_solver_service.generate_from_chapter(intent=intent, chapter_text=text)
        await message.answer(out)
    except Exception:
        await message.answer("حدث خطأ أثناء توليد السؤال من ملفات الفصل")


@router.message(F.text.startswith("/add_subject"))
async def add_subject(message: Message, settings: Settings, session_factory: async_sessionmaker[AsyncSession]):
    if not _is_admin(message=message, settings=settings):
        return

    name = (message.text or "").replace("/add_subject", "", 1).strip()
    if not name:
        await message.answer("اكتب اسم المادة")
        return

    async with session_factory() as session:
        exists = await session.execute(select(SubjectModel).where(SubjectModel.name == name))
        if exists.scalars().first():
            await message.answer("المادة موجودة مسبقاً")
            return

        subject = SubjectModel(name=name)
        session.add(subject)
        await session.commit()

    await message.answer("تم إضافة المادة")


@router.message(F.text.startswith("/add_chapter"))
async def add_chapter(message: Message, settings: Settings, session_factory: async_sessionmaker[AsyncSession]):
    if not _is_admin(message=message, settings=settings):
        return

    payload = (message.text or "").replace("/add_chapter", "", 1).strip()
    if "|" not in payload:
        await message.answer("الصيغة: /add_chapter اسم_المادة|عنوان_الفصل")
        return

    subject_name, chapter_title = [p.strip() for p in payload.split("|", 1)]
    if not subject_name or not chapter_title:
        await message.answer("الصيغة: /add_chapter اسم_المادة|عنوان_الفصل")
        return

    async with session_factory() as session:
        res = await session.execute(select(SubjectModel).where(SubjectModel.name == subject_name))
        subject = res.scalars().first()
        if not subject:
            await message.answer("المادة غير موجودة")
            return

        chapter = ChapterModel(subject_id=subject.id, title=chapter_title, order_index=0)
        session.add(chapter)
        await session.commit()

    await message.answer("تم إضافة الفصل")


@router.message(F.text.startswith("/chapters"))
async def list_chapters(message: Message, settings: Settings, session_factory: async_sessionmaker[AsyncSession]):
    if not _is_admin(message=message, settings=settings):
        return

    payload = (message.text or "").replace("/chapters", "", 1).strip()
    if not payload:
        await message.answer("الصيغة: /chapters اسم_المادة")
        return

    subject_name = payload

    async with session_factory() as session:
        res = await session.execute(select(SubjectModel).where(SubjectModel.name == subject_name))
        subject = res.scalars().first()
        if not subject:
            await message.answer("المادة غير موجودة")
            return

        chapters_res = await session.execute(
            select(ChapterModel)
            .where(ChapterModel.subject_id == subject.id)
            .order_by(ChapterModel.order_index.asc(), ChapterModel.title.asc())
        )
        chapters = chapters_res.scalars().all()

    if not chapters:
        await message.answer("لا توجد فصول لهذه المادة")
        return

    lines: list[str] = []
    for c in chapters:
        lines.append(f"{c.title} -> {c.id}")

    await message.answer("\n".join(lines))


@router.message(F.text.startswith("/upload_file"))
async def upload_file_entry(message: Message, state: FSMContext, settings: Settings):
    if not _is_admin(message=message, settings=settings):
        return

    parts = (message.text or "").split(maxsplit=1)
    if len(parts) != 2:
        await message.answer("الصيغة: /upload_file <chapter_id>")
        return

    try:
        chapter_id = uuid.UUID(parts[1].strip())
    except ValueError:
        await message.answer("chapter_id غير صحيح")
        return

    await state.set_state(AdminStates.waiting_chapter_file)
    await state.update_data(chapter_id=str(chapter_id))
    await message.answer("ارسل الملف الآن (PDF/DOCX/ZIP/صورة)")


@router.message(AdminStates.waiting_chapter_file)
async def upload_file_receive(
    message: Message,
    state: FSMContext,
    settings: Settings,
    session_factory: async_sessionmaker[AsyncSession],
):
    if not _is_admin(message=message, settings=settings):
        await state.clear()
        return

    data = await state.get_data()
    chapter_id_str = data.get("chapter_id")
    if not chapter_id_str:
        await state.clear()
        await message.answer("انتهت العملية. أرسل /upload_file من جديد")
        return

    try:
        chapter_id = uuid.UUID(chapter_id_str)
    except ValueError:
        await state.clear()
        await message.answer("انتهت العملية. أرسل /upload_file من جديد")
        return

    telegram_file_id: str | None = None
    file_name: str | None = None
    file_type = "document"

    if message.document:
        telegram_file_id = message.document.file_id
        file_name = message.document.file_name
        file_type = "document"
    elif message.photo:
        telegram_file_id = message.photo[-1].file_id
        file_type = "photo"
    else:
        await message.answer("ارسل ملف أو صورة فقط")
        return

    async with session_factory() as session:
        res = await session.execute(select(ChapterModel).where(ChapterModel.id == chapter_id))
        chapter = res.scalars().first()
        if not chapter:
            await message.answer("الفصل غير موجود")
            await state.clear()
            return

        obj = ChapterFileModel(
            chapter_id=chapter_id,
            telegram_file_id=telegram_file_id,
            file_name=file_name,
            file_type=file_type,
        )
        session.add(obj)
        await session.commit()

    await state.clear()
    await message.answer("تم حفظ الملف")
