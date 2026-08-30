"""Client REST vers pricing-service — Workflow E (vérification du prix
catalogue plutôt que de faire confiance au client) et taxes TS/TPT
(fixe-par-pax) posées automatiquement au check-in."""

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


async def get_extras_catalog_item(establishment_id: str, catalog_item_id: str) -> dict | None:
    """pricing-service n'expose qu'une liste (pas de GET par id unitaire) —
    on filtre côté client. `None` si l'item n'existe pas/plus (catalogue mal
    référencé, appelant doit gérer)."""
    token = await _get_service_token()
    async with httpx.AsyncClient(timeout=5.0) as client:
        resp = await client.get(
            f"{settings.pricing_service_url}/api/v1/pricing/{establishment_id}/extras",
            headers={"Authorization": f"Bearer {token}"},
        )
        resp.raise_for_status()
        items = resp.json()
    return next((item for item in items if item["id"] == catalog_item_id), None)


async def get_ts_tpt_taxes(establishment_id: str) -> list[dict]:
    token = await _get_service_token()
    async with httpx.AsyncClient(timeout=5.0) as client:
        resp = await client.get(
            f"{settings.pricing_service_url}/api/v1/pricing/{establishment_id}/taxes",
            headers={"Authorization": f"Bearer {token}"},
        )
        resp.raise_for_status()
        taxes = resp.json()
    return [t for t in taxes if t["type"] in ("TS", "TPT")]
