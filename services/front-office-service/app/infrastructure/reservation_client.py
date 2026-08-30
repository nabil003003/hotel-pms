"""Client REST vers reservation-service — Workflow D/G : lecture de la
réservation et transition de statut (`status_checked_in`/`status_checked_out`)."""

from __future__ import annotations

import time
from typing import Any

import httpx

from app.config import get_settings

settings = get_settings()

_token_cache: dict[str, Any] = {"access_token": None, "expires_at": 0.0}


class ReservationClientError(Exception):
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


async def get_booking(booking_id: str) -> dict:
    token = await _get_service_token()
    async with httpx.AsyncClient(timeout=5.0) as client:
        resp = await client.get(
            f"{settings.reservation_service_url}/api/v1/bookings/{booking_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
    if resp.status_code >= 400:
        raise ReservationClientError(resp.status_code, resp.text)
    return resp.json()


async def get_customer(establishment_id: str, customer_id: str) -> dict:
    token = await _get_service_token()
    async with httpx.AsyncClient(timeout=5.0) as client:
        resp = await client.get(
            f"{settings.reservation_service_url}/api/v1/customers/{establishment_id}/{customer_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
    if resp.status_code >= 400:
        raise ReservationClientError(resp.status_code, resp.text)
    return resp.json()


async def update_booking_status(booking_id: str, new_status: str, *, reason: str | None = None) -> dict:
    token = await _get_service_token()
    async with httpx.AsyncClient(timeout=5.0) as client:
        resp = await client.patch(
            f"{settings.reservation_service_url}/api/v1/bookings/{booking_id}/status",
            json={"new_status": new_status, "reason": reason},
            headers={"Authorization": f"Bearer {token}"},
        )
    if resp.status_code >= 400:
        raise ReservationClientError(resp.status_code, resp.text)
    return resp.json()
