"""Événements publiés — nouveaux vs Appendix C du spec (décision D1, plan
Sprint 1) : establishment-service n'a pas d'événement défini dans le catalogue
d'origine, mais housekeeping-service a besoin de se synchroniser sur les
chambres. On introduit ces 3 événements sur l'exchange `amh.establishment`."""

from __future__ import annotations

import uuid
from typing import Any

from app.infrastructure.rabbitmq import publish


async def publish_establishment_created(establishment_id: uuid.UUID, name: str) -> None:
    await publish("establishment.created", {"establishment_id": str(establishment_id), "name": name})


async def publish_rooms_imported(establishment_id: uuid.UUID, rooms: list[dict[str, Any]]) -> None:
    await publish(
        "establishment.rooms_imported",
        {"establishment_id": str(establishment_id), "rooms": rooms},
    )


async def publish_room_updated(establishment_id: uuid.UUID, room: dict[str, Any]) -> None:
    await publish(
        "establishment.room_updated",
        {"establishment_id": str(establishment_id), "room": room},
    )
