from __future__ import annotations

import json
from typing import Any

import aio_pika

from app.config import get_settings

settings = get_settings()

BOOKING_EXCHANGE = "amh.booking"
ROOM_EXCHANGE = "amh.room"
ROOM_QUEUE = "reservation.room_events"
AUDIT_EXCHANGE = "amh.audit"
AUDIT_QUEUE = "reservation.audit_events"

_connection: aio_pika.abc.AbstractRobustConnection | None = None
_booking_exchange: aio_pika.abc.AbstractExchange | None = None


async def _get_connection() -> aio_pika.abc.AbstractRobustConnection:
    global _connection
    if _connection is None or _connection.is_closed:
        _connection = await aio_pika.connect_robust(settings.rabbitmq_url)
    return _connection


async def get_booking_exchange() -> aio_pika.abc.AbstractExchange:
    global _booking_exchange
    connection = await _get_connection()
    if _booking_exchange is None:
        channel = await connection.channel()
        _booking_exchange = await channel.declare_exchange(
            BOOKING_EXCHANGE, aio_pika.ExchangeType.TOPIC, durable=True
        )
    return _booking_exchange


async def publish(routing_key: str, payload: dict[str, Any]) -> None:
    exchange = await get_booking_exchange()
    message = aio_pika.Message(
        body=json.dumps(payload, default=str).encode("utf-8"),
        content_type="application/json",
        delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
    )
    await exchange.publish(message, routing_key=routing_key)


async def consume_room_events(handler) -> None:
    """`room.status_changed` (housekeeping-service) — reservation-service
    est listé comme consommateur dans l'Appendix C du spec sans qu'aucune
    logique métier ne soit décrite pour ça encore ; le handler journalise
    seulement (même précaution que channel-manager-service Sprint 2 : câbler
    la queue réellement plutôt que d'inventer un comportement métier)."""
    connection = await _get_connection()
    channel = await connection.channel()
    await channel.set_qos(prefetch_count=10)

    exchange = await channel.declare_exchange(ROOM_EXCHANGE, aio_pika.ExchangeType.TOPIC, durable=True)
    queue = await channel.declare_queue(ROOM_QUEUE, durable=True, arguments={"x-dead-letter-exchange": "amh.dlx"})
    await queue.bind(exchange, routing_key="room.status_changed")

    async with queue.iterator() as queue_iter:
        async for message in queue_iter:
            async with message.process():
                payload = json.loads(message.body.decode("utf-8"))
                await handler(message.routing_key, payload)


async def consume_audit_events(handler) -> None:
    """`audit.closed` (D12) — publié par night-audit-service (Sprint 5)."""
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
