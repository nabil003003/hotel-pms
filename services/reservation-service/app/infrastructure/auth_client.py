"""Client REST vers auth-gateway-service — consommation d'un token
d'élévation (D8, Workflow F upsell)."""

from __future__ import annotations

import time
from typing import Any

import httpx

from app.config import get_settings

settings = get_settings()

_token_cache: dict[str, Any] = {"access_token": None, "expires_at": 0.0}


class ElevationConsumptionError(Exception):
    pass


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


async def consume_elevation(elevation_token: str) -> dict:
    token = await _get_service_token()
    async with httpx.AsyncClient(timeout=5.0) as client:
        resp = await client.post(
            f"{settings.auth_gateway_service_url}/api/v1/auth/elevate/consume",
            json={"token": elevation_token},
            headers={"Authorization": f"Bearer {token}"},
        )
    if resp.status_code == 401:
        raise ElevationConsumptionError(resp.json().get("detail", "Elevation token invalid"))
    resp.raise_for_status()
    return resp.json()
