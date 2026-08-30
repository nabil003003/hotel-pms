"""Cache Redis — Workflow J précise des durées littérales : `/kpi/today`
5 min, `/kpi/monthly` 1h (spec lignes 667, 675)."""

from __future__ import annotations

import redis.asyncio as redis

from app.config import get_settings

settings = get_settings()

_client: redis.Redis | None = None


def get_redis() -> redis.Redis:
    global _client
    if _client is None:
        _client = redis.from_url(settings.redis_url, decode_responses=True)
    return _client


async def cache_get(key: str) -> str | None:
    return await get_redis().get(key)


async def cache_set(key: str, value: str, ttl_seconds: int) -> None:
    await get_redis().set(key, value, ex=ttl_seconds)


async def cache_delete(key: str) -> None:
    await get_redis().delete(key)
