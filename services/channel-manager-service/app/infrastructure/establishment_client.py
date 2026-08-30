"""Client REST vers establishment-service — D3 (Sprint 2, option 1) :
`ota_mappings` reste dans `establishment_db`, channel-manager-service la lit
en REST plutôt que de la dupliquer dans `channel_db`.

Le compte de service `svc-channel-manager` doit être marqué
`is_super_admin=true` côté Keycloak (comme `svc-housekeeping`, D1) pour
pouvoir lire le mapping de n'importe quel établissement sans être scopé par
tenant — voir scripts/keycloak_setup.py."""

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


async def get_ota_mapping(
    establishment_id: str, *, ota_name: str, ota_room_type_id: str | None
) -> dict | None:
    token = await _get_service_token()
    params = {"ota_name": ota_name}
    if ota_room_type_id is not None:
        params["ota_room_type_id"] = ota_room_type_id

    async with httpx.AsyncClient(timeout=5.0) as client:
        resp = await client.get(
            f"{settings.establishment_service_url}/api/v1/establishments/{establishment_id}/ota-mappings",
            params=params,
            headers={"Authorization": f"Bearer {token}"},
        )
        resp.raise_for_status()
        mappings = resp.json()

    return mappings[0] if mappings else None
