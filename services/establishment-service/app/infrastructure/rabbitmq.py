from __future__ import annotations

import json
from typing import Any

import aio_pika

from app.config import get_settings

settings = get_settings()

_connection: aio_pika.abc.AbstractRobustConnection | None = None
_exchange: aio_pika.abc.AbstractExchange | None = None

EXCHANGE_NAME = "amh.establishment"


async def get_exchange() -> aio_pika.abc.AbstractExchange:
    global _connection, _exchange
    if _connection is None or _connection.is_closed:
        _connection = await aio_pika.connect_robust(settings.rabbitmq_url)
    if _exchange is None:
        channel = await _connection.channel()
        _exchange = await channel.declare_exchange(EXCHANGE_NAME, aio_pika.ExchangeType.TOPIC, durable=True)
    return _exchange


async def publish(routing_key: str, payload: dict[str, Any]) -> None:
    exchange = await get_exchange()
    message = aio_pika.Message(
        body=json.dumps(payload, default=str).encode("utf-8"),
        content_type="application/json",
        delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
    )
    await exchange.publish(message, routing_key=routing_key)
