import logging

from app.domain.services import handle_audit_closed
from app.infrastructure.database import AsyncSessionLocal

logger = logging.getLogger(__name__)


async def on_room_event(routing_key: str, payload: dict) -> None:
    """Journalisation seulement — voir infrastructure/rabbitmq.py pour le
    raisonnement (aucune logique métier décrite par le spec pour ce
    consumer)."""
    logger.info("room event received: %s %s", routing_key, payload)


async def on_audit_event(routing_key: str, payload: dict) -> None:
    async with AsyncSessionLocal() as db:
        await handle_audit_closed(db, payload)
