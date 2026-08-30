"""Client REST vers reservation-service — D6 (Sprint 3) : le webhook OTA
appelle `POST /api/v1/bookings` en synchrone (au lieu de bufferiser) pour
obtenir un vrai `internal_booking_id`, conformément au contrat d'origine du
Workflow C (spec ligne 268-272)."""

from __future__ import annotations

import time
from typing import Any

import httpx

from app.config import get_settings

settings = get_settings()

_token_cache: dict[str, Any] = {"access_token": None, "expires_at": 0.0}


class ReservationBookingError(Exception):
    def __init__(self, status_code: int, detail: Any):
        super().__init__(str(detail))
        self.status_code = status_code
        self.detail = detail


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


async def create_booking_from_ota(establishment_id: str, booking_payload: dict) -> dict:
    token = await _get_service_token()
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.post(
            f"{settings.reservation_service_url}/api/v1/bookings",
            json={"establishment_id": establishment_id, **booking_payload},
            headers={"Authorization": f"Bearer {token}"},
        )
    if resp.status_code >= 400:
        try:
            detail = resp.json().get("detail", resp.text)
        except ValueError:
            detail = resp.text
        raise ReservationBookingError(resp.status_code, detail)
    return resp.json()
