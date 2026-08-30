"""Événements publiés sur `amh.booking` (déjà déclaré Sprint 1)."""

from __future__ import annotations

from typing import Any

from app.infrastructure.rabbitmq import publish


async def publish_booking_created(booking: dict[str, Any]) -> None:
    await publish("booking.created", booking)


async def publish_booking_cancelled(booking: dict[str, Any], reason: str | None) -> None:
    await publish(
        "booking.cancelled",
        {"booking_id": booking["id"], "reason": reason, "establishment_id": booking["establishment_id"]},
    )


async def publish_booking_room_changed(booking: dict[str, Any], old_room_id, new_room_id) -> None:
    await publish(
        "booking.room_changed",
        {
            "booking_id": booking["id"],
            "old_room": str(old_room_id),
            "new_room": str(new_room_id),
            "establishment_id": booking["establishment_id"],
        },
    )
