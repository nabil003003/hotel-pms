"""Client REST vers reservation-service — lecture de réservations
(`channel_performance.revenue`) et de segments (labels pour les endpoints
`/segments/*`)."""

from __future__ import annotations

import time
from typing import Any

import httpx

from app.config import get_settings

settings = get_settings()

_token_cache: dict[str, Any] = {"access_token": None, "expires_at": 0.0}


async def _get_service_token() -> str:
    now = time.time()
    if _token_cache["access_token"] is not None and now < _token_cache["expires_at"] - 10:
        return _token_cache["access_token"]

    url = f"{settings.keycloak_url}/realms/{settings.keycloak_realm}/protocol/openid-connect/token"
    async with httpx.AsyncClient(timeout=5.0) as client:
        resp = await client.post(
            url,
            data={
                "grant_type": "client_credentials",
                "client_id": settings.keycloak_client_id,
                "client_secret": settings.keycloak_client_secret,
            },
        )
        resp.raise_for_status()
        body = resp.json()

    _token_cache["access_token"] = body["access_token"]
    _token_cache["expires_at"] = now + body.get("expires_in", 60)
    return _token_cache["access_token"]


async def get_booking(booking_id: str) -> dict | None:
    token = await _get_service_token()
    async with httpx.AsyncClient(timeout=5.0) as client:
        resp = await client.get(
            f"{settings.reservation_service_url}/api/v1/bookings/{booking_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
    if resp.status_code == 404:
        return None
    resp.raise_for_status()
    return resp.json()


async def get_arrivals_count(establishment_id: str, business_date: str) -> int:
    """Arrivées prévues à `business_date` (D12 — `occupancy_forecast_J+1`),
    exclut les statuts qui ne matérialiseront jamais un séjour."""
    token = await _get_service_token()
    async with httpx.AsyncClient(timeout=5.0) as client:
        resp = await client.get(
            f"{settings.reservation_service_url}/api/v1/bookings",
            params={"establishment_id": establishment_id, "check_in_date": business_date},
            headers={"Authorization": f"Bearer {token}"},
        )
        resp.raise_for_status()
        bookings = resp.json()
    return sum(1 for b in bookings if b["status"] not in ("status_cancelled", "status_no_show"))


async def get_occupied_room_count(establishment_id: str) -> int:
    """Chambres réellement occupées maintenant (distinct par room_id), pour
    `kpi/today.occupancy_rate` — remplace le comptage `nuitees` cumulatif
    (incrémenté au check-in, jamais décrémenté au check-out, cf. D10) qui ne
    reflète pas l'occupation réelle à l'instant T. Même endpoint que
    housekeeping-service utilise déjà pour la même raison (D12,
    `reservation_client.get_checked_in_room_ids`)."""
    token = await _get_service_token()
    async with httpx.AsyncClient(timeout=5.0) as client:
        resp = await client.get(
            f"{settings.reservation_service_url}/api/v1/bookings",
            params={"establishment_id": establishment_id, "status": "status_checked_in"},
            headers={"Authorization": f"Bearer {token}"},
        )
        resp.raise_for_status()
        bookings = resp.json()
    return len({b["room_id"] for b in bookings})


async def get_market_segments(establishment_id: str) -> list[dict]:
    token = await _get_service_token()
    async with httpx.AsyncClient(timeout=5.0) as client:
        resp = await client.get(
            f"{settings.reservation_service_url}/api/v1/market-segments/{establishment_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        resp.raise_for_status()
        return resp.json()
