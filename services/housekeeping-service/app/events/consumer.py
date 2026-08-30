import asyncio
import logging

from app.events.handlers import on_audit_event, on_establishment_event
from app.infrastructure.rabbitmq import consume_audit_events, consume_establishment_events

logger = logging.getLogger(__name__)


async def _run_forever(consume_fn, handler, name: str) -> None:
    while True:
        try:
            await consume_fn(handler)
        except Exception:  # noqa: BLE001 — on ne doit jamais laisser mourir ce worker
            logger.exception("%s consumer crashed, retrying in 5s", name)
            await asyncio.sleep(5)


async def run_consumer_forever() -> None:
    """Lancé en tâche de fond au démarrage de l'app (voir main.py lifespan).
    Se reconnecte automatiquement si la connexion RabbitMQ tombe (D1).
    `audit.closed` (D12) ajouté Sprint 5, en parallèle de establishment_events."""
    await asyncio.gather(
        _run_forever(consume_establishment_events, on_establishment_event, "establishment_events"),
        _run_forever(consume_audit_events, on_audit_event, "audit_events"),
    )
