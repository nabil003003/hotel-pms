"""Client REST vers establishment-service — utilisé pour résoudre un
`room_id` concret à partir d'une catégorie (chemin OTA, D6 : le webhook ne
connaît que `internal_room_category`, pas de chambre précise)."""

from __future__ import annotations

import time
from typing import Any

import httpx

from app.config import get_settings

settings = get_settings()

_token_cache: dict[str, Any] = {"access_token": None, "expires_at": 0.0}

# Perf (Sprint 8, D15) : un seul client HTTP partagé et réutilisé (pool de
# connexions keep-alive) au lieu d'`async with httpx.AsyncClient(...)` par
# appel — ouvrir une connexion TCP neuve à chaque `POST /bookings` était une
# part mesurable de la latence sous concurrence (load test Sprint 7).
# `httpx.AsyncClient` est explicitement conçu pour être partagé entre
# coroutines concurrentes.
_client: httpx.AsyncClient | None = None


def _get_client() -> httpx.AsyncClient:
    global _client
    if _client is None:
        _client = httpx.AsyncClient(timeout=5.0)
    return _client


async def _get_service_token() -> str:
    now = time.time()
    if _token_cache["access_token"] is not None and now < _token_cache["expires_at"] - 10:
        return _token_cache["access_token"]

    url = f"{settings.keycloak_url}/realms/{settings.keycloak_realm}/protocol/openid-connect/token"
    resp = await _get_client().post(
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


async def get_rooms_by_category(establishment_id: str, categorie: str) -> list[dict]:
    token = await _get_service_token()
    resp = await _get_client().get(
        f"{settings.establishment_service_url}/api/v1/establishments/{establishment_id}/rooms",
        params={"categorie": categorie},
        headers={"Authorization": f"Bearer {token}"},
    )
    resp.raise_for_status()
    return resp.json()
