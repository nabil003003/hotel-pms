from __future__ import annotations

import json

import aio_pika

from app.config import get_settings

settings = get_settings()

_connection: aio_pika.abc.AbstractRobustConnection | None = None


async def _get_connection() -> aio_pika.abc.AbstractRobustConnection:
    global _connection
    if _connection is None or _connection.is_closed:
        _connection = await aio_pika.connect_robust(settings.rabbitmq_url)
    return _connection


async def _consume(exchange_name: str, queue_name: str, routing_key: str, handler) -> None:
    connection = await _get_connection()
    channel = await connection.channel()
    await channel.set_qos(prefetch_count=10)

    exchange = await channel.declare_exchange(exchange_name, aio_pika.ExchangeType.TOPIC, durable=True)
    queue = await channel.declare_queue(queue_name, durable=True, arguments={"x-dead-letter-exchange": "amh.dlx"})
    await queue.bind(exchange, routing_key=routing_key)

    async with queue.iterator() as queue_iter:
        async for message in queue_iter:
            async with message.process():
                payload = json.loads(message.body.decode("utf-8"))
                await handler(message.routing_key, payload)


async def consume_booking_events(handler) -> None:
    await _consume("amh.booking", "analytics.booking_events", "booking.#", handler)


async def consume_channel_events(handler) -> None:
    await _consume("amh.channel", "analytics.channel_events", "channel.#", handler)


async def consume_audit_events(handler) -> None:
    await _consume("amh.audit", "analytics.audit_events", "audit.#", handler)


async def consume_folio_events(handler) -> None:
    await _consume("amh.folio", "analytics.folio_events", "folio.#", handler)
