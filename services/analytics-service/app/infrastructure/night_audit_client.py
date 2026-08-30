"""Client REST vers night-audit-service — `kpi/today` doit lire le snapshot
de la date métier réelle de l'établissement, pas `date.today()` (même
incident que front-office-service : une clôture avance `business_date`
au-delà du calendrier, et les écritures de `handle_booking_checked_in` /
`handle_folio_charge_added` / `handle_payment_added` sont déjà indexées sur
cette date métier réelle — lire avec `date.today()` désynchronisait
silencieusement la lecture de l'écriture)."""

from __future__ import annotations

import time
from datetime import date as date_type
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


async def get_business_date(establishment_id: str) -> date_type:
    token = await _get_service_token()
    async with httpx.AsyncClient(timeout=5.0) as client:
        resp = await client.get(
            f"{settings.night_audit_service_url}/api/v1/night-audit/business-date",
            params={"establishment_id": establishment_id},
            headers={"Authorization": f"Bearer {token}"},
        )
        resp.raise_for_status()
        return date_type.fromisoformat(resp.json()["business_date"])
