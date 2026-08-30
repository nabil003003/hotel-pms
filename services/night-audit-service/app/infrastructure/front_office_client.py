"""Client REST vers front-office-service — sources des rapports
`ca_detaille_J`, `encaissements_J`, `debiteurs_J`, `departs_attendus_J+1`,
et de la vérification pré-audit (débits/crédits/écarts)."""

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


async def _get(path: str, params: dict) -> Any:
    token = await _get_service_token()
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(
            f"{settings.front_office_service_url}{path}", params=params,
            headers={"Authorization": f"Bearer {token}"},
        )
        resp.raise_for_status()
        return resp.json()


async def get_daily_debits(establishment_id: str, date: str) -> dict:
    return await _get("/api/v1/folios/reports/daily-debits", {"establishment_id": establishment_id, "date": date})


async def get_daily_credits(establishment_id: str, date: str) -> dict:
    return await _get("/api/v1/folios/reports/daily-credits", {"establishment_id": establishment_id, "date": date})


async def get_discrepancy_report(establishment_id: str, date: str) -> list[dict]:
    return await _get(
        "/api/v1/folios/reports/discrepancy", {"establishment_id": establishment_id, "date": date}
    )


async def get_daily_ca_detail(establishment_id: str, date: str) -> dict:
    return await _get(
        "/api/v1/folios/reports/daily-ca-detail", {"establishment_id": establishment_id, "date": date}
    )


async def get_daily_encashments(establishment_id: str, date: str) -> dict:
    return await _get(
        "/api/v1/folios/reports/daily-encashments", {"establishment_id": establishment_id, "date": date}
    )


async def get_debtors(establishment_id: str) -> list[dict]:
    return await _get("/api/v1/folios/reports/debtors", {"establishment_id": establishment_id})


async def get_departures(establishment_id: str, date: str) -> dict:
    return await _get("/api/v1/folios/reports/departures", {"establishment_id": establishment_id, "date": date})
