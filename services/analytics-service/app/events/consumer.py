import asyncio
import logging

from app.events.handlers import on_audit_event, on_booking_event, on_channel_event, on_folio_event
from app.infrastructure.rabbitmq import consume_audit_events, consume_booking_events, consume_channel_events, consume_folio_events

logger = logging.getLogger(__name__)


async def _run_forever(consume_fn, handler, name: str) -> None:
    while True:
        try:
            await consume_fn(handler)
        except Exception:  # noqa: BLE001
            logger.exception("%s consumer crashed, retrying in 5s", name)
            await asyncio.sleep(5)


async def run_consumers_forever() -> None:
    await asyncio.gather(
        _run_forever(consume_booking_events, on_booking_event, "booking_events"),
        _run_forever(consume_folio_events, on_folio_event, "folio_events"),
        _run_forever(consume_channel_events, on_channel_event, "channel_events"),
        _run_forever(consume_audit_events, on_audit_event, "audit_events"),
    )
