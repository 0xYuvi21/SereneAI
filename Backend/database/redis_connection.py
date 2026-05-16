import redis.asyncio as redis
from Backend.core.config import get_settings


class RedisCache:
    client = None


redis_cache = RedisCache()


async def connect_redis():
    settings = get_settings()
    redis_cache.client = await redis.from_url(settings.redis_url, decode_responses=True)


async def close_redis():
    if redis_cache.client:
        await redis_cache.client.close()


def get_redis():
    return redis_cache.client
