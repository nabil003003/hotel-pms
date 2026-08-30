import uuid

from app.domain.services import apply_end_of_day_turnover, handle_establishment_event
from app.infrastructure.database import AsyncSessionLocal


async def on_establishment_event(routing_key: str, payload: dict) -> None:
    async with AsyncSessionLocal() as db:
        await handle_establishment_event(db, routing_key, payload)


async def on_audit_event(routing_key: str, payload: dict) -> None:
    async with AsyncSessionLocal() as db:
        await apply_end_of_day_turnover(db, uuid.UUID(payload["establishment_id"]))
