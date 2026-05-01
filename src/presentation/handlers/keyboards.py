import uuid

from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def build_subjects_kb(subjects, *, prefix: str = "qb") -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for s in subjects:
        kb.button(text=s.name, callback_data=f"{prefix}:subject:{s.id}")
    kb.adjust(1)
    return kb.as_markup()


def build_chapters_kb(chapters, *, prefix: str = "qb") -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for c in chapters:
        kb.button(text=c.title, callback_data=f"{prefix}:chapter:{c.id}")
    kb.adjust(1)
    return kb.as_markup()


def build_topics_kb(topics) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for t in topics:
        kb.button(text=t.title, callback_data=f"qb:topic:{t.id}")
    kb.adjust(1)
    return kb.as_markup()


def build_show_solution_kb(question_id: uuid.UUID) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="إظهار الحل", callback_data=f"qb:solution:{question_id}")
    kb.adjust(1)
    return kb.as_markup()


def build_solver_subjects_kb(subjects) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for s in subjects:
        kb.button(text=s.name, callback_data=f"solve:subject:{s.id}")
    kb.adjust(1)
    return kb.as_markup()
