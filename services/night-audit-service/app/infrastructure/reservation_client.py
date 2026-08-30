"""Client REST vers reservation-service — rapport `arrivees_prevues_J+1`."""

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


async def get_arrivals(establishment_id: str, check_in_date: str) -> list[dict]:
    token = await _get_service_token()
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(
            f"{settings.reservation_service_url}/api/v1/bookings",
            params={"establishment_id": establishment_id, "check_in_date": check_in_date},
            headers={"Authorization": f"Bearer {token}"},
        )
        resp.raise_for_status()
        bookings = resp.json()
    return [b for b in bookings if b["status"] not in ("status_cancelled", "status_no_show")]
