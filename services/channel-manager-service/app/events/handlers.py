from app.domain.services import handle_booking_event
from app.infrastructure.database import AsyncSessionLocal


async def on_booking_event(routing_key: str, payload: dict) -> None:
    async with AsyncSessionLocal() as db:
        await handle_booking_event(db, routing_key, payload)
