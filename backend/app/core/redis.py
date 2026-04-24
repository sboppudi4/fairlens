"""Redis client for progress tracking and rate limiting."""
from redis.asyncio import Redis as AsyncRedis
from redis import Redis as SyncRedis

from app.config import get_settings

_async_client: AsyncRedis | None = None


def get_async_redis() -> AsyncRedis:
    global _async_client
    if _async_client is None:
        _async_client = AsyncRedis.from_url(get_settings().REDIS_URL, decode_responses=True)
    return _async_client


def get_sync_redis() -> SyncRedis:
    return SyncRedis.from_url(get_settings().REDIS_URL, decode_responses=True)
