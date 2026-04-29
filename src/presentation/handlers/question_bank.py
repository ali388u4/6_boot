import uuid

from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, ReplyKeyboardMarkup
from aiogram.utils.keyboard import ReplyKeyboardBuilder

from src.application.services.question_bank import QuestionBankService
from src.application.services.user_sessions import UserSessionService
from src.infrastructure.persistence.repositories import SqlAlchemyQuestionRepository
from src.presentation.handlers.keyboards import (
    build_chapters_kb,
    build_show_solution_kb,
    build_subjects_kb,
    build_topics_kb,
)
from src.presentation.handlers.states import QuestionBankStates

router = Router()


def _main_menu() -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardBuilder()
    kb.button(text="اعطني سؤال")
    kb.button(text="حل سؤال")
    kb.adjust(2)
    return kb.as_markup(resize_keyboard=True)


@router.message(CommandStart())
async def start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("اختر من القائمة:", reply_markup=_main_menu())


@router.message(F.text == "اعطني سؤال")
async def ask_question_entry(message: Message, state: FSMContext, question_bank_service: QuestionBankService):
    await state.set_state(QuestionBankStates.choosing_subject)
    subjects = await question_bank_service.list_subjects()
    if not subjects:
        await message.answer("لا توجد مواد مضافة بعد.")
        return
    await message.answer("اختر المادة:", reply_markup=build_subjects_kb(subjects))


@router.callback_query(F.data.startswith("qb:subject:"))
async def choose_subject(
    callback: CallbackQuery,
    state: FSMContext,
    question_bank_service: QuestionBankService,
    user_session_service: UserSessionService,
):
    subject_id = uuid.UUID(callback.data.split(":")[-1])
    await state.update_data(subject_id=str(subject_id))

    if callback.from_user:
        await user_session_service.update_selection(telegram_user_id=callback.from_user.id, subject_id=subject_id)

    chapters = await question_bank_service.list_chapters(subject_id)
    await state.set_state(QuestionBankStates.choosing_chapter)
    if not chapters:
        await callback.message.answer("لا توجد فصول لهذه المادة.")
        await callback.answer()
        return

    await callback.message.answer("اختر الفصل:", reply_markup=build_chapters_kb(chapters))
    await callback.answer()


@router.callback_query(F.data.startswith("qb:chapter:"))
async def choose_chapter(
    callback: CallbackQuery,
    state: FSMContext,
    question_bank_service: QuestionBankService,
    user_session_service: UserSessionService,
):
    chapter_id = uuid.UUID(callback.data.split(":")[-1])
    await state.update_data(chapter_id=str(chapter_id))

    if callback.from_user:
        await user_session_service.update_selection(telegram_user_id=callback.from_user.id, chapter_id=chapter_id)

    topics = await question_bank_service.list_topics(chapter_id)
    await state.set_state(QuestionBankStates.choosing_topic)
    if not topics:
        await callback.message.answer("لا توجد مواضيع لهذا الفصل.")
        await callback.answer()
        return

    await callback.message.answer("اختر الموضوع:", reply_markup=build_topics_kb(topics))
    await callback.answer()


@router.callback_query(F.data.startswith("qb:topic:"))
async def choose_topic(
    callback: CallbackQuery,
    state: FSMContext,
    question_bank_service: QuestionBankService,
    user_session_service: UserSessionService,
):
    topic_id = uuid.UUID(callback.data.split(":")[-1])

    if callback.from_user:
        await user_session_service.update_selection(telegram_user_id=callback.from_user.id, topic_id=topic_id)

    question = await question_bank_service.get_random_question(topic_id)
    if not question:
        await callback.message.answer("لا يوجد أسئلة لهذا الموضوع.")
        await callback.answer()
        return

    await callback.message.answer(
        f"<b>السؤال</b>\n\n{question.prompt_text}",
        reply_markup=build_show_solution_kb(question.id),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("qb:solution:"))
async def show_solution(callback: CallbackQuery, question_repo: SqlAlchemyQuestionRepository):
    question_id = uuid.UUID(callback.data.split(":")[-1])
    question = await question_repo.get_question(question_id)
    if not question:
        await callback.message.answer("لم يتم العثور على السؤال.")
        await callback.answer()
        return

    payload = question.solution_json or {}
    steps = payload.get("steps") or []
    final_answer = payload.get("final_answer")

    if not steps and not final_answer:
        await callback.message.answer("لا يوجد حل مخزن لهذا السؤال.")
        await callback.answer()
        return

    for idx, step in enumerate(steps, start=1):
        title = step.get("title")
        explanation = step.get("explanation") or ""
        result = step.get("result")

        text = f"<b>الخطوة {idx}</b>\n"
        if title:
            text += f"<b>{title}</b>\n"
        text += explanation
        if result:
            text += f"\n\n<b>النتيجة:</b> {result}"

        await callback.message.answer(text)

    if final_answer:
        await callback.message.answer(f"<b>الإجابة النهائية:</b> {final_answer}")

    await callback.answer()
