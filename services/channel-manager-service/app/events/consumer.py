import asyncio
import logging

from app.events.handlers import on_booking_event
from app.infrastructure.rabbitmq import consume_booking_events

logger = logging.getLogger(__name__)


async def run_consumer_forever() -> None:
    """Lancé en tâche de fond au démarrage de l'app (voir main.py lifespan).
    Se reconnecte automatiquement si la connexion RabbitMQ tombe (même
    stratégie que housekeeping-service, D1)."""
    while True:
        try:
            await consume_booking_events(on_booking_event)
        except Exception:  # noqa: BLE001 — on ne doit jamais laisser mourir ce worker
            logger.exception("booking_events consumer crashed, retrying in 5s")
            await asyncio.sleep(5)
