from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.redis import RedisStorage
from openai import AsyncOpenAI
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.application.services.ai_solver import AISolverService
from src.application.services.question_bank import QuestionBankService
from src.application.services.user_sessions import UserSessionService
from src.infrastructure.persistence.repositories import (
    SqlAlchemyCatalogRepository,
    SqlAlchemyQuestionRepository,
    SqlAlchemySolvingStyleRepository,
    SqlAlchemyUserSessionRepository,
)
from src.infrastructure.settings import Settings
from src.presentation.handlers.materials import router as materials_router
from src.presentation.handlers.solver import router as solver_router
from src.presentation.middlewares.error_handler import ErrorHandlerMiddleware
from src.presentation.middlewares.rate_limit import RateLimitMiddleware
from src.presentation.middlewares.user_session import UserSessionMiddleware


def create_bot_app(
    *,
    settings: Settings,
    session_factory: async_sessionmaker[AsyncSession],
    redis: Redis,
) -> tuple[Bot, Dispatcher]:
    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    storage = RedisStorage.from_url(settings.redis_dsn)
    dp = Dispatcher(storage=storage)

    catalog_repo = SqlAlchemyCatalogRepository(session_factory)
    question_repo = SqlAlchemyQuestionRepository(session_factory)
    style_repo = SqlAlchemySolvingStyleRepository(session_factory)
    user_session_repo = SqlAlchemyUserSessionRepository(session_factory)

    question_bank_service = QuestionBankService(catalog_repo=catalog_repo, question_repo=question_repo)
    user_session_service = UserSessionService(repo=user_session_repo)

    openai_client = AsyncOpenAI(api_key=settings.openai_api_key) if settings.openai_api_key else AsyncOpenAI()
    ai_solver_service = AISolverService(solving_style_repo=style_repo, openai_client=openai_client, model=settings.openai_model)

    dp.update.middleware(ErrorHandlerMiddleware())
    dp.update.middleware(RateLimitMiddleware(redis=redis, limit_per_minute=settings.rate_limit_per_minute))
    dp.update.middleware(UserSessionMiddleware(user_session_service=user_session_service))

    dp.workflow_data.update(
        {
            "settings": settings,
            "session_factory": session_factory,
            "question_bank_service": question_bank_service,
            "question_repo": question_repo,
            "ai_solver_service": ai_solver_service,
            "user_session_service": user_session_service,
        }
    )

    dp.include_router(materials_router)
    dp.include_router(solver_router)

    return bot, dp
