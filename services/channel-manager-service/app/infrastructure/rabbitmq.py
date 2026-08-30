from __future__ import annotations

import json
from typing import Any

import aio_pika

from app.config import get_settings

settings = get_settings()

CHANNEL_EXCHANGE = "amh.channel"
BOOKING_EXCHANGE = "amh.booking"
BOOKING_QUEUE = "channel.booking_events"

_connection: aio_pika.abc.AbstractRobustConnection | None = None
_channel_exchange: aio_pika.abc.AbstractExchange | None = None


async def _get_connection() -> aio_pika.abc.AbstractRobustConnection:
    global _connection
    if _connection is None or _connection.is_closed:
        _connection = await aio_pika.connect_robust(settings.rabbitmq_url)
    return _connection


async def get_channel_exchange() -> aio_pika.abc.AbstractExchange:
    global _channel_exchange
    connection = await _get_connection()
    if _channel_exchange is None:
        channel = await connection.channel()
        _channel_exchange = await channel.declare_exchange(
            CHANNEL_EXCHANGE, aio_pika.ExchangeType.TOPIC, durable=True
        )
    return _channel_exchange


async def publish(routing_key: str, payload: dict[str, Any]) -> None:
    exchange = await get_channel_exchange()
    message = aio_pika.Message(
        body=json.dumps(payload, default=str).encode("utf-8"),
        content_type="application/json",
        delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
    )
    await exchange.publish(message, routing_key=routing_key)


async def consume_booking_events(handler) -> None:
    """Boucle de consommation, lancée en tâche de fond au démarrage : les
    événements `booking.*` (reservation-service/front-office-service, hors
    scope Sprint 2) déclenchent une mise à jour d'inventaire OTA côté
    channel-manager-service (Workflow A/F). Comme reservation-service
    n'existe pas encore, le handler se contente de journaliser
    (`inventory_update_pending`) — voir décision D6.

    Déclare ET lie explicitement la queue à l'exchange (même raisonnement
    que housekeeping-service D1) : `infra/rabbitmq/definitions.json` déclare
    aussi ce binding, mais un service ne doit pas dépendre d'une
    pré-configuration externe pour ses propres besoins de routage."""
    connection = await _get_connection()
    channel = await connection.channel()
    await channel.set_qos(prefetch_count=10)

    exchange = await channel.declare_exchange(BOOKING_EXCHANGE, aio_pika.ExchangeType.TOPIC, durable=True)
    queue = await channel.declare_queue(
        BOOKING_QUEUE, durable=True, arguments={"x-dead-letter-exchange": "amh.dlx"}
    )
    await queue.bind(exchange, routing_key="booking.#")

    async with queue.iterator() as queue_iter:
        async for message in queue_iter:
            async with message.process():
                payload = json.loads(message.body.decode("utf-8"))
                await handler(message.routing_key, payload)
