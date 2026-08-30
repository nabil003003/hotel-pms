from __future__ import annotations

import json
from typing import Any

import aio_pika

from app.config import get_settings

settings = get_settings()

ROOM_EXCHANGE = "amh.room"
ESTABLISHMENT_EXCHANGE = "amh.establishment"
ESTABLISHMENT_QUEUE = "housekeeping.establishment_events"
AUDIT_EXCHANGE = "amh.audit"
AUDIT_QUEUE = "housekeeping.audit_events"

_connection: aio_pika.abc.AbstractRobustConnection | None = None
_room_exchange: aio_pika.abc.AbstractExchange | None = None


async def _get_connection() -> aio_pika.abc.AbstractRobustConnection:
    global _connection
    if _connection is None or _connection.is_closed:
        _connection = await aio_pika.connect_robust(settings.rabbitmq_url)
    return _connection


async def get_room_exchange() -> aio_pika.abc.AbstractExchange:
    global _room_exchange
    connection = await _get_connection()
    if _room_exchange is None:
        channel = await connection.channel()
        _room_exchange = await channel.declare_exchange(ROOM_EXCHANGE, aio_pika.ExchangeType.TOPIC, durable=True)
    return _room_exchange


async def publish_room_event(routing_key: str, payload: dict[str, Any]) -> None:
    exchange = await get_room_exchange()
    message = aio_pika.Message(
        body=json.dumps(payload, default=str).encode("utf-8"),
        content_type="application/json",
        delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
    )
    await exchange.publish(message, routing_key=routing_key)


async def consume_establishment_events(handler) -> None:
    """Boucle de consommation, lancée en tâche de fond au démarrage (D1) : les
    événements `establishment.*` (émis par establishment-service, non prévus
    dans l'Appendix C d'origine) maintiennent la copie locale de `rooms`.

    Déclare ET lie explicitement la queue à l'exchange (`queue.bind`) —
    `infra/rabbitmq/definitions.json` déclare aussi ce binding (chargé via
    `rabbitmq.conf` / `load_definitions`), mais un service ne doit pas
    dépendre d'une pré-configuration externe pour ses propres besoins de
    routage — le bind explicite ici est la source de vérité robuste.

    La queue DOIT être déclarée avec le même argument `x-dead-letter-exchange`
    que celui posé par definitions.json (`amh.dlx`) : RabbitMQ rejette une
    re-déclaration aux arguments différents (`PRECONDITION_FAILED -
    inequivalent arg`), ce qui faisait crasher ce consumer en boucle avant
    correction (vérification Sprint 1)."""
    connection = await _get_connection()
    channel = await connection.channel()
    await channel.set_qos(prefetch_count=10)

    exchange = await channel.declare_exchange(
        ESTABLISHMENT_EXCHANGE, aio_pika.ExchangeType.TOPIC, durable=True
    )
    queue = await channel.declare_queue(
        ESTABLISHMENT_QUEUE, durable=True, arguments={"x-dead-letter-exchange": "amh.dlx"}
    )
    await queue.bind(exchange, routing_key="establishment.#")

    async with queue.iterator() as queue_iter:
        async for message in queue_iter:
            async with message.process():
                payload = json.loads(message.body.decode("utf-8"))
                await handler(message.routing_key, payload)


async def consume_audit_events(handler) -> None:
    """`audit.closed` (D12, Sprint 5) — déclenche la bascule fin de journée."""
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
