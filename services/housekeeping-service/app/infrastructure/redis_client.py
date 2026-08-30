from __future__ import annotations

import json
from collections.abc import AsyncGenerator
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


def ws_channel(establishment_id: str) -> str:
    return f"ws:rooms:{establishment_id}"


async def publish_ws_message(establishment_id: str, payload: dict[str, Any]) -> None:
    """Relai pub/sub Redis pour le WebSocket /ws/rooms — §6.4, SLA <500ms.
    Découplé de RabbitMQ (qui reste le bus d'intégration inter-services) :
    ce canal ne sert qu'à pousser les mises à jour temps réel aux clients
    connectés à CE service."""
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
