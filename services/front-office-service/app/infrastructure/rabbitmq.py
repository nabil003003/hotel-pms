from __future__ import annotations

import json
from typing import Any

import aio_pika

from app.config import get_settings

settings = get_settings()

BOOKING_EXCHANGE = "amh.booking"
FOLIO_EXCHANGE = "amh.folio"
AUDIT_EXCHANGE = "amh.audit"
AUDIT_QUEUE = "fo.audit_events"

_connection: aio_pika.abc.AbstractRobustConnection | None = None
_exchanges: dict[str, aio_pika.abc.AbstractExchange] = {}


async def _get_connection() -> aio_pika.abc.AbstractRobustConnection:
    global _connection
    if _connection is None or _connection.is_closed:
        _connection = await aio_pika.connect_robust(settings.rabbitmq_url)
    return _connection


async def _get_exchange(name: str) -> aio_pika.abc.AbstractExchange:
    connection = await _get_connection()
    if name not in _exchanges:
        channel = await connection.channel()
        _exchanges[name] = await channel.declare_exchange(name, aio_pika.ExchangeType.TOPIC, durable=True)
    return _exchanges[name]


async def publish(exchange_name: str, routing_key: str, payload: dict[str, Any]) -> None:
    exchange = await _get_exchange(exchange_name)
    message = aio_pika.Message(
        body=json.dumps(payload, default=str).encode("utf-8"),
        content_type="application/json",
        delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
    )
    await exchange.publish(message, routing_key=routing_key)


async def consume_audit_events(handler) -> None:
    """`audit.closed` (D9) — publié par night-audit-service (Sprint 5, pas
    encore construit). Câblé pour de vrai dès maintenant."""
    connection = await _get_connection()
    channel = await connection.channel()
    await channel.set_qos(prefetch_count=10)

    exchange = await channel.declare_exchange(AUDIT_EXCHANGE, aio_pika.ExchangeType.TOPIC, durable=True)
    queue = await channel.declare_queue(AUDIT_QUEUE, durable=True, arguments={"x-dead-letter-exchange": "amh.dlx"})
    await queue.bind(exchange, routing_key="audit.#")

    async with queue.iterator() as queue_iter:
        async for message in queue_iter:
            async with message.process():
                payload = json.loads(message.body.decode("utf-8"))
                await handler(message.routing_key, payload)
