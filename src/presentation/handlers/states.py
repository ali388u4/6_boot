from aiogram.fsm.state import State, StatesGroup


class QuestionBankStates(StatesGroup):
    choosing_subject = State()
    choosing_chapter = State()
    choosing_topic = State()


class SolverStates(StatesGroup):
    choosing_subject = State()
    waiting_question_text = State()


class AdminStates(StatesGroup):
    waiting_chapter_file = State()
