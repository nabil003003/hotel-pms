from __future__ import annotations

from app.infrastructure.rabbitmq import publish


async def publish_audit_closed(establishment_id: str, business_date: str, report_hash: str) -> None:
    await publish(
        "audit.closed",
        {"establishment_id": establishment_id, "business_date": business_date, "report_hash": report_hash},
    )
