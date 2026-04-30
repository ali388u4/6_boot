from redis.asyncio import Redis

from src.infrastructure.settings import Settings


def create_redis(settings: Settings) -> Redis:
    return Redis.from_url(settings.redis_dsn, decode_responses=True)
