import asyncio
import logging

from app.events.handlers import on_audit_event
from app.infrastructure.rabbitmq import consume_audit_events

logger = logging.getLogger(__name__)


async def run_consumer_forever() -> None:
    while True:
        try:
            await consume_audit_events(on_audit_event)
        except Exception:  # noqa: BLE001
            logger.exception("audit_events consumer crashed, retrying in 5s")
            await asyncio.sleep(5)
