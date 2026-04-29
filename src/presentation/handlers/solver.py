import uuid

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from src.application.services.ai_solver import AISolverService
from src.application.services.question_bank import QuestionBankService
from src.application.services.user_sessions import UserSessionService
from src.presentation.handlers.keyboards import build_solver_subjects_kb
from src.presentation.handlers.states import SolverStates

router = Router()


@router.message(F.text == "حل سؤال")
async def solve_entry(message: Message, state: FSMContext, question_bank_service: QuestionBankService):
    await state.set_state(SolverStates.choosing_subject)
    subjects = await question_bank_service.list_subjects()
    if not subjects:
        await message.answer("لا توجد مواد مضافة بعد.")
        return
    await message.answer("اختر المادة:", reply_markup=build_solver_subjects_kb(subjects))


@router.callback_query(F.data.startswith("solve:subject:"))
async def solve_choose_subject(
    callback: CallbackQuery,
    state: FSMContext,
    user_session_service: UserSessionService,
):
    subject_id = uuid.UUID(callback.data.split(":")[-1])
    await state.update_data(solve_subject_id=str(subject_id))

    if callback.from_user:
        await user_session_service.update_selection(telegram_user_id=callback.from_user.id, subject_id=subject_id)

    await state.set_state(SolverStates.waiting_question_text)
    await callback.message.answer("أرسل السؤال نصياً الآن:")
    await callback.answer()


@router.message(SolverStates.waiting_question_text)
async def solve_question_text(message: Message, state: FSMContext, ai_solver_service: AISolverService):
    data = await state.get_data()
    subject_id_str = data.get("solve_subject_id")
    if not subject_id_str:
        await message.answer("اختر المادة أولاً.")
        return

    question_text = (message.text or "").strip()
    if not question_text:
        await message.answer("أرسل نص السؤال.")
        return

    subject_id = uuid.UUID(subject_id_str)

    solution = await ai_solver_service.solve_question(subject_id=subject_id, question_text=question_text)

    for idx, step in enumerate(solution.steps, start=1):
        text = f"<b>الخطوة {idx}</b>\n"
        if step.title:
            text += f"<b>{step.title}</b>\n"
        text += step.explanation
        if step.result:
            text += f"\n\n<b>النتيجة:</b> {step.result}"
        await message.answer(text)

    if solution.final_answer:
        await message.answer(f"<b>الإجابة النهائية:</b> {solution.final_answer}")

    await state.clear()
