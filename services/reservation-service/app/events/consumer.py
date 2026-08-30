import asyncio
import logging

from app.events.handlers import on_audit_event, on_room_event
from app.infrastructure.rabbitmq import consume_audit_events, consume_room_events

logger = logging.getLogger(__name__)


async def _run_forever(consume_fn, handler, name: str) -> None:
    while True:
        try:
            await consume_fn(handler)
        except Exception:  # noqa: BLE001
            logger.exception("%s consumer crashed, retrying in 5s", name)
            await asyncio.sleep(5)


async def run_consumer_forever() -> None:
    """Lancé en tâche de fond au démarrage (voir main.py lifespan) — même
    stratégie de reconnexion que housekeeping-service/channel-manager-service.
    `audit.closed` (D12) ajouté Sprint 5, en parallèle du consumer room_events
    existant depuis Sprint 3."""
    await asyncio.gather(
        _run_forever(consume_room_events, on_room_event, "room_events"),
        _run_forever(consume_audit_events, on_audit_event, "audit_events"),
    )
