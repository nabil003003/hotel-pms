"""Token d'audit (D12 — même famille de pattern que les jetons d'élévation
de reservation-service, D8) + cache 5 min de la date métier."""

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


async def store_audit_token(token: str, establishment_id: str) -> None:
    client = get_redis()
    await client.set(f"audit_token:{token}", establishment_id, ex=settings.audit_token_ttl_seconds)


async def consume_audit_token(token: str) -> str | None:
    """Usage unique — supprime le jeton après lecture (même précaution que
    l'élévation de reservation-service, D8)."""
    client = get_redis()
    establishment_id = await client.get(f"audit_token:{token}")
    if establishment_id is not None:
        await client.delete(f"audit_token:{token}")
    return establishment_id


async def cache_business_date(establishment_id: str, business_date: str) -> None:
    client = get_redis()
    await client.set(f"business_date:{establishment_id}", business_date, ex=settings.business_date_cache_seconds)


async def get_cached_business_date(establishment_id: str) -> str | None:
    client = get_redis()
    return await client.get(f"business_date:{establishment_id}")
