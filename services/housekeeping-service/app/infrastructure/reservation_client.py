"""Client REST vers reservation-service — bascule fin de journée (D12,
Sprint 5) : housekeeping-service ne connaît pas l'occupation des chambres
(son `Room.statut` ne couvre que le cycle ménage — Sale/Nettoyage/Propre/
Contrôlée/Bloquée, jamais "Occupée"), donc il interroge reservation-service
pour savoir quelles chambres ont un séjour en cours."""

from __future__ import annotations

import httpx

from app.config import get_settings
from app.infrastructure.keycloak import get_service_token

settings = get_settings()


async def get_checked_in_room_ids(establishment_id: str) -> list[str]:
    token = await get_service_token()
    async with httpx.AsyncClient(timeout=5.0) as client:
        resp = await client.get(
            f"{settings.reservation_service_url}/api/v1/bookings",
            params={"establishment_id": establishment_id, "status": "status_checked_in"},
            headers={"Authorization": f"Bearer {token}"},
        )
        resp.raise_for_status()
        bookings = resp.json()
    return [b["room_id"] for b in bookings]
