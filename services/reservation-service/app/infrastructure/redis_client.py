from __future__ import annotations

import json
from collections.abc import AsyncGenerator
from datetime import date as date_type
from typing import Any

import redis.asyncio as redis

from app.config import get_settings

settings = get_settings()

_client: redis.Redis | None = None


def get_redis() -> redis.Redis:
    global _client
    if _client is None:
        _client = redis.from_url(settings.redis_url, decode_responses=True)
    return _client


def booking_lock_key(establishment_id, room_id, night: date_type) -> str:
    return f"booking_lock:{establishment_id}:{room_id}:{night.isoformat()}"


def room_shift_lock_key(establishment_id, room_id, night: date_type) -> str:
    return f"room_shift_lock:{establishment_id}:{room_id}:{night.isoformat()}"


async def acquire_lock(key: str, ttl_seconds: int = 30) -> bool:
    client = get_redis()
    return bool(await client.set(key, "1", nx=True, ex=ttl_seconds))


async def release_lock(key: str) -> None:
    client = get_redis()
    await client.delete(key)


async def acquire_locks(keys: list[str], ttl_seconds: int = 30) -> list[str]:
    """Tout-ou-rien : si une clé est déjà verrouillée, relâche celles déjà
    acquises et retourne une liste vide (l'appelant doit alors traiter ça
    comme un échec de verrouillage)."""
    acquired: list[str] = []
    for key in keys:
        if await acquire_lock(key, ttl_seconds):
            acquired.append(key)
        else:
            for held in acquired:
                await release_lock(held)
            return []
    return acquired


async def release_locks(keys: list[str]) -> None:
    for key in keys:
        await release_lock(key)


async def get_idempotent_booking_id(idempotency_key: str) -> str | None:
    client = get_redis()
    return await client.get(f"idempotency:{idempotency_key}")


async def set_idempotent_booking_id(idempotency_key: str, booking_id: str, ttl_seconds: int = 86400) -> None:
    client = get_redis()
    await client.set(f"idempotency:{idempotency_key}", booking_id, ex=ttl_seconds)


def ws_channel(establishment_id: str) -> str:
    return f"ws:planning:{establishment_id}"


async def publish_ws_message(establishment_id: str, payload: dict[str, Any]) -> None:
    """Relai pub/sub Redis pour le WebSocket /ws/planning — même pattern que
    housekeeping-service (/ws/rooms) : découplé de RabbitMQ (bus
    d'intégration inter-services), ce canal ne sert qu'à pousser les mises à
    jour temps réel aux clients connectés à CE service."""
    client = get_redis()
    await client.publish(ws_channel(establishment_id), json.dumps(payload, default=str))


async def subscribe_ws_channel(establishment_id: str) -> AsyncGenerator[str, None]:
    client = get_redis()
    pubsub = client.pubsub()
    await pubsub.subscribe(ws_channel(establishment_id))
    try:
        async for message in pubsub.listen():
            if message["type"] == "message":
                yield message["data"]
    finally:
        await pubsub.unsubscribe(ws_channel(establishment_id))
        await pubsub.close()
