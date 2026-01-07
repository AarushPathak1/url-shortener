from fastapi import HTTPException
from app.cache.redis_client import redis_client


async def rate_limit(
    key: str,
    limit: int,
    window_seconds: int,
):
    count = await redis_client.incr(key)

    if count == 1:
        await redis_client.expire(key, window_seconds)

    if count > limit:
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded"
        )
