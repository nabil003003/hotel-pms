from app.domain.services import handle_audit_closed
from app.infrastructure.database import AsyncSessionLocal


async def on_audit_event(routing_key: str, payload: dict) -> None:
    async with AsyncSessionLocal() as db:
        await handle_audit_closed(db, payload)
