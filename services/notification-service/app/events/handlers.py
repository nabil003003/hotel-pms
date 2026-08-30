from app.domain.services import (
    handle_booking_cancelled,
    handle_booking_checked_in,
    handle_booking_checked_out,
    handle_booking_created,
    handle_channel_sync_failed,
    handle_room_incident_reported,
)
from app.infrastructure.database import AsyncSessionLocal

_BOOKING_HANDLERS = {
    "booking.created": handle_booking_created,
    "booking.checked_in": handle_booking_checked_in,
    "booking.checked_out": handle_booking_checked_out,
    "booking.cancelled": handle_booking_cancelled,
}


async def on_booking_event(routing_key: str, payload: dict) -> None:
    handler = _BOOKING_HANDLERS.get(routing_key)
    if handler is None:
        return  # booking.room_changed n'est pas consommé par notification-service (Appendix C)
    async with AsyncSessionLocal() as db:
        await handler(db, payload)


async def on_room_incident_event(routing_key: str, payload: dict) -> None:
    async with AsyncSessionLocal() as db:
        await handle_room_incident_reported(db, payload)


async def on_channel_event(routing_key: str, payload: dict) -> None:
    if routing_key != "channel.sync_failed":
        return  # channel.booking_received n'est pas consommé par notification-service (Appendix C)
    async with AsyncSessionLocal() as db:
        await handle_channel_sync_failed(db, payload)
