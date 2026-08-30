"""Événements publiés sur `amh.channel` (déjà déclaré, inutilisé jusqu'ici —
voir Appendix C du spec)."""

from __future__ import annotations

import uuid
from typing import Any

from app.infrastructure.rabbitmq import publish


async def publish_channel_booking_received(
    establishment_id: uuid.UUID, ota_name: str, ota_reference: str, correlation_id: str, extra: dict[str, Any]
) -> None:
    await publish(
        "channel.booking_received",
        {
            "establishment_id": str(establishment_id),
            "ota_name": ota_name,
            "ota_reference": ota_reference,
            "correlation_id": correlation_id,
            **extra,
        },
    )


async def publish_channel_sync_failed(
    establishment_id: uuid.UUID, ota_name: str, error: str, correlation_id: str | None = None
) -> None:
    await publish(
        "channel.sync_failed",
        {
            "establishment_id": str(establishment_id),
            "ota_name": ota_name,
            "error": error,
            "correlation_id": correlation_id,
        },
    )
