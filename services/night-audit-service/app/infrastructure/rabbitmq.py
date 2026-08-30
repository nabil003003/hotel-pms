"""night-audit-service ne fait que publier `audit.closed` (Appendix C) —
aucun consumer (le seul événement en amont, la clôture elle-même, est
déclenchée par une requête REST admin, pas par un événement)."""

from __future__ import annotations

import json
from typing import Any

import aio_pika

from app.config import get_settings

settings = get_settings()

AUDIT_EXCHANGE = "amh.audit"

_connection: aio_pika.abc.AbstractRobustConnection | None = None
_exchange: aio_pika.abc.AbstractExchange | None = None


async def _get_connection() -> aio_pika.abc.AbstractRobustConnection:
    global _connection
    if _connection is None or _connection.is_closed:
        _connection = await aio_pika.connect_robust(settings.rabbitmq_url)
    return _connection


async def _get_exchange() -> aio_pika.abc.AbstractExchange:
    global _exchange
    connection = await _get_connection()
    if _exchange is None:
        channel = await connection.channel()
        _exchange = await channel.declare_exchange(AUDIT_EXCHANGE, aio_pika.ExchangeType.TOPIC, durable=True)
    return _exchange


async def publish(routing_key: str, payload: dict[str, Any]) -> None:
    exchange = await _get_exchange()
    message = aio_pika.Message(
        body=json.dumps(payload, default=str).encode("utf-8"),
        content_type="application/json",
        delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
    )
    await exchange.publish(message, routing_key=routing_key)
