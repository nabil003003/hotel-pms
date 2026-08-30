"""Idempotence (`X-Idempotency-Key`, mandatory sur check-in/check-out/charges
per spec) — même pattern que reservation-service (pas de colonne dédiée dans
le schéma transcrit, Redis avec TTL)."""

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


async def get_idempotent_result(idempotency_key: str) -> str | None:
    client = get_redis()
    return await client.get(f"idempotency:{idempotency_key}")


async def set_idempotent_result(idempotency_key: str, value: str, ttl_seconds: int = 86400) -> None:
    client = get_redis()
    await client.set(f"idempotency:{idempotency_key}", value, ex=ttl_seconds)
